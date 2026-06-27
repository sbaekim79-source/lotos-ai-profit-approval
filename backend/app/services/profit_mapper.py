from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models
from app.schemas import ApprovalCaseInput, ChargeItem, PartnerFeeInput


class ParserTemplateLike(Protocol):
    template_name: str
    description: str | None
    mode: str | None
    direction: str | None
    file_type: str
    customer_keyword: str | None
    partner_keyword: str | None
    revenue_section_keywords: str
    expense_section_keywords: str
    profit_keywords: str
    duty_keywords: str
    consumption_tax_keywords: str
    transport_keywords: str
    customs_keywords: str
    partner_fee_keywords: str
    food_keywords: str
    is_default: bool
    is_active: bool


@dataclass(frozen=True)
class DefaultParserTemplate:
    template_name: str = "CODE_FALLBACK_STANDARD"
    description: str | None = "Built-in fallback parser template"
    mode: str | None = "ANY"
    direction: str | None = "ANY"
    file_type: str = "ANY"
    customer_keyword: str | None = "CUSTOMER,CONSIGNEE,SHIPPER,고객"
    partner_keyword: str | None = "PARTNER,AGENT,파트너"
    revenue_section_keywords: str = "REVENUE,BILLING,DEBIT,請求,청구,매출"
    expense_section_keywords: str = "EXPENSE,COST,CREDIT,支払,原価,비용,원가"
    profit_keywords: str = "PROFIT,GP,GROSS PROFIT,差益,이익"
    duty_keywords: str = "DUTY,関税,관세"
    consumption_tax_keywords: str = "CONSUMPTION TAX,VAT,消費税,소비세"
    transport_keywords: str = (
        "DRAYAGE,TRUCKING,TRANSPORT,DELIVERY,運送,配送,운송,배송"
    )
    customs_keywords: str = "CUSTOMS,CUSTOM,通関,통관"
    partner_fee_keywords: str = "PARTNER FEE,AGENT FEE,CREDIT,パートナー,파트너"
    food_keywords: str = "FOOD,FROZEN,食品,식품,냉동"
    is_default: bool = True
    is_active: bool = True


@dataclass(frozen=True)
class ParsedAmount:
    currency: str
    amount: float


@dataclass(frozen=True)
class ParsedRow:
    cells: list[str]
    text: str
    upper_text: str


CONTAINER_PATTERN = re.compile(
    r"(20\s*'?\s*D/?C|20DC|20FT|20RF|40DC|40HC|40HQ|LCL)",
    re.IGNORECASE,
)
USD_PATTERN = re.compile(
    r"\(?\s*(?:USD\s*[-+]?\d[\d,\s]*(?:\.\d+)?|[-+]?\d[\d,\s]*(?:\.\d+)?\s*USD)\s*\)?",
    re.IGNORECASE,
)
NUMBER_PATTERN = re.compile(
    r"\(?\s*(?:JPY|¥)?\s*[-+]?\d[\d,\s]*(?:\.\d+)?\s*(?:円)?\s*\)?",
    re.IGNORECASE,
)

SEA_KEYWORDS = ["SEA", "OCEAN", "VESSEL", "B/L", "CY", "CFS", "해상"]
AIR_KEYWORDS = ["AIR", "AWB", "항공"]
EXPORT_KEYWORDS = ["EXPORT", "수출", "POL", "ETD"]
IMPORT_PRIORITY_KEYWORDS = ["D/O", "DO FEE", "IMPORT", "수입", "ETA"]
WORK_KEYWORDS = ["DEVANNING", "W/H", "WAREHOUSE", "창고", "작업", "LABEL", "라벨"]
REVENUE_TOTAL_KEYWORDS = [
    "TOTAL REVENUE",
    "REVENUE TOTAL",
    "売上合計",
    "請求合計",
    "매출합계",
    "청구합계",
]
EXPENSE_TOTAL_KEYWORDS = [
    "TOTAL EXPENSE",
    "EXPENSE TOTAL",
    "COST TOTAL",
    "原価合計",
    "支払合計",
    "원가합계",
    "비용합계",
]


def map_parse_result_to_case(
    parse_result: dict[str, Any],
    db: Session | None = None,
) -> ApprovalCaseInput:
    return map_parse_result_with_metadata(parse_result, db=db)["candidate"]


def map_parse_result_with_metadata(
    parse_result: dict[str, Any],
    db: Session | None = None,
    file_ext: str | None = None,
) -> dict[str, Any]:
    template = select_parser_template(parse_result, db=db, file_ext=file_ext)
    keyword_sets = _keyword_sets(template)
    combined_text = _combined_text(parse_result)
    upper_text = combined_text.upper()
    rows = _iter_rows(parse_result)
    warnings: list[str] = [str(warning) for warning in parse_result.get("warnings") or []]
    if parse_result.get("ocr_status") == "ocr_unavailable":
        warnings.append("OCR 엔진이 없어 이미지형 PDF 내용을 자동 매핑하지 못했습니다.")
    elif parse_result.get("ocr_status") == "ocr_failed":
        warnings.append("이미지형 PDF OCR을 시도했지만 텍스트를 추출하지 못했습니다.")

    customer_name = _extract_customer_name(combined_text, keyword_sets["customer"])
    if customer_name == "UNKNOWN CUSTOMER":
        warnings.append("고객명을 자동 추출하지 못했습니다.")

    mode = _determine_mode(upper_text, warnings)
    direction = _determine_direction(upper_text, warnings)
    container_type = _extract_container_type(combined_text)
    container_count = _extract_container_count(combined_text, container_type)

    extracted = _extract_financial_items(rows, keyword_sets)
    revenue_items = extracted["revenue_items"]
    expense_items = extracted["expense_items"]

    if not revenue_items:
        revenue_items = [ChargeItem(name="TOTAL", amount_jpy=0)]
        warnings.append("매출 총액 또는 매출 항목을 자동 추출하지 못했습니다.")
    if not expense_items:
        expense_items = [ChargeItem(name="TOTAL", amount_jpy=0)]
        warnings.append("원가 총액 또는 원가 항목을 자동 추출하지 못했습니다.")

    _append_profit_validation_warning(
        revenue_items,
        expense_items,
        extracted["profit_amount"],
        warnings,
    )

    partner_fee = _extract_partner_fee(
        rows=rows,
        container_type=container_type,
        container_count=container_count,
        keywords=keyword_sets["partner_fee"],
    )

    has_customs_amount = (
        extracted["customs_revenue_jpy"] > 0
        or extracted["customs_expense_jpy"] > 0
    )
    has_transport_amount = (
        extracted["transport_revenue_jpy"] > 0
        or extracted["transport_expense_jpy"] > 0
    )

    candidate = ApprovalCaseInput(
        customer_name=customer_name,
        trade_type="PARTNER",
        partner_name=partner_fee.partner_name if partner_fee else None,
        shipper_name=_extract_labeled_value(combined_text, "SHIPPER"),
        pic=_extract_labeled_value(combined_text, "PIC"),
        mode=mode,
        direction=direction,
        has_customs=has_customs_amount
        or _contains_customs_text(upper_text, keyword_sets["customs"]),
        has_transport=has_transport_amount
        or _contains_any(upper_text, keyword_sets["transport"]),
        has_work=_contains_any(upper_text, WORK_KEYWORDS),
        pol=_extract_labeled_value(combined_text, "POL"),
        pod=_extract_labeled_value(combined_text, "POD"),
        port=_extract_labeled_value(combined_text, "PORT"),
        cargo_description=_extract_labeled_value(combined_text, "CARGO"),
        container_type=container_type,
        container_count=container_count,
        revenue_items=revenue_items,
        expense_items=expense_items,
        customs_duty_jpy=extracted["customs_duty_jpy"],
        consumption_tax_jpy=extracted["consumption_tax_jpy"],
        transport_revenue_jpy=extracted["transport_revenue_jpy"],
        transport_expense_jpy=extracted["transport_expense_jpy"],
        customs_revenue_jpy=extracted["customs_revenue_jpy"],
        customs_expense_jpy=extracted["customs_expense_jpy"],
        self_customs=True,
        partner_fee=partner_fee,
    )

    confidence = _calculate_confidence(candidate, warnings, template)
    template_used = {
        "template_name": template.template_name,
        "file_type": template.file_type,
        "mode": template.mode,
        "direction": template.direction,
        "is_default": template.is_default,
    }
    return {
        "candidate": candidate,
        "case": candidate,
        "parsing_confidence": confidence,
        "confidence": confidence,
        "warnings": warnings,
        "template_used": template_used,
    }


def select_parser_template(
    parse_result: dict[str, Any],
    db: Session | None = None,
    file_ext: str | None = None,
) -> ParserTemplateLike:
    fallback = DefaultParserTemplate()
    if db is None:
        return fallback

    file_type = _file_type_from_ext(file_ext or str(parse_result.get("file_ext") or ""))
    raw_text = _combined_text(parse_result).upper()
    direction = _direction_hint(raw_text)

    try:
        templates = list(
            db.execute(
                select(models.ParserTemplate).where(
                    models.ParserTemplate.is_active.is_(True)
                )
            ).scalars()
        )
    except SQLAlchemyError:
        return fallback
    if not templates:
        return fallback

    candidates = [
        template
        for template in templates
        if template.file_type in {file_type, "ANY"}
    ]
    if not candidates:
        candidates = templates

    if direction is not None:
        directional = [
            template
            for template in candidates
            if template.direction == direction and template.file_type in {file_type, "ANY"}
        ]
        if directional:
            return _best_specific_template(directional, direction)

    default_candidates = [
        template
        for template in candidates
        if template.is_default and template.file_type in {file_type, "ANY"}
    ]
    if default_candidates:
        return _best_specific_template(default_candidates, direction)

    return _best_specific_template(candidates, direction)


def _best_specific_template(
    templates: list[models.ParserTemplate],
    direction: str | None,
) -> models.ParserTemplate:
    return sorted(
        templates,
        key=lambda template: (
            template.direction in {direction, "EXPORT", "IMPORT"},
            template.file_type != "ANY",
            not template.is_default,
            template.id,
        ),
        reverse=True,
    )[0]


def _file_type_from_ext(file_ext: str | None) -> str:
    normalized = (file_ext or "").lower()
    if normalized == ".pdf":
        return "PDF"
    if normalized in {".xlsx", ".xls"}:
        return "EXCEL"
    return "ANY"


def _direction_hint(upper_text: str) -> str | None:
    import_score = sum(1 for keyword in IMPORT_PRIORITY_KEYWORDS if keyword in upper_text)
    export_score = sum(1 for keyword in EXPORT_KEYWORDS if keyword in upper_text)
    if "D/O" in upper_text or "DO FEE" in upper_text:
        import_score += 2
    if "B/L FEE" in upper_text and "D/O" not in upper_text:
        export_score += 2
    if import_score > export_score:
        return "IMPORT"
    if export_score > import_score:
        return "EXPORT"
    return None


def _keyword_sets(template: ParserTemplateLike) -> dict[str, list[str]]:
    return {
        "customer": _split_keywords(template.customer_keyword)
        or ["CUSTOMER", "CONSIGNEE", "SHIPPER", "고객"],
        "partner": _split_keywords(template.partner_keyword)
        or ["PARTNER", "AGENT", "파트너"],
        "revenue": _split_keywords(template.revenue_section_keywords),
        "expense": _split_keywords(template.expense_section_keywords),
        "profit": _split_keywords(template.profit_keywords),
        "duty": _split_keywords(template.duty_keywords),
        "consumption_tax": _split_keywords(template.consumption_tax_keywords),
        "transport": _split_keywords(template.transport_keywords),
        "customs": _split_keywords(template.customs_keywords),
        "partner_fee": _split_keywords(template.partner_fee_keywords),
        "food": _split_keywords(template.food_keywords),
    }


def _split_keywords(value: str | None) -> list[str]:
    return [keyword.strip() for keyword in (value or "").split(",") if keyword.strip()]


def _combined_text(parse_result: dict[str, Any]) -> str:
    parts = [str(parse_result.get("raw_text") or "")]
    for row in _iter_rows(parse_result):
        parts.append(row.text)
    return "\n".join(parts)


def _iter_rows(parse_result: dict[str, Any]) -> list[ParsedRow]:
    parsed_rows: list[ParsedRow] = []
    for table in parse_result.get("raw_tables") or []:
        for row in table.get("rows") or []:
            cells = [
                str(cell).strip()
                for cell in row
                if cell is not None and str(cell).strip()
            ]
            if not cells:
                continue
            text = " ".join(cells)
            parsed_rows.append(ParsedRow(cells=cells, text=text, upper_text=text.upper()))
    return parsed_rows


def _contains_any(value: str | None, keywords: list[str]) -> bool:
    if value is None:
        return False
    normalized = value.upper()
    return any(keyword.upper() in normalized for keyword in keywords)


def _contains_customs_text(value: str | None, keywords: list[str]) -> bool:
    if value is None:
        return False
    normalized = value.upper()
    for keyword in keywords:
        upper_keyword = keyword.upper()
        if upper_keyword == "CUSTOM":
            if re.search(r"\bCUSTOM\b", normalized):
                return True
            continue
        if upper_keyword in normalized:
            return True
    return False


def _extract_customer_name(text: str, keywords: list[str]) -> str:
    label_group = "|".join(re.escape(keyword) for keyword in keywords)
    patterns = [
        rf"(?:{label_group})\s*[:：\-]\s*([^\n\r]+)",
        rf"(?:{label_group})\s+([A-Za-z0-9 .,&()_\-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip(" :：-\t")
            if value:
                return value[:120]
    return "UNKNOWN CUSTOMER"


def _determine_mode(upper_text: str, warnings: list[str]) -> str:
    if _contains_any(upper_text, SEA_KEYWORDS):
        return "SEA"
    if _contains_any(upper_text, AIR_KEYWORDS):
        return "AIR"
    warnings.append("해상/항공 구분을 명확히 찾지 못해 SEA로 기본 설정했습니다.")
    return "SEA"


def _determine_direction(upper_text: str, warnings: list[str]) -> str:
    has_import = _contains_any(upper_text, IMPORT_PRIORITY_KEYWORDS)
    has_export = _contains_any(upper_text, EXPORT_KEYWORDS)
    if has_import:
        return "IMPORT"
    if has_export or ("B/L FEE" in upper_text and "D/O" not in upper_text):
        return "EXPORT"
    warnings.append("수출/수입 방향을 명확히 찾지 못해 EXPORT로 기본 설정했습니다.")
    return "EXPORT"


def _extract_container_type(text: str) -> str | None:
    match = CONTAINER_PATTERN.search(text)
    if not match:
        return None
    value = re.sub(r"\s+", "", match.group(1).upper())
    if value in {"20'D/C", "20D/C"}:
        return "20DC"
    return value


def _extract_container_count(text: str, container_type: str | None) -> int:
    if container_type is None:
        return 1
    escaped = re.escape(container_type)
    patterns = [
        rf"{escaped}\s*[x×*]\s*(\d+)",
        rf"(\d+)\s*[x×*]\s*{escaped}",
        rf"{escaped}\s+(\d+)",
        rf"(\d+)\s+{escaped}",
    ]
    compact_text = text.replace("'", "").replace("/", "")
    for pattern in patterns:
        match = re.search(pattern, compact_text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return 1


def _extract_labeled_value(text: str, label: str) -> str | None:
    match = re.search(rf"{label}\s*[:：\-]\s*([^\n\r]+)", text, flags=re.IGNORECASE)
    if not match:
        return None
    value = match.group(1).strip(" :：-\t")
    return value[:120] or None


def _extract_financial_items(
    rows: list[ParsedRow],
    keywords: dict[str, list[str]],
) -> dict[str, Any]:
    section: str | None = None
    revenue_detail_items: list[ChargeItem] = []
    expense_detail_items: list[ChargeItem] = []
    revenue_total: float | None = None
    expense_total: float | None = None
    profit_amount: float | None = None

    transport_revenue_jpy = 0.0
    transport_expense_jpy = 0.0
    customs_revenue_jpy = 0.0
    customs_expense_jpy = 0.0
    customs_duty_jpy = 0.0
    consumption_tax_jpy = 0.0

    for row in rows:
        if _contains_any(row.upper_text, keywords["revenue"]):
            section = "revenue"
        elif _contains_any(row.upper_text, keywords["expense"]):
            section = "expense"
        elif _contains_any(row.upper_text, keywords["profit"]):
            section = "profit"

        amount = _last_jpy_amount(row.cells)
        if amount is None:
            continue

        item_name = _first_label_cell(row.cells) or "TOTAL"

        if _contains_any(row.upper_text, REVENUE_TOTAL_KEYWORDS):
            revenue_total = amount
            continue
        if _contains_any(row.upper_text, EXPENSE_TOTAL_KEYWORDS):
            expense_total = amount
            continue
        if _contains_any(row.upper_text, keywords["profit"]) and section == "profit":
            profit_amount = amount
            continue

        if _contains_any(row.upper_text, keywords["duty"]):
            customs_duty_jpy += amount
        if _contains_any(row.upper_text, keywords["consumption_tax"]):
            consumption_tax_jpy += amount

        if section == "revenue" or _contains_any(row.upper_text, keywords["revenue"]):
            revenue_detail_items.append(ChargeItem(name=item_name, amount_jpy=amount))
            if _contains_any(row.upper_text, keywords["transport"]):
                transport_revenue_jpy += amount
            if _contains_any(row.upper_text, keywords["customs"]):
                customs_revenue_jpy += amount
        elif section == "expense" or _contains_any(row.upper_text, keywords["expense"]):
            expense_detail_items.append(ChargeItem(name=item_name, amount_jpy=amount))
            if _contains_any(row.upper_text, keywords["transport"]):
                transport_expense_jpy += amount
            if _contains_any(row.upper_text, keywords["customs"]):
                customs_expense_jpy += amount

    revenue_items = (
        [ChargeItem(name="TOTAL", amount_jpy=revenue_total)]
        if revenue_total is not None
        else revenue_detail_items
    )
    expense_items = (
        [ChargeItem(name="TOTAL", amount_jpy=expense_total)]
        if expense_total is not None
        else expense_detail_items
    )

    return {
        "revenue_items": revenue_items,
        "expense_items": expense_items,
        "profit_amount": profit_amount,
        "transport_revenue_jpy": transport_revenue_jpy,
        "transport_expense_jpy": transport_expense_jpy,
        "customs_revenue_jpy": customs_revenue_jpy,
        "customs_expense_jpy": customs_expense_jpy,
        "customs_duty_jpy": customs_duty_jpy,
        "consumption_tax_jpy": consumption_tax_jpy,
    }


def _append_profit_validation_warning(
    revenue_items: list[ChargeItem],
    expense_items: list[ChargeItem],
    profit_amount: float | None,
    warnings: list[str],
) -> None:
    if profit_amount is None or not revenue_items or not expense_items:
        return
    calculated_gp = sum(item.amount_jpy for item in revenue_items) - sum(
        item.amount_jpy for item in expense_items
    )
    if abs(calculated_gp - profit_amount) > max(1000, abs(profit_amount) * 0.02):
        warnings.append(
            f"Profit Sheet Profit {profit_amount:.0f}엔과 계산 GP {calculated_gp:.0f}엔의 차이가 큽니다."
        )


def _extract_partner_fee(
    rows: list[ParsedRow],
    container_type: str | None,
    container_count: int,
    keywords: list[str],
) -> PartnerFeeInput | None:
    for row in rows:
        if not _contains_any(row.upper_text, keywords):
            continue
        usd_amount = _last_currency_amount(row.cells, "USD")
        jpy_amount = _last_currency_amount(row.cells, "JPY")
        if usd_amount is None and jpy_amount is None:
            continue
        return PartnerFeeInput(
            partner_name=_extract_partner_name_from_row(row, keywords),
            actual_fee_jpy=jpy_amount or 0,
            actual_fee_usd=usd_amount or 0,
            bl_count=1,
            container_type=container_type,
            container_count=container_count,
            special_condition=None,
        )
    return None


def _extract_partner_name_from_row(row: ParsedRow, keywords: list[str]) -> str | None:
    for cell in row.cells:
        if _contains_any(cell, keywords):
            continue
        if (
            _last_currency_amount([cell], "USD") is None
            and _last_currency_amount([cell], "JPY") is None
        ):
            return cell[:120]
    return None


def _last_jpy_amount(cells: list[str]) -> float | None:
    return _last_currency_amount(cells, "JPY")


def _last_currency_amount(cells: list[str], currency: str) -> float | None:
    amounts: list[float] = []
    for cell in cells:
        amounts.extend(
            amount.amount
            for amount in _extract_amounts(cell)
            if amount.currency == currency
        )
    if not amounts:
        return None
    return amounts[-1]


def _extract_amounts(value: str) -> list[ParsedAmount]:
    amounts: list[ParsedAmount] = []
    usd_spans: list[tuple[int, int]] = []
    for match in USD_PATTERN.finditer(value):
        amount = _parse_numeric_token(match.group(0), "USD")
        if amount is not None:
            amounts.append(ParsedAmount(currency="USD", amount=amount))
            usd_spans.append(match.span())

    for match in NUMBER_PATTERN.finditer(value):
        if any(start <= match.start() < end for start, end in usd_spans):
            continue
        amount = _parse_numeric_token(match.group(0), "JPY")
        if amount is not None:
            amounts.append(ParsedAmount(currency="JPY", amount=amount))
    return amounts


def _parse_numeric_token(token: str, currency: str) -> float | None:
    cleaned = token.strip()
    is_negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("() ")
    cleaned = re.sub(currency, "", cleaned, flags=re.IGNORECASE)
    cleaned = (
        cleaned.replace("JPY", "")
        .replace("USD", "")
        .replace("円", "")
        .replace("¥", "")
        .replace(",", "")
        .replace(" ", "")
        .strip()
    )
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", cleaned):
        return None
    amount = float(cleaned)
    return -amount if is_negative else amount


def _first_label_cell(cells: list[str]) -> str | None:
    for cell in cells:
        if _extract_amounts(cell):
            continue
        return cell
    return None


def _calculate_confidence(
    candidate: ApprovalCaseInput,
    warnings: list[str],
    template: ParserTemplateLike,
) -> float:
    score = 1.0
    if candidate.customer_name == "UNKNOWN CUSTOMER":
        score -= 0.2
    if candidate.revenue_items == [ChargeItem(name="TOTAL", amount_jpy=0)]:
        score -= 0.25
    if candidate.expense_items == [ChargeItem(name="TOTAL", amount_jpy=0)]:
        score -= 0.25
    if candidate.container_type is None:
        score -= 0.05
    if not candidate.has_customs and candidate.customs_revenue_jpy == 0:
        score -= 0.03
    if not candidate.has_transport and candidate.transport_revenue_jpy == 0:
        score -= 0.03
    if template.template_name == "CODE_FALLBACK_STANDARD":
        score -= 0.05
    score -= min(len(warnings) * 0.05, 0.25)
    return max(round(score, 2), 0.0)
