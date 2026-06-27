from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import ParserImprovementSuggestionRead
from app.services.audit_service import create_audit_log


router = APIRouter(prefix="/api/parser-improvements", tags=["Parser Improvements"])


@router.get("/suggestions", response_model=list[ParserImprovementSuggestionRead])
def list_suggestions(
    status: str | None = None,
    issue_type: str | None = None,
    case_name: str | None = None,
    db: Session = Depends(get_db),
) -> list[ParserImprovementSuggestionRead]:
    statement = select(models.ParserImprovementSuggestion).order_by(
        models.ParserImprovementSuggestion.created_at.desc()
    )
    if status:
        statement = statement.where(models.ParserImprovementSuggestion.status == status)
    if issue_type:
        statement = statement.where(models.ParserImprovementSuggestion.issue_type == issue_type)
    if case_name:
        statement = statement.where(models.ParserImprovementSuggestion.case_name.contains(case_name))
    rows = db.execute(statement.limit(500)).scalars()
    return [_to_read(row) for row in rows]


@router.post(
    "/suggestions/{suggestion_id}/apply",
    response_model=ParserImprovementSuggestionRead,
)
def apply_suggestion(
    suggestion_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> ParserImprovementSuggestionRead:
    suggestion = db.get(models.ParserImprovementSuggestion, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Parser improvement suggestion not found")
    if suggestion.status != "OPEN":
        raise HTTPException(status_code=400, detail="Only OPEN suggestions can be applied")
    if not suggestion.template_id:
        raise HTTPException(status_code=400, detail="Suggestion has no target parser template")
    if not suggestion.suggested_keyword:
        raise HTTPException(status_code=400, detail="Suggestion has no keyword to apply")

    template = db.get(models.ParserTemplate, suggestion.template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Parser template not found")

    field_name = _target_keyword_field(suggestion)
    if field_name is None:
        raise HTTPException(status_code=400, detail="Suggestion cannot be applied automatically")

    before_value = getattr(template, field_name) or ""
    after_value = _append_keywords(before_value, suggestion.suggested_keyword)
    setattr(template, field_name, after_value)
    suggestion.status = "APPLIED"
    suggestion.applied_at = models.utc_now()
    db.commit()
    db.refresh(suggestion)

    create_audit_log(
        db,
        user_name=request.headers.get("X-USER-NAME"),
        action="APPLY_PARSER_IMPROVEMENT",
        entity_type="PARSER_TEMPLATE",
        entity_id=template.id,
        detail=(
            f"suggestion_id={suggestion.id}, field={field_name}, "
            f"added={suggestion.suggested_keyword}"
        ),
        ip_address=request.client.host if request.client else None,
    )
    return _to_read(suggestion)


@router.post(
    "/suggestions/{suggestion_id}/reject",
    response_model=ParserImprovementSuggestionRead,
)
def reject_suggestion(
    suggestion_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> ParserImprovementSuggestionRead:
    suggestion = db.get(models.ParserImprovementSuggestion, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Parser improvement suggestion not found")
    if suggestion.status != "OPEN":
        raise HTTPException(status_code=400, detail="Only OPEN suggestions can be rejected")
    suggestion.status = "REJECTED"
    db.commit()
    db.refresh(suggestion)
    create_audit_log(
        db,
        user_name=request.headers.get("X-USER-NAME"),
        action="REJECT_PARSER_IMPROVEMENT",
        entity_type="PARSER_IMPROVEMENT_SUGGESTION",
        entity_id=suggestion.id,
        detail=suggestion.suggestion_text,
        ip_address=request.client.host if request.client else None,
    )
    return _to_read(suggestion)


def _target_keyword_field(suggestion: models.ParserImprovementSuggestion) -> str | None:
    if suggestion.issue_type == "TRANSPORT_MISMATCH":
        return "transport_keywords"
    if suggestion.issue_type == "CUSTOMS_MISMATCH":
        return "customs_keywords"
    if suggestion.issue_type == "PARTNER_FEE_MISMATCH":
        return "partner_fee_keywords"
    if suggestion.issue_type == "TAX_MISMATCH":
        if "consumption" in suggestion.field_name.lower():
            return "consumption_tax_keywords"
        return "duty_keywords"
    if suggestion.issue_type == "MISSING_KEYWORD":
        field = suggestion.field_name.lower()
        if "transport" in field:
            return "transport_keywords"
        if "customs" in field:
            return "customs_keywords"
        if "partner" in field:
            return "partner_fee_keywords"
        if "consumption" in field or "vat" in field:
            return "consumption_tax_keywords"
        if "duty" in field:
            return "duty_keywords"
    return None


def _append_keywords(current_value: str, suggested_keyword: str) -> str:
    existing = [item.strip() for item in current_value.split(",") if item.strip()]
    existing_upper = {item.upper() for item in existing}
    for keyword in suggested_keyword.split(","):
        clean_keyword = keyword.strip()
        if clean_keyword and clean_keyword.upper() not in existing_upper:
            existing.append(clean_keyword)
            existing_upper.add(clean_keyword.upper())
    return ",".join(existing)


def _to_read(row: models.ParserImprovementSuggestion) -> ParserImprovementSuggestionRead:
    return ParserImprovementSuggestionRead(
        id=row.id,
        validation_result_id=row.validation_result_id,
        template_id=row.template_id,
        case_name=row.case_name,
        issue_type=row.issue_type,
        field_name=row.field_name,
        current_value=row.current_value,
        expected_value=row.expected_value,
        suggested_keyword=row.suggested_keyword,
        suggestion_text=row.suggestion_text,
        status=row.status,
        created_at=row.created_at,
        applied_at=row.applied_at,
    )
