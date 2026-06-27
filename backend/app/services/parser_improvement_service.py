from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models


TRANSPORT_KEYWORDS = "DRAYAGE,TRUCKING,TRANSPORT,運送,운송"
CUSTOMS_KEYWORDS = "CUSTOMS,CUSTOM,通関,통관"
DUTY_KEYWORDS = "DUTY,関税,관세"
CONSUMPTION_TAX_KEYWORDS = "CONSUMPTION TAX,VAT,消費税,소비세"
PARTNER_FEE_KEYWORDS = "PARTNER FEE,AGENT FEE,CREDIT,パートナー,파트너"


def generate_suggestions_from_validation_result(
    db: Session,
    validation_result_id: int,
) -> list[models.ParserImprovementSuggestion]:
    result = db.get(models.ParserValidationResult, validation_result_id)
    if result is None:
        return []

    existing = db.execute(
        select(models.ParserImprovementSuggestion).where(
            models.ParserImprovementSuggestion.validation_result_id == validation_result_id
        )
    ).scalars().all()
    if existing:
        return list(existing)

    validation_case = db.get(models.ParserValidationCase, result.validation_case_id)
    if validation_case is None:
        return []

    template = _select_template_for_result(db, validation_case, result)
    suggestions: list[models.ParserImprovementSuggestion] = []
    tolerance = validation_case.tolerance_jpy

    if validation_case.expected_code and validation_case.expected_code != result.parsed_code:
        suggestions.append(
            _suggestion(
                validation_result_id=validation_result_id,
                template_id=template.id if template else None,
                case_name=validation_case.case_name,
                issue_type="CODE_MISMATCH",
                field_name="code",
                current_value=result.parsed_code,
                expected_value=validation_case.expected_code,
                suggestion_text=(
                    "업무코드 판정이 기대값과 다릅니다. "
                    "direction/mode/customs/transport/work 판정 키워드를 확인하세요."
                ),
            )
        )

    _compare_amount(
        suggestions,
        validation_result_id,
        template,
        validation_case,
        "gp_jpy",
        validation_case.expected_gp_jpy,
        result.parsed_gp_jpy,
        tolerance,
        "AMOUNT_MISMATCH",
        None,
        "GP 값이 기대값과 다릅니다. Revenue/Expense Total 키워드 또는 Profit 키워드를 확인하세요.",
    )
    _compare_amount(
        suggestions,
        validation_result_id,
        template,
        validation_case,
        "transport_revenue_jpy",
        validation_case.expected_transport_revenue_jpy,
        result.parsed_transport_revenue_jpy,
        tolerance,
        "TRANSPORT_MISMATCH",
        TRANSPORT_KEYWORDS,
        "운송 매출이 기대값과 다릅니다. transport_keywords에 누락된 표현이 있는지 확인하세요.",
    )
    _compare_amount(
        suggestions,
        validation_result_id,
        template,
        validation_case,
        "transport_expense_jpy",
        validation_case.expected_transport_expense_jpy,
        result.parsed_transport_expense_jpy,
        tolerance,
        "TRANSPORT_MISMATCH",
        TRANSPORT_KEYWORDS,
        "운송 원가가 기대값과 다릅니다. transport_keywords와 Expense 영역 키워드를 확인하세요.",
    )
    _compare_amount(
        suggestions,
        validation_result_id,
        template,
        validation_case,
        "customs_revenue_jpy",
        validation_case.expected_customs_revenue_jpy,
        result.parsed_customs_revenue_jpy,
        tolerance,
        "CUSTOMS_MISMATCH",
        CUSTOMS_KEYWORDS,
        "통관 매출이 기대값과 다릅니다. customs_keywords에 누락된 표현이 있는지 확인하세요.",
    )
    _compare_amount(
        suggestions,
        validation_result_id,
        template,
        validation_case,
        "customs_duty_jpy",
        validation_case.expected_customs_duty_jpy,
        result.parsed_customs_duty_jpy,
        tolerance,
        "TAX_MISMATCH",
        DUTY_KEYWORDS,
        "관세 추출이 기대값과 다릅니다. duty_keywords에 누락된 표현이 있는지 확인하세요.",
    )
    _compare_amount(
        suggestions,
        validation_result_id,
        template,
        validation_case,
        "consumption_tax_jpy",
        validation_case.expected_consumption_tax_jpy,
        result.parsed_consumption_tax_jpy,
        tolerance,
        "TAX_MISMATCH",
        CONSUMPTION_TAX_KEYWORDS,
        "소비세 추출이 기대값과 다릅니다. consumption_tax_keywords에 누락된 표현이 있는지 확인하세요.",
    )
    _compare_amount(
        suggestions,
        validation_result_id,
        template,
        validation_case,
        "partner_fee_jpy",
        validation_case.expected_partner_fee_jpy,
        result.parsed_partner_fee_jpy,
        tolerance,
        "PARTNER_FEE_MISMATCH",
        PARTNER_FEE_KEYWORDS,
        "Partner Fee 추출이 기대값과 다릅니다. Partner Fee Rule 또는 partner_fee_keywords를 확인하세요.",
    )
    _compare_amount(
        suggestions,
        validation_result_id,
        template,
        validation_case,
        "partner_fee_usd",
        validation_case.expected_partner_fee_usd,
        result.parsed_partner_fee_usd,
        0.01,
        "PARTNER_FEE_MISMATCH",
        PARTNER_FEE_KEYWORDS,
        "Partner Fee 추출이 기대값과 다릅니다. Partner Fee Rule 또는 partner_fee_keywords를 확인하세요.",
    )

    for suggestion in suggestions:
        db.add(suggestion)
    db.commit()
    for suggestion in suggestions:
        db.refresh(suggestion)
    return suggestions


def _select_template_for_result(
    db: Session,
    validation_case: models.ParserValidationCase,
    result: models.ParserValidationResult,
) -> models.ParserTemplate | None:
    file_type = None
    if result.upload_id:
        upload = db.execute(
            select(models.ProfitUpload).where(models.ProfitUpload.upload_id == result.upload_id)
        ).scalar_one_or_none()
        if upload:
            file_type = "PDF" if upload.file_ext.lower() == ".pdf" else "EXCEL"

    direction = _direction_from_code(validation_case.expected_code or result.parsed_code)
    statement = select(models.ParserTemplate).where(models.ParserTemplate.is_active == True)  # noqa: E712
    if file_type:
        statement = statement.where(models.ParserTemplate.file_type.in_([file_type, "ANY"]))
    if direction:
        specific = db.execute(
            statement.where(models.ParserTemplate.direction == direction).order_by(
                models.ParserTemplate.is_default.asc(),
                models.ParserTemplate.id.asc(),
            )
        ).scalars().first()
        if specific:
            return specific

    default = db.execute(
        select(models.ParserTemplate)
        .where(
            models.ParserTemplate.is_active == True,  # noqa: E712
            models.ParserTemplate.is_default == True,  # noqa: E712
        )
        .order_by(models.ParserTemplate.id.asc())
    ).scalars().first()
    if default:
        return default
    return db.execute(statement.order_by(models.ParserTemplate.id.asc())).scalars().first()


def _direction_from_code(code: str | None) -> str | None:
    if not code:
        return None
    if code.startswith(("SE", "AE")):
        return "EXPORT"
    if code.startswith(("SI", "AI")):
        return "IMPORT"
    return None


def _compare_amount(
    suggestions: list[models.ParserImprovementSuggestion],
    validation_result_id: int,
    template: models.ParserTemplate | None,
    validation_case: models.ParserValidationCase,
    field_name: str,
    expected: float | None,
    current: float | None,
    tolerance: float,
    issue_type: str,
    suggested_keyword: str | None,
    suggestion_text: str,
) -> None:
    if expected is None:
        return
    current_value = current or 0
    if abs(current_value - expected) <= tolerance:
        return
    suggestions.append(
        _suggestion(
            validation_result_id=validation_result_id,
            template_id=template.id if template else None,
            case_name=validation_case.case_name,
            issue_type=issue_type,
            field_name=field_name,
            current_value=f"{current_value:g}",
            expected_value=f"{expected:g}",
            suggested_keyword=suggested_keyword,
            suggestion_text=suggestion_text,
        )
    )


def _suggestion(
    validation_result_id: int,
    template_id: int | None,
    case_name: str,
    issue_type: str,
    field_name: str,
    suggestion_text: str,
    current_value: str | None = None,
    expected_value: str | None = None,
    suggested_keyword: str | None = None,
) -> models.ParserImprovementSuggestion:
    return models.ParserImprovementSuggestion(
        validation_result_id=validation_result_id,
        template_id=template_id,
        case_name=case_name,
        issue_type=issue_type,
        field_name=field_name,
        current_value=current_value,
        expected_value=expected_value,
        suggested_keyword=suggested_keyword,
        suggestion_text=suggestion_text,
        status="OPEN",
    )
