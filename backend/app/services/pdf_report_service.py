from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import models
from app.config import settings


REPORT_DIR = settings.report_dir


def generate_approval_pdf(
    db: Session,
    approval_case_id: int,
    report_type: str = "DETAIL",
    created_by: str | None = None,
) -> models.ApprovalReportFile:
    normalized_type = report_type.upper()
    if normalized_type not in {"SUMMARY", "DETAIL"}:
        raise HTTPException(status_code=400, detail="report_type must be SUMMARY or DETAIL")

    approval_case = db.execute(
        select(models.ApprovalCase)
        .options(
            selectinload(models.ApprovalCase.findings),
            selectinload(models.ApprovalCase.workflow),
            selectinload(models.ApprovalCase.productivity_points),
        )
        .where(models.ApprovalCase.id == approval_case_id)
    ).scalar_one_or_none()
    if approval_case is None:
        raise HTTPException(status_code=404, detail="Approval case not found")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    file_name = (
        f"approval_{approval_case_id}_{normalized_type.lower()}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}.pdf"
    )
    file_path = REPORT_DIR / file_name

    styles = _build_styles()
    story = (
        _summary_story(approval_case, styles)
        if normalized_type == "SUMMARY"
        else _detail_story(approval_case, styles)
    )

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=f"LOTOS AI Approval {normalized_type}",
    )
    doc.build(story)

    report_file = models.ApprovalReportFile(
        approval_case_id=approval_case.id,
        report_type=normalized_type,
        file_name=file_name,
        file_path=str(file_path),
        created_by=created_by,
    )
    db.add(report_file)
    db.commit()
    db.refresh(report_file)
    return report_file


def _build_styles() -> dict[str, ParagraphStyle]:
    font_name = _register_korean_font()
    sample = getSampleStyleSheet()
    base = ParagraphStyle(
        "LotosBase",
        parent=sample["BodyText"],
        fontName=font_name,
        fontSize=9,
        leading=12,
    )
    return {
        "title": ParagraphStyle(
            "LotosTitle",
            parent=base,
            fontSize=18,
            leading=22,
            spaceAfter=10,
            textColor=colors.HexColor("#1f4f82"),
        ),
        "heading": ParagraphStyle(
            "LotosHeading",
            parent=base,
            fontSize=12,
            leading=15,
            spaceBefore=8,
            spaceAfter=5,
            textColor=colors.HexColor("#1f2937"),
        ),
        "body": base,
        "small": ParagraphStyle(
            "LotosSmall",
            parent=base,
            fontSize=8,
            leading=10,
        ),
    }


def _register_korean_font() -> str:
    candidates = [
        ("MalgunGothic", Path("C:/Windows/Fonts/malgun.ttf")),
        ("MalgunGothicBold", Path("C:/Windows/Fonts/malgunbd.ttf")),
        ("NanumGothic", Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf")),
        ("NotoSansCJK", Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")),
        ("AppleGothic", Path("/System/Library/Fonts/AppleGothic.ttf")),
    ]
    for font_name, path in candidates:
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(path)))
                return font_name
            except Exception:
                continue
    return "Helvetica"


def _summary_story(
    approval_case: models.ApprovalCase,
    styles: dict[str, ParagraphStyle],
) -> list:
    story: list = [Paragraph("LOTOS AI 결재심사 요약", styles["title"])]
    story.append(_key_value_table(_summary_rows(approval_case), styles))
    story.append(Spacer(1, 6))
    story.append(Paragraph("핵심 Findings", styles["heading"]))
    story.append(_findings_table(approval_case.findings[:5], styles))
    story.append(Paragraph("대표이사 결재의견", styles["heading"]))
    story.append(Paragraph(_text(approval_case.executive_comment), styles["body"]))
    return story


def _detail_story(
    approval_case: models.ApprovalCase,
    styles: dict[str, ParagraphStyle],
) -> list:
    findings_by_category = _findings_by_category(approval_case.findings)
    story: list = [Paragraph("LOTOS AI 상세 결재심사서", styles["title"])]
    story.append(Paragraph("기본정보", styles["heading"]))
    story.append(_key_value_table(_basic_rows(approval_case), styles))
    story.append(Paragraph("Revenue / Expense 요약", styles["heading"]))
    story.append(_key_value_table(_profit_rows(approval_case), styles))

    for title, category in [
        ("Minimum GP 심사", "Minimum GP"),
        ("운송마진 심사", "운송마진"),
        ("통관수익 심사", "통관수익"),
        ("Partner Fee 심사", "Partner Fee"),
        ("필수 청구항목 누락 검사", "비용누락"),
        ("자사자원 활용 검사", "자사자원"),
    ]:
        story.append(Paragraph(title, styles["heading"]))
        story.append(_findings_table(findings_by_category.get(category, []), styles))

    story.append(Paragraph("생산성 Point", styles["heading"]))
    story.append(
        _key_value_table(
            [
                ("담당자", approval_case.pic or "-"),
                ("업무코드", approval_case.code),
                ("Point", f"{approval_case.point:g}"),
            ],
            styles,
        )
    )

    story.append(Paragraph("Workflow 이력", styles["heading"]))
    story.append(_workflow_table(approval_case.workflow, styles))
    story.append(Paragraph("대표이사 결재의견", styles["heading"]))
    story.append(Paragraph(_text(approval_case.executive_comment), styles["body"]))
    story.append(Paragraph("최종 결재결과", styles["heading"]))
    story.append(Paragraph(_text(approval_case.decision), styles["body"]))
    return story


def _summary_rows(approval_case: models.ApprovalCase) -> list[tuple[str, str]]:
    workflow_status = approval_case.workflow.current_status if approval_case.workflow else "-"
    return [
        ("고객명", approval_case.customer_name),
        ("거래구분", approval_case.trade_type),
        ("Partner", approval_case.partner_name or "-"),
        ("담당자", approval_case.pic or "-"),
        ("업무코드", approval_case.code),
        ("Point", f"{approval_case.point:g}"),
        ("매출", _jpy(approval_case.total_revenue_jpy)),
        ("원가", _jpy(approval_case.total_expense_jpy)),
        ("GP", _jpy(approval_case.gp_jpy)),
        ("GP율", _rate(approval_case.gp_rate)),
        ("실GP율", _rate(approval_case.net_gp_rate_ex_tax)),
        ("Minimum GP", _jpy(approval_case.minimum_gp_jpy)),
        ("AI Decision", approval_case.decision),
        ("Workflow Status", workflow_status),
    ]


def _basic_rows(approval_case: models.ApprovalCase) -> list[tuple[str, str]]:
    return [
        ("고객명", approval_case.customer_name),
        ("거래구분", approval_case.trade_type),
        ("Partner", approval_case.partner_name or "-"),
        ("Shipper", approval_case.shipper_name or "-"),
        ("담당자", approval_case.pic or "-"),
        ("업무코드", approval_case.code),
        ("Mode", approval_case.mode),
        ("Direction", approval_case.direction),
        ("POL", approval_case.pol or "-"),
        ("POD", approval_case.pod or "-"),
        ("PORT", approval_case.port or "-"),
        ("Container", f"{approval_case.container_type or '-'} x {approval_case.container_count}"),
    ]


def _profit_rows(approval_case: models.ApprovalCase) -> list[tuple[str, str]]:
    return [
        ("매출", _jpy(approval_case.total_revenue_jpy)),
        ("원가", _jpy(approval_case.total_expense_jpy)),
        ("GP", _jpy(approval_case.gp_jpy)),
        ("GP율", _rate(approval_case.gp_rate)),
        ("관세/소비세 제외 실매출", _jpy(approval_case.net_revenue_ex_tax_jpy)),
        ("관세/소비세 제외 실원가", _jpy(approval_case.net_expense_ex_tax_jpy)),
        ("관세/소비세 제외 GP율", _rate(approval_case.net_gp_rate_ex_tax)),
        ("Minimum GP", _jpy(approval_case.minimum_gp_jpy)),
    ]


def _key_value_table(
    rows: list[tuple[str, str]],
    styles: dict[str, ParagraphStyle],
) -> Table:
    table_data = [
        [Paragraph(_text(key), styles["small"]), Paragraph(_text(value), styles["small"])]
        for key, value in rows
    ]
    table = Table(table_data, colWidths=[42 * mm, 126 * mm])
    table.setStyle(_table_style())
    return table


def _findings_table(
    findings: list[models.ApprovalFinding],
    styles: dict[str, ParagraphStyle],
) -> Table | Paragraph:
    if not findings:
        return Paragraph("해당 사항 없음", styles["body"])
    table_data = [[
        Paragraph("구분", styles["small"]),
        Paragraph("상태", styles["small"]),
        Paragraph("내용", styles["small"]),
        Paragraph("금액", styles["small"]),
    ]]
    for finding in findings:
        table_data.append([
            Paragraph(_text(finding.category), styles["small"]),
            Paragraph(_text(finding.status), styles["small"]),
            Paragraph(_text(finding.message), styles["small"]),
            Paragraph(_jpy(finding.amount_jpy), styles["small"]),
        ])
    table = Table(table_data, colWidths=[28 * mm, 18 * mm, 100 * mm, 22 * mm])
    table.setStyle(_table_style(header=True))
    return table


def _workflow_table(
    workflow: models.ApprovalWorkflow | None,
    styles: dict[str, ParagraphStyle],
) -> Table | Paragraph:
    if workflow is None:
        return Paragraph("Workflow 정보 없음", styles["body"])
    rows = [
        ("현재상태", workflow.current_status),
        ("상신자", workflow.requested_by or "-"),
        ("팀장 승인", workflow.team_approved_by or "-"),
        ("본부장 승인", workflow.director_approved_by or "-"),
        ("대표 승인", workflow.ceo_approved_by or "-"),
        ("반려자", workflow.rejected_by or "-"),
        ("보완요청자", workflow.returned_by or "-"),
    ]
    return _key_value_table(rows, styles)


def _findings_by_category(
    findings: list[models.ApprovalFinding],
) -> dict[str, list[models.ApprovalFinding]]:
    grouped: dict[str, list[models.ApprovalFinding]] = {}
    for finding in findings:
        grouped.setdefault(finding.category, []).append(finding)
    return grouped


def _table_style(header: bool = False) -> TableStyle:
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef6")))
    return TableStyle(commands)


def _text(value: object) -> str:
    return str(value).replace("\n", "<br/>")


def _jpy(amount: float | None) -> str:
    if amount is None:
        return "-"
    return f"JPY {amount:,.0f}"


def _rate(rate: float | None) -> str:
    if rate is None:
        return "-"
    return f"{rate:.1%}"
