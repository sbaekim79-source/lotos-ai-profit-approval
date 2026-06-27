from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import models
from app.database import get_db
from app.routers.dashboard import (
    get_dashboard_summary,
    get_low_margin_cases,
    get_productivity_monthly,
)
from app.services.auth import actor_name, ensure_role, get_current_user
from app.services.audit_service import create_audit_log
from app.services.date_filter import resolve_date_range
from app.services.export_service import create_excel_file


router = APIRouter(prefix="/api/exports", tags=["Exports"])

EXCEL_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
EXPORT_ROLES = {"TEAM_MANAGER", "DIRECTOR", "CEO"}


def _today_stamp() -> str:
    return datetime.now().strftime("%Y%m%d")


def _filters_payload(**filters: Any) -> dict[str, Any]:
    return {key: value for key, value in filters.items() if value is not None and value != ""}


def _like(statement, column, value: str | None):
    if value:
        return statement.where(column.ilike(f"%{value}%"))
    return statement


def _authorized_user(request: Request, db: Session) -> models.User:
    user = get_current_user(request, db)
    ensure_role(user, EXPORT_ROLES)
    return user


def _record_export(
    *,
    db: Session,
    request: Request,
    user: models.User,
    export_type: str,
    path,
    detail: dict[str, Any],
) -> None:
    export_file = models.ExportFile(
        export_type=export_type,
        file_name=path.name,
        file_path=str(path),
        created_by=actor_name(user),
    )
    db.add(export_file)
    db.commit()
    create_audit_log(
        db,
        user_name=user.username,
        action="EXPORT_EXCEL",
        entity_type=export_type,
        entity_id=export_file.id,
        detail=json.dumps(detail, ensure_ascii=False),
        ip_address=request.client.host if request.client else None,
    )


def _file_response(path):
    return FileResponse(
        path,
        media_type=EXCEL_MEDIA_TYPE,
        filename=path.name,
    )


@router.get("/approvals.xlsx")
def export_approvals(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    work_month: str | None = None,
    pic: str | None = None,
    trade_type: str | None = None,
    code: str | None = None,
    decision: str | None = None,
    workflow_status: str | None = None,
    partner_name: str | None = None,
    customer_name: str | None = None,
    db: Session = Depends(get_db),
):
    user = _authorized_user(request, db)
    start_datetime, end_datetime, _ = resolve_date_range(start_date, end_date, work_month)

    statement = (
        select(models.ApprovalCase, models.ApprovalWorkflow.current_status)
        .outerjoin(models.ApprovalWorkflow)
        .where(
            models.ApprovalCase.created_at >= start_datetime,
            models.ApprovalCase.created_at <= end_datetime,
        )
        .order_by(models.ApprovalCase.created_at.desc())
    )
    if pic:
        statement = statement.where(models.ApprovalCase.pic == pic)
    if trade_type:
        statement = statement.where(models.ApprovalCase.trade_type == trade_type)
    if code:
        statement = statement.where(models.ApprovalCase.code == code)
    if decision:
        statement = statement.where(models.ApprovalCase.decision == decision)
    if workflow_status:
        statement = statement.where(models.ApprovalWorkflow.current_status == workflow_status)
    statement = _like(statement, models.ApprovalCase.partner_name, partner_name)
    statement = _like(statement, models.ApprovalCase.customer_name, customer_name)

    rows = [
        {
            "ID": approval.id,
            "고객명": approval.customer_name,
            "거래구분": approval.trade_type,
            "파트너": approval.partner_name,
            "실화주": approval.shipper_name,
            "담당자": approval.pic,
            "업무코드": approval.code,
            "Point": approval.point,
            "POL": approval.pol,
            "POD": approval.pod,
            "PORT": approval.port,
            "매출": approval.total_revenue_jpy,
            "원가": approval.total_expense_jpy,
            "GP": approval.gp_jpy,
            "GP율": approval.gp_rate,
            "실GP율": approval.net_gp_rate_ex_tax,
            "Minimum GP": approval.minimum_gp_jpy,
            "AI Decision": approval.decision,
            "Workflow Status": workflow_status_value,
            "생성일": approval.created_at,
        }
        for approval, workflow_status_value in db.execute(statement).all()
    ]

    filters = _filters_payload(
        start_date=start_date,
        end_date=end_date,
        work_month=work_month,
        pic=pic,
        trade_type=trade_type,
        code=code,
        decision=decision,
        workflow_status=workflow_status,
        partner_name=partner_name,
        customer_name=customer_name,
    )
    path = create_excel_file(f"approvals_{_today_stamp()}.xlsx", {"Approvals": rows})
    _record_export(
        db=db,
        request=request,
        user=user,
        export_type="APPROVALS",
        path=path,
        detail=filters,
    )
    return _file_response(path)


@router.get("/dashboard.xlsx")
def export_dashboard(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    work_month: str | None = None,
    db: Session = Depends(get_db),
):
    user = _authorized_user(request, db)
    summary = get_dashboard_summary(start_date, end_date, work_month, db=db)
    low_margin = get_low_margin_cases(start_date, end_date, work_month, db=db)

    sheets = {
        "Summary": [
            {
                "Period": summary.period_label,
                "Start Date": summary.start_date,
                "End Date": summary.end_date,
                "Total Cases": summary.total_cases,
                "Total Revenue JPY": summary.total_revenue_jpy,
                "Total Expense JPY": summary.total_expense_jpy,
                "Total GP JPY": summary.total_gp_jpy,
                "Average GP Rate": summary.average_gp_rate,
            }
        ],
        "Decision Counts": [
            {"Decision": key, "Count": value}
            for key, value in summary.decision_counts.model_dump().items()
        ],
        "Code Counts": [
            {"Code": key, "Count": value} for key, value in summary.code_counts.items()
        ],
        "Productivity": [
            row.model_dump() for row in summary.productivity_by_pic
        ],
        "Customer GP": [
            row.model_dump() for row in summary.gp_by_customer
        ],
        "Partner Summary": [
            row.model_dump() for row in summary.partner_summary
        ],
        "Low Margin": [
            row.model_dump() for row in low_margin
        ],
    }
    filters = _filters_payload(start_date=start_date, end_date=end_date, work_month=work_month)
    path = create_excel_file(f"dashboard_{_today_stamp()}.xlsx", sheets)
    _record_export(
        db=db,
        request=request,
        user=user,
        export_type="DASHBOARD",
        path=path,
        detail=filters,
    )
    return _file_response(path)


@router.get("/tariffs/transport.xlsx")
def export_transport_tariffs(
    request: Request,
    port: str | None = None,
    origin: str | None = None,
    destination: str | None = None,
    container_type: str | None = None,
    vendor_name: str | None = None,
    db: Session = Depends(get_db),
):
    user = _authorized_user(request, db)
    statement = select(models.TransportTariff).order_by(
        models.TransportTariff.created_at.desc()
    )
    statement = _like(statement, models.TransportTariff.port, port)
    statement = _like(statement, models.TransportTariff.origin, origin)
    statement = _like(statement, models.TransportTariff.destination, destination)
    statement = _like(statement, models.TransportTariff.container_type, container_type)
    statement = _like(statement, models.TransportTariff.vendor_name, vendor_name)

    rows = [
        {
            "ID": tariff.id,
            "PORT": tariff.port,
            "Origin": tariff.origin,
            "Destination": tariff.destination,
            "Distance KM": tariff.distance_km,
            "Container Type": tariff.container_type,
            "Container Count": tariff.container_count,
            "Vendor": tariff.vendor_name,
            "Transport Cost": tariff.transport_cost_jpy,
            "Highway Cost": tariff.highway_cost_jpy,
            "Transport Revenue": tariff.transport_revenue_jpy,
            "Transport GP": tariff.transport_gp_jpy,
            "Created At": tariff.created_at,
        }
        for tariff in db.execute(statement).scalars()
    ]
    filters = _filters_payload(
        port=port,
        origin=origin,
        destination=destination,
        container_type=container_type,
        vendor_name=vendor_name,
    )
    path = create_excel_file(
        f"transport_tariff_{_today_stamp()}.xlsx",
        {"Transport Tariff": rows},
    )
    _record_export(
        db=db,
        request=request,
        user=user,
        export_type="TARIFF_TRANSPORT",
        path=path,
        detail=filters,
    )
    return _file_response(path)


@router.get("/tariffs/customs.xlsx")
def export_customs_tariffs(
    request: Request,
    port: str | None = None,
    direction: str | None = None,
    self_customs: bool | None = None,
    vendor_name: str | None = None,
    db: Session = Depends(get_db),
):
    user = _authorized_user(request, db)
    statement = select(models.CustomsTariff).order_by(
        models.CustomsTariff.created_at.desc()
    )
    statement = _like(statement, models.CustomsTariff.port, port)
    statement = _like(statement, models.CustomsTariff.direction, direction)
    statement = _like(statement, models.CustomsTariff.vendor_name, vendor_name)
    if self_customs is not None:
        statement = statement.where(models.CustomsTariff.self_customs == self_customs)

    rows = [
        {
            "ID": tariff.id,
            "PORT": tariff.port,
            "Direction": tariff.direction,
            "Self Customs": tariff.self_customs,
            "Vendor": tariff.vendor_name,
            "Customs Revenue": tariff.customs_revenue_jpy,
            "Customs Expense": tariff.customs_expense_jpy,
            "Customs GP": tariff.customs_gp_jpy,
            "Food Declaration Fee": tariff.food_declaration_fee_jpy,
            "Inspection Fee": tariff.inspection_fee_jpy,
            "Created At": tariff.created_at,
        }
        for tariff in db.execute(statement).scalars()
    ]
    filters = _filters_payload(
        port=port,
        direction=direction,
        self_customs=self_customs,
        vendor_name=vendor_name,
    )
    path = create_excel_file(
        f"customs_tariff_{_today_stamp()}.xlsx",
        {"Customs Tariff": rows},
    )
    _record_export(
        db=db,
        request=request,
        user=user,
        export_type="TARIFF_CUSTOMS",
        path=path,
        detail=filters,
    )
    return _file_response(path)


@router.get("/quotes.xlsx")
def export_quotes(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    customer_name: str | None = None,
    partner_name: str | None = None,
    code: str | None = None,
    decision_hint: str | None = None,
    db: Session = Depends(get_db),
):
    user = _authorized_user(request, db)
    statement = (
        select(models.QuoteCase)
        .options(selectinload(models.QuoteCase.items))
        .order_by(models.QuoteCase.created_at.desc())
    )
    if start_date is not None or end_date is not None:
        start_datetime, end_datetime, _ = resolve_date_range(start_date, end_date, None)
        statement = statement.where(
            models.QuoteCase.created_at >= start_datetime,
            models.QuoteCase.created_at <= end_datetime,
        )
    statement = _like(statement, models.QuoteCase.customer_name, customer_name)
    statement = _like(statement, models.QuoteCase.partner_name, partner_name)
    if code:
        statement = statement.where(models.QuoteCase.code == code)
    if decision_hint:
        statement = statement.where(models.QuoteCase.decision_hint == decision_hint)

    quote_cases = list(db.execute(statement).scalars())
    quote_rows = [
        {
            "ID": quote.id,
            "Customer": quote.customer_name,
            "Trade Type": quote.trade_type,
            "Partner": quote.partner_name,
            "Mode": quote.mode,
            "Direction": quote.direction,
            "Code": quote.code,
            "Origin": quote.origin,
            "Destination": quote.destination,
            "Container Type": quote.container_type,
            "Container Count": quote.container_count,
            "Estimated Cost": quote.total_estimated_cost_jpy,
            "Recommended Revenue": quote.total_recommended_revenue_jpy,
            "Expected GP": quote.expected_gp_jpy,
            "Expected GP Rate": quote.expected_gp_rate,
            "Minimum GP": quote.minimum_gp_jpy,
            "Target GP Rate": quote.target_gp_rate,
            "Decision Hint": quote.decision_hint,
            "Created At": quote.created_at,
        }
        for quote in quote_cases
    ]
    item_rows = [
        {
            "Quote ID": quote.id,
            "Category": item.category,
            "Name": item.name,
            "Basis": item.basis,
            "Estimated Cost": item.estimated_cost_jpy,
            "Recommended Revenue": item.recommended_revenue_jpy,
            "GP": item.gp_jpy,
            "Source": item.source,
            "Note": item.note,
        }
        for quote in quote_cases
        for item in quote.items
    ]
    filters = _filters_payload(
        start_date=start_date,
        end_date=end_date,
        customer_name=customer_name,
        partner_name=partner_name,
        code=code,
        decision_hint=decision_hint,
    )
    path = create_excel_file(
        f"quotes_{_today_stamp()}.xlsx",
        {"Quotes": quote_rows, "Quote Items": item_rows},
    )
    _record_export(
        db=db,
        request=request,
        user=user,
        export_type="QUOTES",
        path=path,
        detail=filters,
    )
    return _file_response(path)


@router.get("/productivity.xlsx")
def export_productivity(
    request: Request,
    start_month: str | None = None,
    end_month: str | None = None,
    pic: str | None = None,
    db: Session = Depends(get_db),
):
    user = _authorized_user(request, db)
    productivity = get_productivity_monthly(start_month, end_month, pic, db)
    rows = [
        {
            "Work Month": item.work_month,
            "PIC": item.pic,
            "Total Point": item.total_point,
            "Case Count": item.case_count,
            "Grade": item.grade,
        }
        for item in productivity
    ]
    filters = _filters_payload(start_month=start_month, end_month=end_month, pic=pic)
    path = create_excel_file(
        f"productivity_{_today_stamp()}.xlsx",
        {"Productivity": rows},
    )
    _record_export(
        db=db,
        request=request,
        user=user,
        export_type="PRODUCTIVITY",
        path=path,
        detail=filters,
    )
    return _file_response(path)
