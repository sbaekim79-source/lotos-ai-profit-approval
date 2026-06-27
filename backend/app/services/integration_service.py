from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import models


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def build_approval_payload(db: Session, approval_case_id: int) -> dict[str, Any]:
    approval_case = db.execute(
        select(models.ApprovalCase)
        .options(
            selectinload(models.ApprovalCase.findings),
            selectinload(models.ApprovalCase.workflow),
        )
        .where(models.ApprovalCase.id == approval_case_id)
    ).scalar_one_or_none()
    if approval_case is None:
        raise HTTPException(status_code=404, detail="Approval case not found")

    return {
        "approval_case_id": approval_case.id,
        "case_no": approval_case.case_no,
        "customer_name": approval_case.customer_name,
        "trade_type": approval_case.trade_type,
        "partner_name": approval_case.partner_name,
        "shipper_name": approval_case.shipper_name,
        "pic": approval_case.pic,
        "code": approval_case.code,
        "point": approval_case.point,
        "revenue": approval_case.total_revenue_jpy,
        "expense": approval_case.total_expense_jpy,
        "gp": approval_case.gp_jpy,
        "gp_rate": approval_case.gp_rate,
        "decision": approval_case.decision,
        "workflow_status": (
            approval_case.workflow.current_status if approval_case.workflow else None
        ),
        "created_at": _serialize(approval_case.created_at),
        "findings": [
            {
                "category": finding.category,
                "status": finding.status,
                "message": finding.message,
                "amount_jpy": finding.amount_jpy,
            }
            for finding in approval_case.findings
        ],
    }


def build_quote_payload(db: Session, quote_case_id: int) -> dict[str, Any]:
    quote_case = db.execute(
        select(models.QuoteCase)
        .options(selectinload(models.QuoteCase.items))
        .where(models.QuoteCase.id == quote_case_id)
    ).scalar_one_or_none()
    if quote_case is None:
        raise HTTPException(status_code=404, detail="Quote case not found")

    return {
        "quote_case_id": quote_case.id,
        "customer_name": quote_case.customer_name,
        "trade_type": quote_case.trade_type,
        "partner_name": quote_case.partner_name,
        "mode": quote_case.mode,
        "direction": quote_case.direction,
        "code": quote_case.code,
        "pol": quote_case.pol,
        "pod": quote_case.pod,
        "port": quote_case.port,
        "origin": quote_case.origin,
        "destination": quote_case.destination,
        "container_type": quote_case.container_type,
        "container_count": quote_case.container_count,
        "total_estimated_cost_jpy": quote_case.total_estimated_cost_jpy,
        "total_recommended_revenue_jpy": quote_case.total_recommended_revenue_jpy,
        "expected_gp_jpy": quote_case.expected_gp_jpy,
        "expected_gp_rate": quote_case.expected_gp_rate,
        "minimum_gp_jpy": quote_case.minimum_gp_jpy,
        "target_gp_rate": quote_case.target_gp_rate,
        "decision_hint": quote_case.decision_hint,
        "executive_summary": quote_case.executive_summary,
        "created_at": _serialize(quote_case.created_at),
        "items": [
            {
                "category": item.category,
                "name": item.name,
                "basis": item.basis,
                "estimated_cost_jpy": item.estimated_cost_jpy,
                "recommended_revenue_jpy": item.recommended_revenue_jpy,
                "gp_jpy": item.gp_jpy,
                "source": item.source,
                "note": item.note,
            }
            for item in quote_case.items
        ],
    }


def build_tariff_payload(
    db: Session,
    tariff_type: str,
    tariff_id: int,
) -> dict[str, Any]:
    normalized_type = tariff_type.upper()
    if normalized_type == "TRANSPORT":
        tariff = db.get(models.TransportTariff, tariff_id)
        if tariff is None:
            raise HTTPException(status_code=404, detail="Transport tariff not found")
        return {
            "tariff_type": "TRANSPORT",
            "tariff_id": tariff.id,
            "approval_case_id": tariff.approval_case_id,
            "port": tariff.port,
            "origin": tariff.origin,
            "destination": tariff.destination,
            "distance_km": tariff.distance_km,
            "container_type": tariff.container_type,
            "container_count": tariff.container_count,
            "vendor_name": tariff.vendor_name,
            "transport_cost_jpy": tariff.transport_cost_jpy,
            "highway_cost_jpy": tariff.highway_cost_jpy,
            "transport_revenue_jpy": tariff.transport_revenue_jpy,
            "transport_gp_jpy": tariff.transport_gp_jpy,
            "created_at": _serialize(tariff.created_at),
        }

    if normalized_type == "CUSTOMS":
        tariff = db.get(models.CustomsTariff, tariff_id)
        if tariff is None:
            raise HTTPException(status_code=404, detail="Customs tariff not found")
        return {
            "tariff_type": "CUSTOMS",
            "tariff_id": tariff.id,
            "approval_case_id": tariff.approval_case_id,
            "port": tariff.port,
            "direction": tariff.direction,
            "self_customs": tariff.self_customs,
            "vendor_name": tariff.vendor_name,
            "customs_revenue_jpy": tariff.customs_revenue_jpy,
            "customs_expense_jpy": tariff.customs_expense_jpy,
            "customs_gp_jpy": tariff.customs_gp_jpy,
            "food_declaration_fee_jpy": tariff.food_declaration_fee_jpy,
            "inspection_fee_jpy": tariff.inspection_fee_jpy,
            "created_at": _serialize(tariff.created_at),
        }

    raise HTTPException(status_code=400, detail="Unsupported tariff type")
