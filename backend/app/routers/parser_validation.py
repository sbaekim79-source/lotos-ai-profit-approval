from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import (
    ParserValidationCaseCreate,
    ParserValidationCaseRead,
    ParserValidationResultRead,
    ParserValidationRunAllRequest,
    ParserValidationRunRequest,
)
from app.services.approval_engine import analyze_case_with_rules
from app.services.audit_service import create_audit_log
from app.services.parser_improvement_service import (
    generate_suggestions_from_validation_result,
)
from app.services.profit_mapper import map_parse_result_with_metadata
from app.services.profit_parser import parse_profit_file


router = APIRouter(prefix="/api/parser-validation", tags=["Parser Validation"])


@router.get("/cases", response_model=list[ParserValidationCaseRead])
def list_cases(
    is_active: bool | None = None,
    db: Session = Depends(get_db),
) -> list[ParserValidationCaseRead]:
    statement = select(models.ParserValidationCase).order_by(
        models.ParserValidationCase.case_name
    )
    if is_active is not None:
        statement = statement.where(models.ParserValidationCase.is_active == is_active)
    return [_to_case_read(row) for row in db.execute(statement).scalars()]


@router.post("/cases", response_model=ParserValidationCaseRead)
def create_case(
    payload: ParserValidationCaseCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> ParserValidationCaseRead:
    row = models.ParserValidationCase(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    _audit(db, request, "CREATE_PARSER_VALIDATION_CASE", "PARSER_VALIDATION_CASE", row.id, row.case_name)
    return _to_case_read(row)


@router.put("/cases/{case_id}", response_model=ParserValidationCaseRead)
def update_case(
    case_id: int,
    payload: ParserValidationCaseCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> ParserValidationCaseRead:
    row = db.get(models.ParserValidationCase, case_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Parser validation case not found")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    _audit(db, request, "UPDATE_PARSER_VALIDATION_CASE", "PARSER_VALIDATION_CASE", row.id, row.case_name)
    return _to_case_read(row)


@router.delete("/cases/{case_id}", response_model=ParserValidationCaseRead)
def deactivate_case(
    case_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> ParserValidationCaseRead:
    row = db.get(models.ParserValidationCase, case_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Parser validation case not found")
    row.is_active = False
    db.commit()
    db.refresh(row)
    _audit(db, request, "DEACTIVATE_PARSER_VALIDATION_CASE", "PARSER_VALIDATION_CASE", row.id, row.case_name)
    return _to_case_read(row)


@router.post("/cases/{case_id}/run", response_model=ParserValidationResultRead)
def run_case(
    case_id: int,
    payload: ParserValidationRunRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ParserValidationResultRead:
    validation_case = db.get(models.ParserValidationCase, case_id)
    if validation_case is None or not validation_case.is_active:
        raise HTTPException(status_code=404, detail="Parser validation case not found")
    result = _run_validation(db, validation_case, payload.upload_id)
    _audit(db, request, "RUN_PARSER_VALIDATION", "PARSER_VALIDATION_RESULT", result.id, result.diff_summary)
    return _to_result_read(result)


@router.post("/run-all", response_model=list[ParserValidationResultRead])
def run_all(
    payload: ParserValidationRunAllRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> list[ParserValidationResultRead]:
    rows = db.execute(
        select(models.ParserValidationCase).where(
            models.ParserValidationCase.is_active == True  # noqa: E712
        )
    ).scalars()
    results = []
    for validation_case in rows:
        upload_id = payload.upload_mapping.get(validation_case.case_name)
        if not upload_id:
            continue
        result = _run_validation(db, validation_case, upload_id)
        _audit(db, request, "RUN_PARSER_VALIDATION", "PARSER_VALIDATION_RESULT", result.id, result.diff_summary)
        results.append(_to_result_read(result))
    return results


@router.get("/results", response_model=list[ParserValidationResultRead])
def list_results(
    case_id: int | None = None,
    result: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
) -> list[ParserValidationResultRead]:
    statement = select(models.ParserValidationResult).order_by(
        models.ParserValidationResult.created_at.desc()
    )
    if case_id is not None:
        statement = statement.where(models.ParserValidationResult.validation_case_id == case_id)
    if result:
        statement = statement.where(models.ParserValidationResult.result == result)
    if start_date:
        statement = statement.where(models.ParserValidationResult.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        statement = statement.where(
            models.ParserValidationResult.created_at
            <= datetime.fromisoformat(end_date).replace(hour=23, minute=59, second=59)
        )
    return [_to_result_read(row) for row in db.execute(statement.limit(500)).scalars()]


def _run_validation(
    db: Session,
    validation_case: models.ParserValidationCase,
    upload_id: str,
) -> models.ParserValidationResult:
    upload = db.execute(
        select(models.ProfitUpload).where(models.ProfitUpload.upload_id == upload_id)
    ).scalar_one_or_none()
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    file_path = Path(upload.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded file not found")

    parse_result = parse_profit_file(str(file_path), upload.file_ext)
    mapped = map_parse_result_with_metadata(parse_result, db=db, file_ext=upload.file_ext)
    candidate = mapped["candidate"]
    approval_result = analyze_case_with_rules(candidate, db)

    diffs = _compare(validation_case, candidate, approval_result)
    major_fail = any(diff.startswith("MAJOR:") for diff in diffs)
    result_status = "PASS" if not diffs else "FAIL" if major_fail else "PARTIAL"
    diff_summary = " / ".join(diff.replace("MAJOR:", "") for diff in diffs) or "All checks passed"

    partner_fee = candidate.partner_fee
    row = models.ParserValidationResult(
        validation_case_id=validation_case.id,
        upload_id=upload_id,
        parsed_customer_name=candidate.customer_name,
        parsed_code=approval_result.code,
        parsed_gp_jpy=approval_result.gp_jpy,
        parsed_decision=approval_result.decision,
        parsed_transport_revenue_jpy=candidate.transport_revenue_jpy,
        parsed_transport_expense_jpy=candidate.transport_expense_jpy,
        parsed_customs_revenue_jpy=candidate.customs_revenue_jpy,
        parsed_customs_duty_jpy=candidate.customs_duty_jpy,
        parsed_consumption_tax_jpy=candidate.consumption_tax_jpy,
        parsed_partner_fee_jpy=partner_fee.actual_fee_jpy if partner_fee else None,
        parsed_partner_fee_usd=partner_fee.actual_fee_usd if partner_fee else None,
        confidence=mapped.get("confidence") or mapped.get("parsing_confidence"),
        result=result_status,
        diff_summary=diff_summary,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    if row.result in {"PARTIAL", "FAIL"}:
        generate_suggestions_from_validation_result(db, row.id)
    return row


def _compare(
    validation_case: models.ParserValidationCase,
    candidate,
    approval_result,
) -> list[str]:
    diffs: list[str] = []
    tolerance = validation_case.tolerance_jpy

    if validation_case.expected_customer_name:
        expected = validation_case.expected_customer_name.upper()
        actual = (candidate.customer_name or "").upper()
        if expected not in actual:
            diffs.append(f"customer 불일치 expected={validation_case.expected_customer_name}, actual={candidate.customer_name}")

    if validation_case.expected_code and approval_result.code != validation_case.expected_code:
        diffs.append(f"MAJOR:code 불일치 expected={validation_case.expected_code}, actual={approval_result.code}")

    _compare_amount(diffs, "GP", validation_case.expected_gp_jpy, approval_result.gp_jpy, tolerance, major=True)
    _compare_amount(diffs, "운송매출", validation_case.expected_transport_revenue_jpy, candidate.transport_revenue_jpy, tolerance)
    _compare_amount(diffs, "운송원가", validation_case.expected_transport_expense_jpy, candidate.transport_expense_jpy, tolerance)
    _compare_amount(diffs, "통관매출", validation_case.expected_customs_revenue_jpy, candidate.customs_revenue_jpy, tolerance)
    _compare_amount(diffs, "관세", validation_case.expected_customs_duty_jpy, candidate.customs_duty_jpy, tolerance)
    _compare_amount(diffs, "소비세", validation_case.expected_consumption_tax_jpy, candidate.consumption_tax_jpy, tolerance)

    partner_fee = candidate.partner_fee
    _compare_amount(
        diffs,
        "Partner Fee JPY",
        validation_case.expected_partner_fee_jpy,
        partner_fee.actual_fee_jpy if partner_fee else None,
        tolerance,
    )
    _compare_amount(
        diffs,
        "Partner Fee USD",
        validation_case.expected_partner_fee_usd,
        partner_fee.actual_fee_usd if partner_fee else None,
        0.01,
    )

    if validation_case.expected_decision:
        allowed = {item.strip() for item in validation_case.expected_decision.split("|")}
        if approval_result.decision not in allowed:
            diffs.append(f"decision 불일치 expected={validation_case.expected_decision}, actual={approval_result.decision}")
    return diffs


def _compare_amount(
    diffs: list[str],
    label: str,
    expected: float | None,
    actual: float | None,
    tolerance: float,
    major: bool = False,
) -> None:
    if expected is None:
        return
    actual_value = actual or 0
    diff = actual_value - expected
    if abs(diff) > tolerance:
        prefix = "MAJOR:" if major else ""
        diffs.append(f"{prefix}{label} 차이 {diff:+,.0f}")


def _to_case_read(row: models.ParserValidationCase) -> ParserValidationCaseRead:
    return ParserValidationCaseRead(**_case_dict(row), id=row.id, created_at=row.created_at)


def _case_dict(row: models.ParserValidationCase) -> dict:
    return {
        "case_name": row.case_name,
        "upload_id": row.upload_id,
        "original_filename": row.original_filename,
        "expected_customer_name": row.expected_customer_name,
        "expected_code": row.expected_code,
        "expected_gp_jpy": row.expected_gp_jpy,
        "expected_decision": row.expected_decision,
        "expected_transport_revenue_jpy": row.expected_transport_revenue_jpy,
        "expected_transport_expense_jpy": row.expected_transport_expense_jpy,
        "expected_customs_revenue_jpy": row.expected_customs_revenue_jpy,
        "expected_customs_duty_jpy": row.expected_customs_duty_jpy,
        "expected_consumption_tax_jpy": row.expected_consumption_tax_jpy,
        "expected_partner_fee_jpy": row.expected_partner_fee_jpy,
        "expected_partner_fee_usd": row.expected_partner_fee_usd,
        "tolerance_jpy": row.tolerance_jpy,
        "is_active": row.is_active,
    }


def _to_result_read(row: models.ParserValidationResult) -> ParserValidationResultRead:
    return ParserValidationResultRead(
        id=row.id,
        validation_case_id=row.validation_case_id,
        upload_id=row.upload_id,
        parsed_customer_name=row.parsed_customer_name,
        parsed_code=row.parsed_code,
        parsed_gp_jpy=row.parsed_gp_jpy,
        parsed_decision=row.parsed_decision,
        parsed_transport_revenue_jpy=row.parsed_transport_revenue_jpy,
        parsed_transport_expense_jpy=row.parsed_transport_expense_jpy,
        parsed_customs_revenue_jpy=row.parsed_customs_revenue_jpy,
        parsed_customs_duty_jpy=row.parsed_customs_duty_jpy,
        parsed_consumption_tax_jpy=row.parsed_consumption_tax_jpy,
        parsed_partner_fee_jpy=row.parsed_partner_fee_jpy,
        parsed_partner_fee_usd=row.parsed_partner_fee_usd,
        confidence=row.confidence,
        result=row.result,
        diff_summary=row.diff_summary,
        created_at=row.created_at,
    )


def _audit(
    db: Session,
    request: Request,
    action: str,
    entity_type: str,
    entity_id: int | str | None,
    detail: str | None,
) -> None:
    create_audit_log(
        db,
        user_name=request.headers.get("X-USER-NAME"),
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail,
        ip_address=request.client.host if request.client else None,
    )
