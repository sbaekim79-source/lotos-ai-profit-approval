from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models
from app.schemas import QuoteCostItem, QuoteRequest, QuoteResult
from app.services.approval_engine import GP_RATE_RULES, MINIMUM_GP_RULES


USD_JPY_RATE = 160


def generate_quote(request: QuoteRequest, db: Session) -> QuoteResult:
    warnings: list[str] = []
    items: list[QuoteCostItem] = []

    minimum_gp_jpy = _minimum_gp(request.code, db)
    target_gp_rate = request.target_gp_rate
    if target_gp_rate is None:
        target_gp_rate = _target_gp_rate(request.trade_type, db)

    if request.include_transport:
        items.append(_transport_item(request, db, warnings))

    if request.include_customs:
        items.append(_customs_item(request, db, warnings))

    partner_fee_item = _partner_fee_item(request, db)
    if partner_fee_item is not None:
        items.append(partner_fee_item)

    totals = _totals(items)
    if totals["gp"] < minimum_gp_jpy:
        shortage = minimum_gp_jpy - totals["gp"]
        items.append(
            QuoteCostItem(
                category="BASIC_MARGIN",
                name="Minimum GP 보정",
                basis=f"{request.code} Minimum GP {minimum_gp_jpy:.0f} JPY",
                estimated_cost_jpy=0,
                recommended_revenue_jpy=shortage,
                gp_jpy=shortage,
                source="MASTER",
                note="업무코드별 Minimum GP 충족을 위한 보정",
            )
        )
        totals = _totals(items)

    if target_gp_rate > 0 and totals["revenue"] > 0:
        current_rate = totals["gp"] / totals["revenue"]
        if current_rate < target_gp_rate:
            adjustment = _gp_rate_adjustment(
                revenue=totals["revenue"],
                gp=totals["gp"],
                target_gp_rate=target_gp_rate,
            )
            if adjustment > 0:
                items.append(
                    QuoteCostItem(
                        category="GP_RATE_ADJUSTMENT",
                        name="Target GP율 보정",
                        basis=f"Target GP Rate {target_gp_rate:.1%}",
                        estimated_cost_jpy=0,
                        recommended_revenue_jpy=adjustment,
                        gp_jpy=adjustment,
                        source="MASTER",
                        note="거래구분별 목표 GP율 충족을 위한 보정",
                    )
                )
                totals = _totals(items)

    expected_gp_rate = totals["gp"] / totals["revenue"] if totals["revenue"] else 0
    decision_hint = (
        "QUOTABLE"
        if not warnings
        and totals["gp"] >= minimum_gp_jpy
        and expected_gp_rate >= target_gp_rate
        else "NEED_REVIEW"
    )
    executive_summary = (
        f"{request.customer_name or '견적 대상'} {request.code} 견적은 "
        f"예상원가 {totals['cost']:.0f}엔, 권장청구액 {totals['revenue']:.0f}엔, "
        f"예상 GP {totals['gp']:.0f}엔, GP율 {expected_gp_rate:.1%}입니다. "
        f"판정: {decision_hint}."
    )

    return QuoteResult(
        customer_name=request.customer_name,
        code=request.code,
        trade_type=request.trade_type,
        total_estimated_cost_jpy=totals["cost"],
        total_recommended_revenue_jpy=totals["revenue"],
        expected_gp_jpy=totals["gp"],
        expected_gp_rate=expected_gp_rate,
        minimum_gp_jpy=minimum_gp_jpy,
        target_gp_rate=target_gp_rate,
        decision_hint=decision_hint,
        items=items,
        warnings=warnings,
        executive_summary=executive_summary,
    )


def _transport_item(
    request: QuoteRequest,
    db: Session,
    warnings: list[str],
) -> QuoteCostItem:
    if request.manual_transport_cost_jpy is not None:
        cost = request.manual_transport_cost_jpy
        source = "MANUAL"
        basis = "manual_transport_cost_jpy"
        note = "수동 입력 운송원가"
    else:
        cost = _avg_transport_cost(
            db,
            origin=request.origin,
            destination=request.destination,
            container_type=request.container_type,
        )
        source = "TARIFF_AVG"
        basis = "origin + destination + container_type"
        note = "Tariff DB 평균 운송원가"
        if cost is None:
            cost = _avg_transport_cost(
                db,
                port=request.port,
                container_type=request.container_type,
            )
            basis = "port + container_type"
        if cost is None:
            cost = 0
            source = "FALLBACK"
            basis = "no tariff match"
            note = "운송 Tariff 평균 원가를 찾지 못했습니다."
            warnings.append("운송 Tariff 원가 데이터가 부족합니다.")

    revenue = cost + max(3000, cost * 0.10) if cost > 0 else 0
    return QuoteCostItem(
        category="TRANSPORT",
        name="운송비",
        basis=basis,
        estimated_cost_jpy=cost,
        recommended_revenue_jpy=revenue,
        gp_jpy=revenue - cost,
        source=source,
        note=note,
    )


def _customs_item(
    request: QuoteRequest,
    db: Session,
    warnings: list[str],
) -> QuoteCostItem:
    if request.manual_customs_cost_jpy is not None:
        cost = request.manual_customs_cost_jpy
        source = "MANUAL"
        basis = "manual_customs_cost_jpy"
        note = "수동 입력 통관원가"
    else:
        cost = _avg_customs_cost(db, port=request.port, direction=request.direction)
        source = "TARIFF_AVG"
        basis = "port + direction"
        note = "Tariff DB 평균 통관원가"
        if cost is None:
            cost = 0
            source = "FALLBACK"
            basis = "no tariff match"
            note = "통관 Tariff 평균 원가를 찾지 못했습니다."
            warnings.append("통관 Tariff 원가 데이터가 부족합니다.")

    revenue = max(8000, cost + 3000) if cost > 0 else 8000
    return QuoteCostItem(
        category="CUSTOMS",
        name="통관수수료",
        basis=basis,
        estimated_cost_jpy=cost,
        recommended_revenue_jpy=revenue,
        gp_jpy=revenue - cost,
        source=source,
        note=note,
    )


def _partner_fee_item(request: QuoteRequest, db: Session) -> QuoteCostItem | None:
    if request.trade_type != "PARTNER" and not request.partner_name:
        return None

    if request.manual_partner_fee_jpy is not None:
        amount_jpy = request.manual_partner_fee_jpy
        settlement_direction = "PARTNER_PAY"
        source = "MANUAL"
        basis = "manual_partner_fee_jpy"
        note = "수동 입력 Partner Fee"
    else:
        rule = _partner_fee_rule(request, db)
        if rule is None:
            amount_jpy = 0
            settlement_direction = "LOTOS_COLLECT"
            source = "FALLBACK"
            basis = "no partner fee rule"
            note = "Partner Fee Rule을 찾지 못했습니다."
        else:
            amount_jpy = _partner_fee_amount_jpy(rule, request)
            settlement_direction = rule.settlement_direction
            source = "MASTER"
            basis = (
                f"{rule.partner_name} {rule.mode} {rule.direction} "
                f"{rule.unit_type} {rule.currency}"
            )
            note = rule.note

    if settlement_direction == "LOTOS_COLLECT":
        estimated_cost = 0.0
        recommended_revenue = amount_jpy
    else:
        estimated_cost = amount_jpy
        recommended_revenue = 0.0

    return QuoteCostItem(
        category="PARTNER_FEE",
        name="Partner Fee",
        basis=basis,
        estimated_cost_jpy=estimated_cost,
        recommended_revenue_jpy=recommended_revenue,
        gp_jpy=recommended_revenue - estimated_cost,
        source=source,
        note=note,
    )


def _avg_transport_cost(
    db: Session,
    origin: str | None = None,
    destination: str | None = None,
    port: str | None = None,
    container_type: str | None = None,
) -> float | None:
    statement = select(func.avg(models.TransportTariff.transport_cost_jpy))
    if origin is not None:
        statement = statement.where(models.TransportTariff.origin == origin)
    if destination is not None:
        statement = statement.where(models.TransportTariff.destination == destination)
    if port is not None:
        statement = statement.where(models.TransportTariff.port == port)
    if container_type is not None:
        statement = statement.where(models.TransportTariff.container_type == container_type)
    return db.execute(statement).scalar_one_or_none()


def _avg_customs_cost(
    db: Session,
    port: str | None,
    direction: str,
) -> float | None:
    statement = select(func.avg(models.CustomsTariff.customs_expense_jpy)).where(
        models.CustomsTariff.direction == direction
    )
    if port is not None:
        statement = statement.where(models.CustomsTariff.port == port)
    return db.execute(statement).scalar_one_or_none()


def _partner_fee_rule(
    request: QuoteRequest,
    db: Session,
) -> models.PartnerFeeRule | None:
    if not request.partner_name:
        return None
    statement = (
        select(models.PartnerFeeRule)
        .where(
            models.PartnerFeeRule.is_active.is_(True),
            models.PartnerFeeRule.mode == request.mode,
            models.PartnerFeeRule.direction == request.direction,
            models.PartnerFeeRule.partner_name.ilike(f"%{request.partner_name}%"),
        )
        .order_by(models.PartnerFeeRule.container_type.desc().nullslast())
    )
    rules = list(db.execute(statement).scalars())
    if not rules:
        statement = (
            select(models.PartnerFeeRule)
            .where(
                models.PartnerFeeRule.is_active.is_(True),
                models.PartnerFeeRule.mode == request.mode,
                models.PartnerFeeRule.direction == request.direction,
            )
            .order_by(models.PartnerFeeRule.container_type.desc().nullslast())
        )
        rules = [
            rule
            for rule in db.execute(statement).scalars()
            if rule.partner_name.upper() in request.partner_name.upper()
            or request.partner_name.upper() in rule.partner_name.upper()
        ]
    for rule in rules:
        if not rule.container_type:
            return rule
        if request.container_type and rule.container_type.upper() in request.container_type.upper():
            return rule
        if request.container_type and request.container_type.upper() in rule.container_type.upper():
            return rule
    return rules[0] if rules else None


def _partner_fee_amount_jpy(
    rule: models.PartnerFeeRule,
    request: QuoteRequest,
) -> float:
    multiplier = 1
    if rule.unit_type in {"CNTR", "CONTAINER"}:
        multiplier = request.container_count
    amount = rule.amount * multiplier
    if rule.currency == "USD":
        return amount * USD_JPY_RATE
    return amount


def _minimum_gp(code: str, db: Session) -> float:
    rule = db.execute(
        select(models.MinimumGPRule).where(
            models.MinimumGPRule.code == code,
            models.MinimumGPRule.is_active.is_(True),
        )
    ).scalar_one_or_none()
    if rule is not None:
        return rule.minimum_gp_jpy
    return MINIMUM_GP_RULES.get(code, 0)


def _target_gp_rate(trade_type: str, db: Session) -> float:
    rule = db.execute(
        select(models.GPRateRule).where(
            models.GPRateRule.trade_type == trade_type,
            models.GPRateRule.is_active.is_(True),
        )
    ).scalar_one_or_none()
    if rule is not None:
        return rule.minimum_gp_rate
    return GP_RATE_RULES.get(trade_type, 0)


def _gp_rate_adjustment(revenue: float, gp: float, target_gp_rate: float) -> float:
    if target_gp_rate >= 1:
        return 0
    shortage = (target_gp_rate * revenue - gp) / (1 - target_gp_rate)
    return max(shortage, 0)


def _totals(items: list[QuoteCostItem]) -> dict[str, float]:
    cost = sum(item.estimated_cost_jpy for item in items)
    revenue = sum(item.recommended_revenue_jpy for item in items)
    return {
        "cost": cost,
        "revenue": revenue,
        "gp": revenue - cost,
    }
