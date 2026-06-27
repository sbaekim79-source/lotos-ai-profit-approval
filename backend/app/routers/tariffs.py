from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import (
    CustomsTariffItem,
    CustomsTariffSummary,
    TransportTariffItem,
    TransportTariffSummary,
)


router = APIRouter(prefix="/api/tariffs", tags=["Tariffs"])


def _ilike_filter(statement, column, value: str | None):
    if value is None:
        return statement
    return statement.where(column.ilike(f"%{value}%"))


def _to_transport_item(tariff: models.TransportTariff) -> TransportTariffItem:
    return TransportTariffItem(
        id=tariff.id,
        approval_case_id=tariff.approval_case_id,
        port=tariff.port,
        origin=tariff.origin,
        destination=tariff.destination,
        distance_km=tariff.distance_km,
        container_type=tariff.container_type,
        container_count=tariff.container_count,
        vendor_name=tariff.vendor_name,
        transport_cost_jpy=tariff.transport_cost_jpy,
        highway_cost_jpy=tariff.highway_cost_jpy,
        transport_revenue_jpy=tariff.transport_revenue_jpy,
        transport_gp_jpy=tariff.transport_gp_jpy,
        created_at=tariff.created_at,
    )


def _to_customs_item(tariff: models.CustomsTariff) -> CustomsTariffItem:
    return CustomsTariffItem(
        id=tariff.id,
        approval_case_id=tariff.approval_case_id,
        port=tariff.port,
        direction=tariff.direction,
        self_customs=tariff.self_customs,
        vendor_name=tariff.vendor_name,
        customs_revenue_jpy=tariff.customs_revenue_jpy,
        customs_expense_jpy=tariff.customs_expense_jpy,
        customs_gp_jpy=tariff.customs_gp_jpy,
        food_declaration_fee_jpy=tariff.food_declaration_fee_jpy,
        inspection_fee_jpy=tariff.inspection_fee_jpy,
        created_at=tariff.created_at,
    )


@router.get("/transport", response_model=list[TransportTariffItem])
def list_transport_tariffs(
    port: str | None = None,
    origin: str | None = None,
    destination: str | None = None,
    container_type: str | None = None,
    vendor_name: str | None = None,
    db: Session = Depends(get_db),
) -> list[TransportTariffItem]:
    statement = select(models.TransportTariff).order_by(
        models.TransportTariff.created_at.desc()
    )
    statement = _ilike_filter(statement, models.TransportTariff.port, port)
    statement = _ilike_filter(statement, models.TransportTariff.origin, origin)
    statement = _ilike_filter(
        statement, models.TransportTariff.destination, destination
    )
    statement = _ilike_filter(
        statement, models.TransportTariff.container_type, container_type
    )
    statement = _ilike_filter(statement, models.TransportTariff.vendor_name, vendor_name)
    return [_to_transport_item(tariff) for tariff in db.execute(statement).scalars()]


@router.get("/transport/summary", response_model=list[TransportTariffSummary])
def summarize_transport_tariffs(
    db: Session = Depends(get_db),
) -> list[TransportTariffSummary]:
    rows = db.execute(
        select(
            models.TransportTariff.origin,
            models.TransportTariff.destination,
            models.TransportTariff.container_type,
            func.count(models.TransportTariff.id),
            func.avg(models.TransportTariff.transport_cost_jpy),
            func.min(models.TransportTariff.transport_cost_jpy),
            func.max(models.TransportTariff.transport_cost_jpy),
            func.avg(models.TransportTariff.transport_revenue_jpy),
            func.avg(models.TransportTariff.transport_gp_jpy),
        )
        .group_by(
            models.TransportTariff.origin,
            models.TransportTariff.destination,
            models.TransportTariff.container_type,
        )
        .order_by(desc(func.count(models.TransportTariff.id)))
    ).all()

    return [
        TransportTariffSummary(
            origin=origin,
            destination=destination,
            container_type=container_type,
            case_count=case_count,
            avg_transport_cost_jpy=avg_cost or 0,
            min_transport_cost_jpy=min_cost or 0,
            max_transport_cost_jpy=max_cost or 0,
            avg_transport_revenue_jpy=avg_revenue or 0,
            avg_transport_gp_jpy=avg_gp or 0,
        )
        for (
            origin,
            destination,
            container_type,
            case_count,
            avg_cost,
            min_cost,
            max_cost,
            avg_revenue,
            avg_gp,
        ) in rows
    ]


@router.get("/customs", response_model=list[CustomsTariffItem])
def list_customs_tariffs(
    port: str | None = None,
    direction: str | None = None,
    self_customs: bool | None = None,
    vendor_name: str | None = None,
    db: Session = Depends(get_db),
) -> list[CustomsTariffItem]:
    statement = select(models.CustomsTariff).order_by(
        models.CustomsTariff.created_at.desc()
    )
    statement = _ilike_filter(statement, models.CustomsTariff.port, port)
    statement = _ilike_filter(statement, models.CustomsTariff.direction, direction)
    statement = _ilike_filter(statement, models.CustomsTariff.vendor_name, vendor_name)
    if self_customs is not None:
        statement = statement.where(models.CustomsTariff.self_customs == self_customs)
    return [_to_customs_item(tariff) for tariff in db.execute(statement).scalars()]


@router.get("/customs/summary", response_model=list[CustomsTariffSummary])
def summarize_customs_tariffs(
    db: Session = Depends(get_db),
) -> list[CustomsTariffSummary]:
    rows = db.execute(
        select(
            models.CustomsTariff.port,
            models.CustomsTariff.direction,
            models.CustomsTariff.self_customs,
            func.count(models.CustomsTariff.id),
            func.avg(models.CustomsTariff.customs_revenue_jpy),
            func.avg(models.CustomsTariff.customs_expense_jpy),
            func.avg(models.CustomsTariff.customs_gp_jpy),
            func.avg(models.CustomsTariff.food_declaration_fee_jpy),
            func.avg(models.CustomsTariff.inspection_fee_jpy),
        )
        .group_by(
            models.CustomsTariff.port,
            models.CustomsTariff.direction,
            models.CustomsTariff.self_customs,
        )
        .order_by(desc(func.count(models.CustomsTariff.id)))
    ).all()

    return [
        CustomsTariffSummary(
            port=port,
            direction=direction,
            self_customs=self_customs,
            case_count=case_count,
            avg_customs_revenue_jpy=avg_revenue or 0,
            avg_customs_expense_jpy=avg_expense or 0,
            avg_customs_gp_jpy=avg_gp or 0,
            avg_food_declaration_fee_jpy=avg_food_fee or 0,
            avg_inspection_fee_jpy=avg_inspection_fee or 0,
        )
        for (
            port,
            direction,
            self_customs,
            case_count,
            avg_revenue,
            avg_expense,
            avg_gp,
            avg_food_fee,
            avg_inspection_fee,
        ) in rows
    ]


@router.get("/warehouse")
def warehouse_tariff_placeholder() -> dict[str, str]:
    return {"message": "warehouse tariff API will be implemented in next step"}
