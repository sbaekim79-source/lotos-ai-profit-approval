from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import logging
from time import perf_counter

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import models
from app.config import settings
from app.database import Base, SessionLocal, engine, ensure_sqlite_schema, get_db
from app.logging_config import setup_logging
from app.routers.admin import router as admin_router
from app.routers.audit_logs import router as audit_logs_router
from app.routers.auth import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.documentation import router as documentation_router
from app.routers.exports import router as exports_router
from app.routers.integrations import router as integrations_router
from app.routers.masters import router as masters_router
from app.routers.operation_tests import router as operation_tests_router
from app.routers.parser_improvements import router as parser_improvements_router
from app.routers.parser_validation import router as parser_validation_router
from app.routers.quotes import router as quotes_router
from app.routers.reports import router as reports_router
from app.routers.tariffs import router as tariffs_router
from app.routers.uploads import router as uploads_router
from app.routers.users import router as users_router
from app.routers.workflows import router as workflows_router
from app.sample_cases import SAMPLE_CASES
from app.schemas import (
    ApprovalCaseInput,
    ApprovalDetail,
    ApprovalListItem,
    ApprovalResult,
    ApprovalSaveResponse,
    Finding,
    HealthResponse,
)
from app.services.approval_engine import analyze_case, analyze_case_with_rules
from app.services.approval_repository import save_approval_case
from app.services.auth import ensure_role, get_current_user
from app.services.audit_service import create_audit_log


setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if not settings.is_production:
        Base.metadata.create_all(bind=engine)
        ensure_sqlite_schema()
    yield


app = FastAPI(
    title="LOTOS AI Profit Approval System",
    description="MVP API for AI-based Profit Sheet profitability approval.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_ = models

app.include_router(admin_router)
app.include_router(audit_logs_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(documentation_router)
app.include_router(exports_router)
app.include_router(integrations_router)
app.include_router(masters_router)
app.include_router(operation_tests_router)
app.include_router(parser_improvements_router)
app.include_router(parser_validation_router)
app.include_router(quotes_router)
app.include_router(reports_router)
app.include_router(tariffs_router)
app.include_router(uploads_router)
app.include_router(users_router)
app.include_router(workflows_router)


@app.middleware("http")
async def request_log_middleware(request: Request, call_next):
    start = perf_counter()
    status_code = 500
    try:
        if (
            settings.is_production
            and request.method in {"POST", "PUT", "DELETE"}
            and request.url.path.startswith("/api/masters")
        ):
            with SessionLocal() as auth_db:
                try:
                    ensure_role(get_current_user(request, auth_db), {"ADMIN"})
                except HTTPException as exc:
                    status_code = exc.status_code
                    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        response = await call_next(request)
        status_code = response.status_code
        if (
            status_code < 400
            and request.method in {"POST", "PUT", "DELETE"}
            and request.url.path.startswith("/api/masters")
        ):
            with SessionLocal() as audit_db:
                create_audit_log(
                    audit_db,
                    user_name=request.headers.get("X-USER-NAME"),
                    action=f"MASTER_{request.method}",
                    entity_type="MASTER_RULE",
                    detail=request.url.path,
                    ip_address=request.client.host if request.client else None,
                )
        return response
    finally:
        duration_ms = (perf_counter() - start) * 1000
        logger.info(
            "method=%s path=%s status_code=%s duration_ms=%.2f user_name=%s",
            request.method,
            request.url.path,
            status_code,
            duration_ms,
            request.headers.get("X-USER-NAME", "-"),
        )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/api/db/status", tags=["Database"])
def database_status() -> dict[str, str]:
    return {"database": "ok"}


@app.post(
    "/api/approvals/analyze",
    response_model=ApprovalResult,
    tags=["Approvals"],
)
def analyze_approval(case: ApprovalCaseInput) -> ApprovalResult:
    return analyze_case(case)


def _to_approval_list_item(approval_case: models.ApprovalCase) -> ApprovalListItem:
    return ApprovalListItem(
        id=approval_case.id,
        customer_name=approval_case.customer_name,
        trade_type=approval_case.trade_type,
        partner_name=approval_case.partner_name,
        pic=approval_case.pic,
        code=approval_case.code,
        point=approval_case.point,
        total_revenue_jpy=approval_case.total_revenue_jpy,
        total_expense_jpy=approval_case.total_expense_jpy,
        gp_jpy=approval_case.gp_jpy,
        gp_rate=approval_case.gp_rate,
        decision=approval_case.decision,
        created_at=approval_case.created_at,
    )


def _to_approval_detail(approval_case: models.ApprovalCase) -> ApprovalDetail:
    return ApprovalDetail(
        id=approval_case.id,
        case_no=approval_case.case_no,
        customer_name=approval_case.customer_name,
        trade_type=approval_case.trade_type,
        partner_name=approval_case.partner_name,
        shipper_name=approval_case.shipper_name,
        pic=approval_case.pic,
        mode=approval_case.mode,
        direction=approval_case.direction,
        code=approval_case.code,
        point=approval_case.point,
        pol=approval_case.pol,
        pod=approval_case.pod,
        port=approval_case.port,
        cargo_description=approval_case.cargo_description,
        container_type=approval_case.container_type,
        container_count=approval_case.container_count,
        total_revenue_jpy=approval_case.total_revenue_jpy,
        total_expense_jpy=approval_case.total_expense_jpy,
        gp_jpy=approval_case.gp_jpy,
        gp_rate=approval_case.gp_rate,
        net_revenue_ex_tax_jpy=approval_case.net_revenue_ex_tax_jpy,
        net_expense_ex_tax_jpy=approval_case.net_expense_ex_tax_jpy,
        net_gp_rate_ex_tax=approval_case.net_gp_rate_ex_tax,
        minimum_gp_jpy=approval_case.minimum_gp_jpy,
        decision=approval_case.decision,
        executive_comment=approval_case.executive_comment,
        created_at=approval_case.created_at,
        findings=[
            Finding(
                category=finding.category,
                status=finding.status,
                message=finding.message,
                amount_jpy=finding.amount_jpy,
            )
            for finding in approval_case.findings
        ],
    )


def _format_jpy(amount: float | None) -> str:
    if amount is None:
        return "-"
    return f"{amount:,.0f}엔"


def _format_rate(rate: float | None) -> str:
    if rate is None:
        return "-"
    return f"{rate:.1%}"


def _escape_markdown_table(value: str | None) -> str:
    if value is None:
        return "-"
    return value.replace("|", "\\|").replace("\n", " ")


def _findings_table(findings: list[models.ApprovalFinding]) -> str:
    if not findings:
        return "특이사항 없음\n"

    lines = [
        "| 구분 | 상태 | 내용 | 금액 |",
        "|---|---|---|---|",
    ]
    for finding in findings:
        lines.append(
            "| "
            f"{_escape_markdown_table(finding.category)} | "
            f"{_escape_markdown_table(finding.status)} | "
            f"{_escape_markdown_table(finding.message)} | "
            f"{_format_jpy(finding.amount_jpy)} |"
        )
    return "\n".join(lines) + "\n"


def _build_approval_report(approval_case: models.ApprovalCase) -> str:
    findings = list(approval_case.findings)
    partner_fee_findings = [
        finding for finding in findings if finding.category == "Partner Fee"
    ]
    missing_cost_findings = [
        finding
        for finding in findings
        if finding.category in {"비용누락", "鍮꾩슜?꾨씫"}
    ]

    return "\n".join(
        [
            "# LOTOS AI 결재심사서",
            "",
            "## 기본정보",
            f"- 고객명: {approval_case.customer_name}",
            f"- 거래구분: {approval_case.trade_type}",
            f"- Partner: {approval_case.partner_name or '-'}",
            f"- 담당자: {approval_case.pic or '-'}",
            f"- 업무코드: {approval_case.code}",
            f"- Point: {approval_case.point}",
            f"- POL: {approval_case.pol or '-'}",
            f"- POD: {approval_case.pod or '-'}",
            f"- PORT: {approval_case.port or '-'}",
            "",
            "## 수익성 분석",
            f"- 매출: {_format_jpy(approval_case.total_revenue_jpy)}",
            f"- 원가: {_format_jpy(approval_case.total_expense_jpy)}",
            f"- GP: {_format_jpy(approval_case.gp_jpy)}",
            f"- GP율: {_format_rate(approval_case.gp_rate)}",
            f"- 관세/소비세 제외 실매출: {_format_jpy(approval_case.net_revenue_ex_tax_jpy)}",
            f"- 관세/소비세 제외 실원가: {_format_jpy(approval_case.net_expense_ex_tax_jpy)}",
            f"- 관세/소비세 제외 GP율: {_format_rate(approval_case.net_gp_rate_ex_tax)}",
            f"- Minimum GP: {_format_jpy(approval_case.minimum_gp_jpy)}",
            "",
            "## LOTOS 기준 심사",
            _findings_table(findings),
            "## Partner Fee 심사",
            _findings_table(partner_fee_findings),
            "## 비용누락 검사",
            _findings_table(missing_cost_findings),
            "## 생산성 Point",
            f"- 담당자: {approval_case.pic or '-'}",
            f"- 업무코드: {approval_case.code}",
            f"- Point: {approval_case.point}",
            "",
            "## 대표이사 결재의견",
            approval_case.executive_comment,
            "",
            "## 최종 결재결과",
            approval_case.decision,
            "",
        ]
    )


@app.post(
    "/api/approvals/analyze-and-save",
    response_model=ApprovalSaveResponse,
    tags=["Approvals"],
)
def analyze_and_save_approval(
    case: ApprovalCaseInput,
    request: Request,
    db: Session = Depends(get_db),
) -> ApprovalSaveResponse:
    result = analyze_case_with_rules(case, db)
    approval_case = save_approval_case(db, case, result)
    create_audit_log(
        db,
        user_name=request.headers.get("X-USER-NAME"),
        action="SAVE_APPROVAL_CASE",
        entity_type="APPROVAL_CASE",
        entity_id=approval_case.id,
        detail=approval_case.customer_name,
        ip_address=request.client.host if request.client else None,
    )
    return ApprovalSaveResponse(approval_case_id=approval_case.id, result=result)


@app.post(
    "/api/approvals/analyze-sample-and-save/{sample_key}",
    response_model=ApprovalSaveResponse,
    tags=["Approvals"],
)
def analyze_sample_and_save_approval(
    sample_key: str,
    request: Request,
    db: Session = Depends(get_db),
) -> ApprovalSaveResponse:
    sample_case = SAMPLE_CASES.get(sample_key)
    if sample_case is None:
        raise HTTPException(status_code=404, detail="Sample case not found")
    result = analyze_case_with_rules(sample_case, db)
    approval_case = save_approval_case(db, sample_case, result)
    create_audit_log(
        db,
        user_name=request.headers.get("X-USER-NAME"),
        action="SAVE_APPROVAL_SAMPLE",
        entity_type="APPROVAL_CASE",
        entity_id=approval_case.id,
        detail=sample_key,
        ip_address=request.client.host if request.client else None,
    )
    return ApprovalSaveResponse(approval_case_id=approval_case.id, result=result)


@app.get(
    "/api/approvals",
    response_model=list[ApprovalListItem],
    tags=["Approvals"],
)
def list_approvals(db: Session = Depends(get_db)) -> list[ApprovalListItem]:
    approval_cases = db.execute(
        select(models.ApprovalCase)
        .order_by(models.ApprovalCase.created_at.desc())
        .limit(100)
    ).scalars()
    return [_to_approval_list_item(approval_case) for approval_case in approval_cases]


@app.get(
    "/api/approvals/{approval_case_id}",
    response_model=ApprovalDetail,
    tags=["Approvals"],
)
def get_approval_detail(
    approval_case_id: int,
    db: Session = Depends(get_db),
) -> ApprovalDetail:
    approval_case = db.execute(
        select(models.ApprovalCase)
        .options(selectinload(models.ApprovalCase.findings))
        .where(models.ApprovalCase.id == approval_case_id)
    ).scalar_one_or_none()
    if approval_case is None:
        raise HTTPException(status_code=404, detail="Approval case not found")
    return _to_approval_detail(approval_case)


@app.get(
    "/api/approvals/{approval_case_id}/report",
    response_class=Response,
    tags=["Approvals"],
)
def get_approval_report(
    approval_case_id: int,
    db: Session = Depends(get_db),
) -> Response:
    approval_case = db.execute(
        select(models.ApprovalCase)
        .options(selectinload(models.ApprovalCase.findings))
        .where(models.ApprovalCase.id == approval_case_id)
    ).scalar_one_or_none()
    if approval_case is None:
        raise HTTPException(status_code=404, detail="Approval case not found")
    return Response(
        content=_build_approval_report(approval_case),
        media_type="text/markdown; charset=utf-8",
    )


@app.get("/api/samples", response_model=list[str], tags=["Samples"])
def list_samples() -> list[str]:
    return list(SAMPLE_CASES.keys())


@app.get(
    "/api/samples/{sample_key}",
    response_model=ApprovalCaseInput,
    tags=["Samples"],
)
def get_sample(sample_key: str) -> ApprovalCaseInput:
    sample_case = SAMPLE_CASES.get(sample_key)
    if sample_case is None:
        raise HTTPException(status_code=404, detail="Sample case not found")
    return sample_case


@app.post(
    "/api/approvals/analyze-sample/{sample_key}",
    response_model=ApprovalResult,
    tags=["Approvals"],
)
def analyze_sample_approval(sample_key: str) -> ApprovalResult:
    sample_case = SAMPLE_CASES.get(sample_key)
    if sample_case is None:
        raise HTTPException(status_code=404, detail="Sample case not found")
    return analyze_case(sample_case)
