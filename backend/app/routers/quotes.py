from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import models
from app.database import get_db
from app.schemas import (
    QuoteCostItem,
    QuoteDetail,
    QuoteListItem,
    QuoteRequest,
    QuoteResult,
    QuoteSaveResponse,
)
from app.services.quote_engine import generate_quote
from app.services.audit_service import create_audit_log


router = APIRouter(prefix="/api/quotes", tags=["Quotes"])


@router.post("/generate", response_model=QuoteResult)
def generate_quote_api(
    request: QuoteRequest,
    db: Session = Depends(get_db),
) -> QuoteResult:
    return generate_quote(request, db)


@router.post("/generate-and-save", response_model=QuoteSaveResponse)
def generate_and_save_quote(
    request: QuoteRequest,
    http_request: Request,
    db: Session = Depends(get_db),
) -> QuoteSaveResponse:
    result = generate_quote(request, db)
    quote_case = _save_quote(db, request, result)
    create_audit_log(
        db,
        user_name=http_request.headers.get("X-USER-NAME"),
        action="SAVE_QUOTE",
        entity_type="QUOTE_CASE",
        entity_id=quote_case.id,
        detail=quote_case.customer_name,
        ip_address=http_request.client.host if http_request.client else None,
    )
    return QuoteSaveResponse(quote_case_id=quote_case.id, result=result)


@router.get("", response_model=list[QuoteListItem])
def list_quotes(db: Session = Depends(get_db)) -> list[QuoteListItem]:
    quote_cases = db.execute(
        select(models.QuoteCase)
        .order_by(models.QuoteCase.created_at.desc())
        .limit(100)
    ).scalars()
    return [_to_quote_list_item(quote_case) for quote_case in quote_cases]


@router.get("/{quote_case_id}", response_model=QuoteDetail)
def get_quote_detail(
    quote_case_id: int,
    db: Session = Depends(get_db),
) -> QuoteDetail:
    quote_case = db.execute(
        select(models.QuoteCase)
        .options(selectinload(models.QuoteCase.items))
        .where(models.QuoteCase.id == quote_case_id)
    ).scalar_one_or_none()
    if quote_case is None:
        raise HTTPException(status_code=404, detail="Quote case not found")
    return _to_quote_detail(quote_case)


def _save_quote(
    db: Session,
    request: QuoteRequest,
    result: QuoteResult,
) -> models.QuoteCase:
    quote_case = models.QuoteCase(
        customer_name=request.customer_name,
        trade_type=request.trade_type,
        partner_name=request.partner_name,
        mode=request.mode,
        direction=request.direction,
        code=request.code,
        pol=request.pol,
        pod=request.pod,
        port=request.port,
        origin=request.origin,
        destination=request.destination,
        container_type=request.container_type,
        container_count=request.container_count,
        total_estimated_cost_jpy=result.total_estimated_cost_jpy,
        total_recommended_revenue_jpy=result.total_recommended_revenue_jpy,
        expected_gp_jpy=result.expected_gp_jpy,
        expected_gp_rate=result.expected_gp_rate,
        minimum_gp_jpy=result.minimum_gp_jpy,
        target_gp_rate=result.target_gp_rate,
        decision_hint=result.decision_hint,
        executive_summary=result.executive_summary,
    )
    db.add(quote_case)
    db.flush()

    for item in result.items:
        db.add(
            models.QuoteItem(
                quote_case_id=quote_case.id,
                category=item.category,
                name=item.name,
                basis=item.basis,
                estimated_cost_jpy=item.estimated_cost_jpy,
                recommended_revenue_jpy=item.recommended_revenue_jpy,
                gp_jpy=item.gp_jpy,
                source=item.source,
                note=item.note,
            )
        )

    db.commit()
    db.refresh(quote_case)
    return quote_case


def _to_quote_list_item(quote_case: models.QuoteCase) -> QuoteListItem:
    return QuoteListItem(
        id=quote_case.id,
        customer_name=quote_case.customer_name,
        trade_type=quote_case.trade_type,
        partner_name=quote_case.partner_name,
        mode=quote_case.mode,
        direction=quote_case.direction,
        code=quote_case.code,
        origin=quote_case.origin,
        destination=quote_case.destination,
        container_type=quote_case.container_type,
        total_estimated_cost_jpy=quote_case.total_estimated_cost_jpy,
        total_recommended_revenue_jpy=quote_case.total_recommended_revenue_jpy,
        expected_gp_jpy=quote_case.expected_gp_jpy,
        expected_gp_rate=quote_case.expected_gp_rate,
        minimum_gp_jpy=quote_case.minimum_gp_jpy,
        target_gp_rate=quote_case.target_gp_rate,
        decision_hint=quote_case.decision_hint,
        created_at=quote_case.created_at,
    )


def _to_quote_detail(quote_case: models.QuoteCase) -> QuoteDetail:
    base = _to_quote_list_item(quote_case).model_dump()
    return QuoteDetail(
        **base,
        pol=quote_case.pol,
        pod=quote_case.pod,
        port=quote_case.port,
        container_count=quote_case.container_count,
        executive_summary=quote_case.executive_summary,
        items=[
            QuoteCostItem(
                category=item.category,
                name=item.name,
                basis=item.basis,
                estimated_cost_jpy=item.estimated_cost_jpy,
                recommended_revenue_jpy=item.recommended_revenue_jpy,
                gp_jpy=item.gp_jpy,
                source=item.source,
                note=item.note,
            )
            for item in quote_case.items
        ],
    )
