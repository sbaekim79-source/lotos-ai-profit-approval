from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import (
    DashboardSummary,
    DecisionCounts,
    GpByCustomer,
    LowMarginItem,
    MonthlyPerformanceItem,
    PartnerSummary,
    ProductivityByPic,
    ProductivityMonthlyItem,
)
from app.services.approval_engine import GP_RATE_RULES
from app.services.date_filter import resolve_date_range


router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

DEFAULT_CODE_COUNTS = {
    "SE": 0,
    "SE+": 0,
    "SE++": 0,
    "SI": 0,
    "SI+": 0,
    "SI++": 0,
}


def _average_gp_rate(total_gp_jpy: float, total_revenue_jpy: float) -> float:
    if total_revenue_jpy == 0:
        return 0
    return total_gp_jpy / total_revenue_jpy


def _grade(total_point: float) -> str:
    if total_point >= 120:
        return "우수"
    if total_point >= 80:
        return "정상"
    if total_point >= 60:
        return "관리"
    return "개선"


def _case_filters(
    *,
    start_datetime: datetime,
    end_datetime: datetime,
    pic: str | None = None,
    trade_type: str | None = None,
    code: str | None = None,
    partner_name: str | None = None,
    customer_name: str | None = None,
) -> list[object]:
    filters: list[object] = [
        models.ApprovalCase.created_at >= start_datetime,
        models.ApprovalCase.created_at <= end_datetime,
    ]
    if pic:
        filters.append(models.ApprovalCase.pic == pic)
    if trade_type:
        filters.append(models.ApprovalCase.trade_type == trade_type)
    if code:
        filters.append(models.ApprovalCase.code == code)
    if partner_name:
        filters.append(models.ApprovalCase.partner_name.ilike(f"%{partner_name}%"))
    if customer_name:
        filters.append(models.ApprovalCase.customer_name.ilike(f"%{customer_name}%"))
    return filters


def _productivity_filters(
    *,
    start_datetime: datetime,
    end_datetime: datetime,
    pic: str | None = None,
) -> list[object]:
    filters: list[object] = [
        models.ProductivityPoint.created_at >= start_datetime,
        models.ProductivityPoint.created_at <= end_datetime,
    ]
    if pic:
        filters.append(models.ProductivityPoint.pic == pic)
    return filters


def _month_filters(
    month_expression: object,
    start_month: str | None,
    end_month: str | None,
) -> list[object]:
    filters: list[object] = []
    if start_month is not None:
        filters.append(month_expression >= start_month)
    if end_month is not None:
        filters.append(month_expression <= end_month)
    return filters


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    start_date: str | None = None,
    end_date: str | None = None,
    work_month: str | None = None,
    pic: str | None = None,
    trade_type: str | None = None,
    code: str | None = None,
    partner_name: str | None = None,
    customer_name: str | None = None,
    db: Session = Depends(get_db),
) -> DashboardSummary:
    start_datetime, end_datetime, period_label = resolve_date_range(
        start_date=start_date,
        end_date=end_date,
        work_month=work_month,
    )
    filters = _case_filters(
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        pic=pic,
        trade_type=trade_type,
        code=code,
        partner_name=partner_name,
        customer_name=customer_name,
    )

    total_cases = db.scalar(select(func.count(models.ApprovalCase.id)).where(*filters)) or 0
    total_revenue_jpy = db.scalar(
        select(func.coalesce(func.sum(models.ApprovalCase.total_revenue_jpy), 0)).where(*filters)
    ) or 0
    total_expense_jpy = db.scalar(
        select(func.coalesce(func.sum(models.ApprovalCase.total_expense_jpy), 0)).where(*filters)
    ) or 0
    total_gp_jpy = db.scalar(
        select(func.coalesce(func.sum(models.ApprovalCase.gp_jpy), 0)).where(*filters)
    ) or 0

    decision_count_data = dict(
        db.execute(
            select(models.ApprovalCase.decision, func.count(models.ApprovalCase.id))
            .where(*filters)
            .group_by(models.ApprovalCase.decision)
        ).all()
    )
    code_counts = DEFAULT_CODE_COUNTS | dict(
        db.execute(
            select(models.ApprovalCase.code, func.count(models.ApprovalCase.id))
            .where(*filters)
            .group_by(models.ApprovalCase.code)
        ).all()
    )

    productivity_by_pic = [
        ProductivityByPic(pic=row_pic, total_point=total_point or 0, case_count=case_count)
        for row_pic, total_point, case_count in db.execute(
            select(
                models.ProductivityPoint.pic,
                func.coalesce(func.sum(models.ProductivityPoint.point), 0),
                func.count(models.ProductivityPoint.id),
            )
            .where(*_productivity_filters(start_datetime=start_datetime, end_datetime=end_datetime, pic=pic))
            .group_by(models.ProductivityPoint.pic)
            .order_by(desc(func.coalesce(func.sum(models.ProductivityPoint.point), 0)))
        ).all()
    ]

    gp_by_customer = [
        GpByCustomer(
            customer_name=name,
            case_count=case_count,
            total_revenue_jpy=total_revenue or 0,
            total_gp_jpy=total_gp or 0,
            average_gp_rate=_average_gp_rate(total_gp or 0, total_revenue or 0),
        )
        for name, case_count, total_revenue, total_gp in db.execute(
            select(
                models.ApprovalCase.customer_name,
                func.count(models.ApprovalCase.id),
                func.coalesce(func.sum(models.ApprovalCase.total_revenue_jpy), 0),
                func.coalesce(func.sum(models.ApprovalCase.gp_jpy), 0),
            )
            .where(*filters)
            .group_by(models.ApprovalCase.customer_name)
            .order_by(desc(func.coalesce(func.sum(models.ApprovalCase.gp_jpy), 0)))
            .limit(20)
        ).all()
    ]

    partner_summary = [
        PartnerSummary(
            partner_name=name,
            case_count=case_count,
            total_revenue_jpy=total_revenue or 0,
            total_gp_jpy=total_gp or 0,
            average_gp_rate=_average_gp_rate(total_gp or 0, total_revenue or 0),
        )
        for name, case_count, total_revenue, total_gp in db.execute(
            select(
                models.ApprovalCase.partner_name,
                func.count(models.ApprovalCase.id),
                func.coalesce(func.sum(models.ApprovalCase.total_revenue_jpy), 0),
                func.coalesce(func.sum(models.ApprovalCase.gp_jpy), 0),
            )
            .where(*filters, models.ApprovalCase.partner_name.is_not(None))
            .group_by(models.ApprovalCase.partner_name)
            .order_by(desc(func.coalesce(func.sum(models.ApprovalCase.gp_jpy), 0)))
            .limit(20)
        ).all()
    ]

    active_filters = {
        "work_month": work_month,
        "pic": pic,
        "trade_type": trade_type,
        "code": code,
        "partner_name": partner_name,
        "customer_name": customer_name,
    }

    return DashboardSummary(
        period_label=period_label,
        start_date=start_datetime.date(),
        end_date=end_datetime.date(),
        filters={key: value for key, value in active_filters.items() if value},
        period_start=start_datetime.date(),
        period_end=end_datetime.date(),
        total_cases=total_cases,
        total_revenue_jpy=total_revenue_jpy,
        total_expense_jpy=total_expense_jpy,
        total_gp_jpy=total_gp_jpy,
        average_gp_rate=_average_gp_rate(total_gp_jpy, total_revenue_jpy),
        decision_counts=DecisionCounts(
            APPROVED=decision_count_data.get("APPROVED", 0),
            CONDITIONAL_APPROVED=decision_count_data.get("CONDITIONAL_APPROVED", 0),
            CEO_REVIEW=decision_count_data.get("CEO_REVIEW", 0),
            REJECTED=decision_count_data.get("REJECTED", 0),
        ),
        code_counts=code_counts,
        productivity_by_pic=productivity_by_pic,
        gp_by_customer=gp_by_customer,
        partner_summary=partner_summary,
    )


def _monthly_statement(
    *,
    start_month: str | None,
    end_month: str | None,
    pic: str | None,
    trade_type: str | None,
    code: str | None,
):
    work_month = func.to_char(models.ApprovalCase.created_at, "YYYY-MM")
    statement = select(
        work_month.label("work_month"),
        func.count(models.ApprovalCase.id),
        func.coalesce(func.sum(models.ApprovalCase.total_revenue_jpy), 0),
        func.coalesce(func.sum(models.ApprovalCase.total_expense_jpy), 0),
        func.coalesce(func.sum(models.ApprovalCase.gp_jpy), 0),
        func.sum(case((models.ApprovalCase.decision == "APPROVED", 1), else_=0)),
        func.sum(case((models.ApprovalCase.decision == "CONDITIONAL_APPROVED", 1), else_=0)),
        func.sum(case((models.ApprovalCase.decision == "CEO_REVIEW", 1), else_=0)),
        func.sum(case((models.ApprovalCase.decision == "REJECTED", 1), else_=0)),
    ).where(*_month_filters(work_month, start_month, end_month))
    if pic:
        statement = statement.where(models.ApprovalCase.pic == pic)
    if trade_type:
        statement = statement.where(models.ApprovalCase.trade_type == trade_type)
    if code:
        statement = statement.where(models.ApprovalCase.code == code)
    return statement.group_by(work_month).order_by(work_month.asc())


@router.get("/monthly-performance", response_model=list[MonthlyPerformanceItem])
def get_monthly_performance(
    start_month: str | None = None,
    end_month: str | None = None,
    pic: str | None = None,
    trade_type: str | None = None,
    code: str | None = None,
    db: Session = Depends(get_db),
) -> list[MonthlyPerformanceItem]:
    return [
        MonthlyPerformanceItem(
            work_month=month,
            case_count=case_count,
            total_cases=case_count,
            total_revenue_jpy=total_revenue or 0,
            total_expense_jpy=total_expense or 0,
            total_gp_jpy=total_gp or 0,
            average_gp_rate=_average_gp_rate(total_gp or 0, total_revenue or 0),
            approved_count=approved_count or 0,
            conditional_count=conditional_count or 0,
            conditional_approved_count=conditional_count or 0,
            ceo_review_count=ceo_review_count or 0,
            rejected_count=rejected_count or 0,
        )
        for (
            month,
            case_count,
            total_revenue,
            total_expense,
            total_gp,
            approved_count,
            conditional_count,
            ceo_review_count,
            rejected_count,
        ) in db.execute(
            _monthly_statement(
                start_month=start_month,
                end_month=end_month,
                pic=pic,
                trade_type=trade_type,
                code=code,
            )
        ).all()
    ]


@router.get("/monthly", response_model=list[MonthlyPerformanceItem])
def get_monthly_performance_legacy(
    start_month: str | None = None,
    end_month: str | None = None,
    pic: str | None = None,
    trade_type: str | None = None,
    code: str | None = None,
    db: Session = Depends(get_db),
) -> list[MonthlyPerformanceItem]:
    return get_monthly_performance(start_month, end_month, pic, trade_type, code, db)


@router.get("/productivity/monthly", response_model=list[ProductivityMonthlyItem])
def get_productivity_monthly(
    start_month: str | None = None,
    end_month: str | None = None,
    pic: str | None = None,
    db: Session = Depends(get_db),
) -> list[ProductivityMonthlyItem]:
    statement = select(
        models.ProductivityPoint.work_month,
        models.ProductivityPoint.pic,
        func.coalesce(func.sum(models.ProductivityPoint.point), 0),
        func.count(models.ProductivityPoint.id),
    )
    if start_month:
        statement = statement.where(models.ProductivityPoint.work_month >= start_month)
    if end_month:
        statement = statement.where(models.ProductivityPoint.work_month <= end_month)
    if pic:
        statement = statement.where(models.ProductivityPoint.pic == pic)
    statement = statement.group_by(
        models.ProductivityPoint.work_month,
        models.ProductivityPoint.pic,
    ).order_by(models.ProductivityPoint.work_month.asc(), models.ProductivityPoint.pic.asc())

    return [
        ProductivityMonthlyItem(
            work_month=month,
            pic=row_pic,
            total_point=total_point or 0,
            case_count=case_count,
            grade=_grade(total_point or 0),
        )
        for month, row_pic, total_point, case_count in db.execute(statement).all()
    ]


@router.get("/productivity", response_model=list[ProductivityMonthlyItem])
def get_productivity(
    work_month: str | None = None,
    start_month: str | None = None,
    end_month: str | None = None,
    pic: str | None = None,
    db: Session = Depends(get_db),
) -> list[ProductivityMonthlyItem]:
    if work_month is not None:
        start_month = work_month
        end_month = work_month
    return get_productivity_monthly(start_month, end_month, pic, db)


@router.get("/low-margin", response_model=list[LowMarginItem])
def get_low_margin_cases(
    start_date: str | None = None,
    end_date: str | None = None,
    work_month: str | None = None,
    pic: str | None = None,
    trade_type: str | None = None,
    code: str | None = None,
    partner_name: str | None = None,
    customer_name: str | None = None,
    db: Session = Depends(get_db),
) -> list[LowMarginItem]:
    start_datetime, end_datetime, _ = resolve_date_range(
        start_date=start_date,
        end_date=end_date,
        work_month=work_month,
    )
    filters = _case_filters(
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        pic=pic,
        trade_type=trade_type,
        code=code,
        partner_name=partner_name,
        customer_name=customer_name,
    )
    approval_cases = db.execute(
        select(models.ApprovalCase)
        .where(*filters)
        .order_by(models.ApprovalCase.created_at.desc())
    ).scalars()

    low_margin_cases: list[LowMarginItem] = []
    for approval_case in approval_cases:
        required_rate = GP_RATE_RULES.get(approval_case.trade_type, 0)
        needs_review = approval_case.decision in {
            "CEO_REVIEW",
            "REJECTED",
            "CONDITIONAL_APPROVED",
        }
        below_required_rate = approval_case.net_gp_rate_ex_tax < required_rate
        if not needs_review and not below_required_rate:
            continue
        low_margin_cases.append(
            LowMarginItem(
                id=approval_case.id,
                customer_name=approval_case.customer_name,
                partner_name=approval_case.partner_name,
                trade_type=approval_case.trade_type,
                code=approval_case.code,
                gp_jpy=approval_case.gp_jpy,
                gp_rate=approval_case.gp_rate,
                net_gp_rate_ex_tax=approval_case.net_gp_rate_ex_tax,
                decision=approval_case.decision,
                executive_comment=approval_case.executive_comment,
                created_at=approval_case.created_at,
            )
        )
    return low_margin_cases
