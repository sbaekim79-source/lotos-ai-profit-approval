from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app import models
from app.database import Base, engine
from app.schemas import ApprovalCaseInput, ApprovalResult, ChargeItem, Finding


@dataclass(frozen=True)
class PartnerFeeExpected:
    currency: str
    amount: float
    direction: str
    note: str


MINIMUM_GP_RULES: dict[str, float] = {
    "SE": 6000,
    "SE+": 19900,
    "SE++": 22900,
    "SE+++": 22900,
    "SI": 8000,
    "SI+": 27800,
    "SI++": 30800,
    "SI+++": 30800,
    "AE": 6000,
    "AE+": 14000,
    "AE++": 17000,
    "AE+++": 17000,
    "AI": 6000,
    "AI+": 14000,
    "AI++": 17000,
    "AI+++": 17000,
}

POINT_RULES: dict[str, float] = {
    "SE": 1,
    "SE+": 1.5,
    "SE++": 2,
    "SE+++": 2.5,
    "SI": 1,
    "SI+": 1.5,
    "SI++": 2,
    "SI+++": 2.5,
    "AE": 1,
    "AE+": 1.5,
    "AE++": 2,
    "AE+++": 2.5,
    "AI": 1,
    "AI+": 1.5,
    "AI++": 2,
    "AI+++": 2.5,
    "PJT": 0,
}

GP_RATE_RULES: dict[str, float] = {
    "SHIPPER": 0.15,
    "FORWARDER": 0.10,
    "PARTNER": 0.05,
}

SELF_CUSTOMS_PRIORITY_PORTS = {"TOKYO", "YOKOHAMA", "KOBE", "OSAKA", "HAKATA"}


def total(items: list[ChargeItem]) -> float:
    return sum(item.amount_jpy for item in items)


def safe_rate(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0
    return numerator / denominator


def determine_code(case: ApprovalCaseInput) -> str:
    if case.is_project:
        return "PJT"

    code_prefixes = {
        ("SEA", "EXPORT"): "SE",
        ("SEA", "IMPORT"): "SI",
        ("AIR", "EXPORT"): "AE",
        ("AIR", "IMPORT"): "AI",
    }
    base_code = code_prefixes[(case.mode, case.direction)]

    if case.has_work:
        return f"{base_code}+++"
    if case.has_transport:
        return f"{base_code}++"
    if case.has_customs:
        return f"{base_code}+"
    return base_code


def _contains_any(value: str | None, keywords: list[str]) -> bool:
    if value is None:
        return False
    normalized = value.upper()
    return any(keyword.upper() in normalized for keyword in keywords)


def _charge_items_contain(items: list[ChargeItem], keywords: list[str]) -> bool:
    return any(_contains_any(item.name, keywords) for item in items)


def _format_rate(rate: float) -> str:
    return f"{rate:.1%}"


def _format_amount(amount: float) -> str:
    if amount == int(amount):
        return str(int(amount))
    return str(amount)


def _partner_name(case: ApprovalCaseInput) -> str | None:
    if case.partner_name:
        return case.partner_name
    if case.partner_fee is not None:
        return case.partner_fee.partner_name
    return None


def _partner_bl_count(case: ApprovalCaseInput) -> int:
    if case.partner_fee is not None:
        return case.partner_fee.bl_count
    return 1


def _partner_container_type(case: ApprovalCaseInput) -> str | None:
    if case.partner_fee is not None and case.partner_fee.container_type:
        return case.partner_fee.container_type
    return case.container_type


def _partner_container_count(case: ApprovalCaseInput) -> int:
    if case.partner_fee is not None:
        return case.partner_fee.container_count
    return case.container_count


def _partner_special_condition(case: ApprovalCaseInput) -> str | None:
    if case.partner_fee is None:
        return None
    return case.partner_fee.special_condition


def expected_partner_fee(case: ApprovalCaseInput) -> PartnerFeeExpected | None:
    partner_name = _partner_name(case)
    container_type = _partner_container_type(case)
    container_count = _partner_container_count(case)
    bl_count = _partner_bl_count(case)
    special_condition = _partner_special_condition(case)

    if partner_name is None:
        return None

    if (
        _contains_any(partner_name, ["TAEWOONG", "?쒖썒"])
        and case.mode == "SEA"
        and case.direction == "EXPORT"
    ):
        return PartnerFeeExpected(
            currency="USD",
            amount=20 * bl_count,
            direction="LOTOS_COLLECT",
            note="?쒖썒濡쒖쭅???댁긽?섏텧 USD20/BL",
        )

    if _contains_any(partner_name, ["J2K"]):
        has_nakashima = _contains_any(case.shipper_name, ["NAKASHIMA", "?섏뭅?쒕쭏"]) or (
            _contains_any(special_condition, ["NAKASHIMA", "?섏뭅?쒕쭏"])
        )
        if _contains_any(case.pol, ["MIZUSHIMA"]) and has_nakashima:
            return PartnerFeeExpected(
                currency="USD",
                amount=500 * bl_count,
                direction="LOTOS_COLLECT",
                note="J2K MIZUSHIMA ?섏뭅?쒕쭏 ?꾨줈?좊윭 USD500/BL",
            )

        has_hankuk_condition = (
            _contains_any(case.shipper_name, ["?쒓뎅?좎옱", "HANKUK", "LOTOS NOMI"])
            or _contains_any(special_condition, ["?쒓뎅?좎옱", "HANKUK", "LOTOS NOMI"])
        )
        if (
            case.direction == "IMPORT"
            and has_hankuk_condition
            and _contains_any(container_type, ["20"])
        ):
            return PartnerFeeExpected(
                currency="USD",
                amount=50 * container_count,
                direction="PARTNER_CREDIT",
                note="J2K GLOBAL ?섏엯 CREDIT USD50/20FT",
            )

        if case.mode == "SEA" and case.direction == "EXPORT":
            if _contains_any(container_type, ["20"]):
                return PartnerFeeExpected(
                    currency="USD",
                    amount=20 * container_count,
                    direction="LOTOS_COLLECT",
                    note="J2K GLOBAL ?댁긽?섏텧 20FT USD20/CNTR",
                )
            if _contains_any(container_type, ["40"]):
                return PartnerFeeExpected(
                    currency="USD",
                    amount=40 * container_count,
                    direction="LOTOS_COLLECT",
                    note="J2K GLOBAL ?댁긽?섏텧 40FT USD40/CNTR",
                )

    if (
        _contains_any(partner_name, ["PNS"])
        and case.direction == "EXPORT"
        and _contains_any(container_type, ["40"])
    ):
        return PartnerFeeExpected(
            currency="USD",
            amount=15 * container_count,
            direction="LOTOS_COLLECT",
            note="PNS NETWORKS ?섏텧 40FT USD15/CNTR",
        )

    if _contains_any(partner_name, ["DONGSHIN", "DONG SHIN"]) and case.direction == "IMPORT":
        return PartnerFeeExpected(
            currency="JPY",
            amount=4000,
            direction="PARTNER_PAY",
            note="DONGSHIN SEA & AIR ?섏엯 JPY4000/SHIPMENT",
        )

    if _contains_any(partner_name, ["EUNSAN"]) and case.direction == "IMPORT":
        return PartnerFeeExpected(
            currency="USD",
            amount=15 * bl_count,
            direction="PARTNER_PAY",
            note="EUNSAN ?섏엯 USD15/BL",
        )

    if _contains_any(partner_name, ["DONGWON", "?숈썝"]) and case.direction == "EXPORT":
        if _contains_any(case.shipper_name, ["ITOCHU"]):
            return PartnerFeeExpected(
                currency="USD",
                amount=10 * bl_count,
                direction="LOTOS_COLLECT",
                note="?숈썝濡쒖뿊??ITOCHU ?섏텧 USD10/BL",
            )
        return PartnerFeeExpected(
            currency="USD",
            amount=20,
            direction="LOTOS_COLLECT",
            note="?숈썝濡쒖뿊???섏텧 USD20/SHIP",
        )

    return None


def _determine_decision(
    code: str,
    gp_jpy: float,
    minimum_gp_jpy: float,
    findings: list[Finding],
) -> str:
    if gp_jpy < 0:
        return "REJECTED"
    if code == "PJT":
        return "CEO_REVIEW"

    minimum_gp_finding = next(
        (
            finding
            for finding in findings
            if finding.category == "Minimum GP" and finding.status == "NG"
        ),
        None,
    )
    if minimum_gp_finding is not None:
        shortfall = minimum_gp_jpy - gp_jpy
        if minimum_gp_jpy > 0 and shortfall <= minimum_gp_jpy * 0.10:
            return "CONDITIONAL_APPROVED"
        return "CEO_REVIEW"

    if any(
        finding.category == "?댁넚留덉쭊" and finding.status == "NG"
        for finding in findings
    ):
        return "CONDITIONAL_APPROVED"

    if any(
        finding.category == "鍮꾩슜?꾨씫" and finding.status == "WARN"
        for finding in findings
    ):
        return "CEO_REVIEW"

    if any(
        finding.category == "Partner Fee" and finding.status == "WARN"
        for finding in findings
    ):
        return "CONDITIONAL_APPROVED"

    if any(finding.status in {"WARN", "NG"} for finding in findings):
        return "CONDITIONAL_APPROVED"

    return "APPROVED"


def _build_executive_comment(
    case: ApprovalCaseInput,
    code: str,
    gp_jpy: float,
    gp_rate: float,
    net_gp_rate_ex_tax: float,
    decision: str,
    findings: list[Finding],
) -> str:
    problem_messages = [
        finding.message for finding in findings if finding.status in {"WARN", "NG"}
    ]
    if not problem_messages:
        return (
            f"{case.customer_name} {code} ?덇굔? GP {gp_jpy:.0f}?? "
            f"GP??{_format_rate(gp_rate)}, ?짨P??{_format_rate(net_gp_rate_ex_tax)}濡?"
            "湲곗???異⑹”?섏뿬 ?뱀씤?⑸땲??"
        )

    summary = "; ".join(problem_messages[:3])
    return (
        f"{case.customer_name} {code} ?덇굔? GP {gp_jpy:.0f}?? "
        f"GP??{_format_rate(gp_rate)}, ?짨P??{_format_rate(net_gp_rate_ex_tax)}?낅땲?? "
        f"二쇱슂 ?뺤씤?ы빆: {summary} ??{decision}."
    )


def _append_partner_fee_finding(
    case: ApprovalCaseInput,
    findings: list[Finding],
) -> None:
    expected = expected_partner_fee(case)
    if expected is None:
        return

    if case.partner_fee is None:
        actual = 0
    elif expected.currency == "USD":
        actual = case.partner_fee.actual_fee_usd
    else:
        actual = case.partner_fee.actual_fee_jpy

    expected_amount = expected.amount
    if actual == expected_amount:
        findings.append(
            Finding(
                category="Partner Fee",
                status="OK",
                message=f"{expected.note} 정상 반영",
                amount_jpy=None,
            )
        )
        return

    if actual < expected_amount:
        message_suffix = "부족 또는 누락"
    else:
        message_suffix = "과다반영 확인 필요"

    findings.append(
        Finding(
            category="Partner Fee",
            status="WARN",
            message=(
                f"{expected.note}. 예상 {_format_amount(expected_amount)}{expected.currency}, "
                f"실제 {_format_amount(actual)}{expected.currency}. {message_suffix}"
            ),
            amount_jpy=None,
        )
    )


def analyze_case(case: ApprovalCaseInput) -> ApprovalResult:
    code = determine_code(case)
    tax_and_duty_jpy = case.customs_duty_jpy + case.consumption_tax_jpy

    total_revenue_jpy = total(case.revenue_items)
    total_expense_jpy = total(case.expense_items)
    gp_jpy = total_revenue_jpy - total_expense_jpy
    gp_rate = safe_rate(gp_jpy, total_revenue_jpy)
    net_revenue_ex_tax_jpy = total_revenue_jpy - tax_and_duty_jpy
    net_expense_ex_tax_jpy = total_expense_jpy - tax_and_duty_jpy
    net_gp_rate_ex_tax = safe_rate(gp_jpy, net_revenue_ex_tax_jpy)
    minimum_gp_jpy = MINIMUM_GP_RULES.get(code, 0)
    findings: list[Finding] = []

    if gp_jpy >= minimum_gp_jpy:
        findings.append(
            Finding(
                category="Minimum GP",
                status="OK",
                message=f"{code} 湲곗? GP {minimum_gp_jpy:.0f}??異⑹”",
            )
        )
    else:
        findings.append(
            Finding(
                category="Minimum GP",
                status="NG",
                message=f"{code} 湲곗? GP {minimum_gp_jpy:.0f}??誘몃떖",
                amount_jpy=gp_jpy - minimum_gp_jpy,
            )
        )

    if (
        case.has_transport
        or case.transport_revenue_jpy > 0
        or case.transport_expense_jpy > 0
    ):
        transport_gp = case.transport_revenue_jpy - case.transport_expense_jpy
        transport_gp_rate = safe_rate(transport_gp, case.transport_revenue_jpy)
        transport_status = (
            "OK" if transport_gp >= 3000 and transport_gp_rate >= 0.10 else "NG"
        )
        if transport_status == "OK":
            transport_message = (
                f"운송 GP {transport_gp:.0f}엔, "
                f"GP율 {_format_rate(transport_gp_rate)} 기준 충족"
            )
        else:
            transport_message = (
                f"운송 GP {transport_gp:.0f}엔, "
                f"GP율 {_format_rate(transport_gp_rate)}. 기준 미달"
            )
        findings.append(
            Finding(
                category="운송마진",
                status=transport_status,
                message=transport_message,
                amount_jpy=transport_gp,
            )
        )

    if case.has_customs or case.customs_revenue_jpy > 0 or case.customs_expense_jpy > 0:
        customs_gp = case.customs_revenue_jpy - case.customs_expense_jpy
        if case.self_customs:
            customs_status = "OK" if case.customs_revenue_jpy >= 8000 else "WARN"
            customs_message = (
                "?먯궗?듦? ?섏닔猷?8,000???댁긽 異⑹”"
                if customs_status == "OK"
                else "?먯궗?듦? ?섏닔猷?8,000??誘몃떖"
            )
        else:
            customs_status = "OK" if customs_gp >= 3000 else "WARN"
            customs_message = (
                "??ы넻愿 ?섏껌鍮꾩슜 +3,000???댁긽 異⑹”"
                if customs_status == "OK"
                else "??ы넻愿 留덉쭊 +3,000??誘몃떖"
            )
        findings.append(
            Finding(
                category="?듦??섏씡",
                status=customs_status,
                message=customs_message,
                amount_jpy=customs_gp,
            )
        )

    required_gp_rate = GP_RATE_RULES[case.trade_type]
    if net_gp_rate_ex_tax >= required_gp_rate:
        gp_rate_status = "OK"
        gp_rate_message = (
            f"{case.trade_type} 湲곗? ?짨P??{_format_rate(required_gp_rate)} ?댁긽 異⑹”"
        )
    else:
        gp_rate_status = "WARN"
        gp_rate_message = (
            f"{case.trade_type} 湲곗? ?짨P??{_format_rate(required_gp_rate)} 誘몃떖"
        )
    findings.append(
        Finding(
            category="실GP율",
            status=gp_rate_status,
            message=gp_rate_message,
        )
    )

    if case.has_customs and not _charge_items_contain(
        case.revenue_items, ["CUSTOM", "?듦?", "CUSTOMS"]
    ):
        findings.append(
            Finding(
                category="鍮꾩슜?꾨씫",
                status="WARN",
                message="?듦? ?ы븿 ?덇굔?대굹 ?듦?猷?泥?뎄??ぉ???뺤씤?섏? ?딆뒿?덈떎.",
            )
        )

    if case.has_transport and case.transport_revenue_jpy <= 0:
        findings.append(
            Finding(
                category="鍮꾩슜?꾨씫",
                status="WARN",
                message="?댁넚 ?ы븿 ?덇굔?대굹 ?댁넚猷?泥?뎄媛 ?뺤씤?섏? ?딆뒿?덈떎.",
            )
        )

    if _contains_any(case.cargo_description, ["FOOD", "FROZEN", "?앺뭹", "?됰룞"]) and not (
        _charge_items_contain(case.revenue_items, ["FOOD", "?앺뭹"])
    ):
        findings.append(
            Finding(
                category="鍮꾩슜?꾨씫",
                status="WARN",
                message="?앺뭹/?됰룞 愿???붾Ъ?대굹 ?앺뭹?좉퀬猷뚭? ?뺤씤?섏? ?딆뒿?덈떎.",
            )
        )

    port = case.port.upper() if case.port is not None else None
    if (
        case.has_customs
        and port in SELF_CUSTOMS_PRIORITY_PORTS
        and not case.self_customs
    ):
        findings.append(
            Finding(
                category="?먯궗?먯썝",
                status="WARN",
                message=f"{port}???먯궗?듦? ?곗꽑 ?댁슜 ??곸엯?덈떎.",
            )
        )

    _append_partner_fee_finding(case, findings)

    decision = _determine_decision(code, gp_jpy, minimum_gp_jpy, findings)

    return ApprovalResult(
        customer_name=case.customer_name,
        code=code,
        point=POINT_RULES.get(code, 0),
        total_revenue_jpy=total_revenue_jpy,
        total_expense_jpy=total_expense_jpy,
        gp_jpy=gp_jpy,
        gp_rate=gp_rate,
        net_revenue_ex_tax_jpy=net_revenue_ex_tax_jpy,
        net_expense_ex_tax_jpy=net_expense_ex_tax_jpy,
        net_gp_rate_ex_tax=net_gp_rate_ex_tax,
        minimum_gp_jpy=minimum_gp_jpy,
        decision=decision,
        findings=findings,
        executive_comment=_build_executive_comment(
            case=case,
            code=code,
            gp_jpy=gp_jpy,
            gp_rate=gp_rate,
            net_gp_rate_ex_tax=net_gp_rate_ex_tax,
            decision=decision,
            findings=findings,
        ),
    )


def _determine_decision(
    code: str,
    gp_jpy: float,
    minimum_gp_jpy: float,
    findings: list[Finding],
) -> str:
    if gp_jpy < 0:
        return "REJECTED"
    if code == "PJT":
        return "CEO_REVIEW"

    minimum_gp_finding = next(
        (
            finding
            for finding in findings
            if finding.category == "Minimum GP" and finding.status == "NG"
        ),
        None,
    )
    if minimum_gp_finding is not None:
        shortfall = minimum_gp_jpy - gp_jpy
        if minimum_gp_jpy > 0 and shortfall <= minimum_gp_jpy * 0.10:
            return "CONDITIONAL_APPROVED"
        return "CEO_REVIEW"

    if any(
        finding.category in {"운송마진", "?댁넚留덉쭊"} and finding.status == "NG"
        for finding in findings
    ):
        return "CONDITIONAL_APPROVED"

    if any(
        finding.category in {"비용누락", "鍮꾩슜?꾨씫"} and finding.status == "WARN"
        for finding in findings
    ):
        return "CEO_REVIEW"

    if any(
        finding.category in {"자사자원", "?먯궗?먯썝"} and finding.status == "NG"
        for finding in findings
    ):
        return "CEO_REVIEW"

    if any(
        finding.category in {"자사자원", "?먯궗?먯썝"} and finding.status == "WARN"
        for finding in findings
    ):
        return "CONDITIONAL_APPROVED"

    if any(
        finding.category == "Partner Fee" and finding.status == "WARN"
        for finding in findings
    ):
        return "CONDITIONAL_APPROVED"

    if any(finding.status in {"WARN", "NG"} for finding in findings):
        return "CONDITIONAL_APPROVED"

    return "APPROVED"


def _db_minimum_gp(db: Session, code: str) -> float:
    rule = db.execute(
        select(models.MinimumGPRule).where(
            models.MinimumGPRule.code == code,
            models.MinimumGPRule.is_active.is_(True),
        )
    ).scalar_one_or_none()
    if rule is None:
        return MINIMUM_GP_RULES.get(code, 0)
    return rule.minimum_gp_jpy


def _db_point(db: Session, code: str) -> float:
    rule = db.execute(
        select(models.WorkCodeRule).where(
            models.WorkCodeRule.code == code,
            models.WorkCodeRule.is_active.is_(True),
        )
    ).scalar_one_or_none()
    if rule is None:
        return POINT_RULES.get(code, 0)
    return rule.point


def _db_gp_rate(db: Session, trade_type: str) -> float:
    rule = db.execute(
        select(models.GPRateRule).where(
            models.GPRateRule.trade_type == trade_type,
            models.GPRateRule.is_active.is_(True),
        )
    ).scalar_one_or_none()
    if rule is None:
        return GP_RATE_RULES.get(trade_type, 0)
    return rule.minimum_gp_rate


def _db_internal_ports(db: Session, resource_type: str) -> set[str]:
    rules = db.execute(
        select(models.InternalResourceRule).where(
            models.InternalResourceRule.resource_type == resource_type,
            models.InternalResourceRule.is_active.is_(True),
        )
    ).scalars()
    return {rule.port.upper() for rule in rules}


def _db_internal_resource_rules(
    db: Session,
    resource_type: str,
) -> list[models.InternalResourceRule]:
    try:
        rules = db.execute(
            select(models.InternalResourceRule).where(
                models.InternalResourceRule.resource_type == resource_type,
                models.InternalResourceRule.is_active.is_(True),
            )
        ).scalars()
    except OperationalError:
        Base.metadata.create_all(bind=engine)
        rules = db.execute(
            select(models.InternalResourceRule).where(
                models.InternalResourceRule.resource_type == resource_type,
                models.InternalResourceRule.is_active.is_(True),
            )
        ).scalars()
    return list(rules)


def _is_self_vendor(vendor_name: str | None) -> bool:
    if vendor_name is None or vendor_name.strip() == "":
        return True
    vendor_upper = vendor_name.upper()
    return any(keyword in vendor_upper for keyword in ["LOTOS", "SELF", "자사"])


def _rule_matches_port(rule: models.InternalResourceRule, *ports: str | None) -> bool:
    rule_port = rule.port.upper()
    return any(port is not None and port.upper() == rule_port for port in ports)


def check_internal_resource_rules(
    case: ApprovalCaseInput,
    db: Session,
) -> list[Finding]:
    findings: list[Finding] = []
    port = case.port.upper() if case.port else None

    if case.has_customs and port:
        customs_rules = [
            rule
            for rule in _db_internal_resource_rules(db, "CUSTOMS")
            if rule.mandatory and _rule_matches_port(rule, case.port)
        ]
        for rule in customs_rules:
            if case.self_customs:
                findings.append(
                    Finding(
                        category="자사자원",
                        status="OK",
                        message=f"{port}는 자사통관 우선 PORT이며 자사통관을 사용했습니다.",
                    )
                )
            elif case.external_customs_reason:
                findings.append(
                    Finding(
                        category="자사자원",
                        status="WARN",
                        message=(
                            f"{port}는 자사통관 우선 PORT이나 외부통관을 사용했습니다. "
                            f"사유: {case.external_customs_reason}"
                        ),
                    )
                )
            else:
                findings.append(
                    Finding(
                        category="자사자원",
                        status="NG",
                        message=f"{port}는 자사통관 우선 PORT이나 외부통관 사용 사유가 없습니다.",
                    )
                )

    if (case.has_work or case.warehouse_vendor_name) and port:
        warehouse_rules = [
            rule
            for rule in _db_internal_resource_rules(db, "WAREHOUSE")
            if rule.mandatory and _rule_matches_port(rule, case.port)
        ]
        for rule in warehouse_rules:
            if _is_self_vendor(case.warehouse_vendor_name):
                findings.append(
                    Finding(
                        category="자사자원",
                        status="OK",
                        message=f"{port}는 자사창고 우선 PORT이며 자사창고를 사용했습니다.",
                    )
                )
            elif case.external_warehouse_reason:
                findings.append(
                    Finding(
                        category="자사자원",
                        status="WARN",
                        message=(
                            f"{port}는 자사창고 우선 PORT이나 외부창고를 사용했습니다. "
                            f"사유: {case.external_warehouse_reason}"
                        ),
                    )
                )
            else:
                findings.append(
                    Finding(
                        category="자사자원",
                        status="NG",
                        message=f"{port}는 자사창고 우선 PORT이나 외부창고 사용 사유가 없습니다.",
                    )
                )

    if case.has_transport:
        transport_rules = [
            rule
            for rule in _db_internal_resource_rules(db, "TRANSPORT")
            if rule.mandatory and _rule_matches_port(rule, case.port, case.pol, case.pod)
        ]
        for rule in transport_rules:
            matched_port = rule.port.upper()
            if _is_self_vendor(case.transport_vendor_name):
                findings.append(
                    Finding(
                        category="자사자원",
                        status="OK",
                        message=f"{matched_port}는 자사운송 우선 대상이며 자사운송을 사용했습니다.",
                    )
                )
            elif case.external_transport_reason:
                findings.append(
                    Finding(
                        category="자사자원",
                        status="WARN",
                        message=(
                            f"{matched_port}는 자사운송 우선 대상이나 외부운송을 사용했습니다. "
                            f"사유: {case.external_transport_reason}"
                        ),
                    )
                )
            else:
                findings.append(
                    Finding(
                        category="자사자원",
                        status="NG",
                        message=f"{matched_port}는 자사운송 우선 대상이나 외부운송 사용 사유가 없습니다.",
                    )
                )

    return findings


def _required_when_applies(required_when: str, case: ApprovalCaseInput) -> bool:
    required_when = required_when.upper()
    cargo = (case.cargo_description or "").upper()
    if required_when == "ALWAYS":
        return True
    if required_when == "CUSTOMS":
        return case.has_customs
    if required_when == "TRANSPORT":
        return case.has_transport
    if required_when == "FOOD":
        return any(keyword in cargo for keyword in ["FOOD", "FROZEN", "식품", "냉동"])
    if required_when == "IMPORT":
        return case.direction == "IMPORT"
    if required_when == "EXPORT":
        return case.direction == "EXPORT"
    return False


def _matches_required_charge_rule(
    rule: models.RequiredChargeRule,
    case: ApprovalCaseInput,
    code: str,
) -> bool:
    if rule.code not in {code, "ANY"}:
        return False
    if rule.mode not in {case.mode, "ANY"}:
        return False
    if rule.direction not in {case.direction, "ANY"}:
        return False
    return _required_when_applies(rule.required_when, case)


def _applicable_required_charge_rules(
    case: ApprovalCaseInput,
    db: Session,
) -> list[models.RequiredChargeRule]:
    code = determine_code(case)
    try:
        rules = db.execute(
            select(models.RequiredChargeRule).where(
                models.RequiredChargeRule.is_active.is_(True),
            )
        ).scalars()
    except OperationalError:
        Base.metadata.create_all(bind=engine)
        rules = db.execute(
            select(models.RequiredChargeRule).where(
                models.RequiredChargeRule.is_active.is_(True),
            )
        ).scalars()
    return [rule for rule in rules if _matches_required_charge_rule(rule, case, code)]


def _has_detailed_charge_items(case: ApprovalCaseInput) -> bool:
    return any(
        item.name.strip().upper() != "TOTAL" and item.amount_jpy != 0
        for item in case.revenue_items + case.expense_items
    )


def check_required_charges_with_rules(
    case: ApprovalCaseInput,
    db: Session,
) -> list[Finding]:
    rules = _applicable_required_charge_rules(case, db)
    if not rules:
        return []
    if not _has_detailed_charge_items(case):
        return []

    charge_text = " ".join(
        [
            *(item.name for item in case.revenue_items),
            *(item.name for item in case.expense_items),
        ]
    ).upper()
    searchable_text = f"{charge_text} {(case.cargo_description or '')}".upper()

    findings: list[Finding] = []
    for rule in rules:
        keywords = [keyword.strip().upper() for keyword in rule.keywords.split(",")]
        keywords = [keyword for keyword in keywords if keyword]
        target_text = charge_text if rule.charge_name == "FOOD_DECLARATION" else searchable_text
        if any(keyword in target_text for keyword in keywords):
            continue
        description = rule.description or "필수 청구항목 Master"
        findings.append(
            Finding(
                category="비용누락",
                status=rule.severity,
                message=(
                    f"{rule.charge_name} 필수 확인 항목이 누락된 것으로 보입니다. "
                    f"({description})"
                ),
            )
        )
    return findings


def _replace_finding(
    findings: list[Finding],
    category: str,
    replacement: Finding,
) -> list[Finding]:
    replaced = False
    next_findings: list[Finding] = []
    for finding in findings:
        if finding.category == category:
            if not replaced:
                next_findings.append(replacement)
                replaced = True
            continue
        next_findings.append(finding)
    if not replaced:
        next_findings.append(replacement)
    return next_findings


def analyze_case_with_rules(case: ApprovalCaseInput, db: Session) -> ApprovalResult:
    result = analyze_case(case)
    minimum_gp_jpy = _db_minimum_gp(db, result.code)
    point = _db_point(db, result.code)
    required_gp_rate = _db_gp_rate(db, case.trade_type)
    findings = list(result.findings)

    if result.gp_jpy >= minimum_gp_jpy:
        minimum_finding = Finding(
            category="Minimum GP",
            status="OK",
            message=f"{result.code} 기준 GP {minimum_gp_jpy:.0f}엔 충족",
        )
    else:
        minimum_finding = Finding(
            category="Minimum GP",
            status="NG",
            message=f"{result.code} 기준 GP {minimum_gp_jpy:.0f}엔 미달",
            amount_jpy=result.gp_jpy - minimum_gp_jpy,
        )
    findings = _replace_finding(findings, "Minimum GP", minimum_finding)

    gp_rate_status = "OK" if result.net_gp_rate_ex_tax >= required_gp_rate else "WARN"
    findings = [
        finding
        for finding in findings
        if finding.category not in {"실GP율", "?짨P??"}
    ]
    findings.append(
        Finding(
            category="실GP율",
            status=gp_rate_status,
            message=(
                f"{case.trade_type} 기준 실GP율 {_format_rate(required_gp_rate)} "
                + ("이상 충족" if gp_rate_status == "OK" else "미달")
            ),
        )
    )

    required_charge_rules = _applicable_required_charge_rules(case, db)
    if required_charge_rules and _has_detailed_charge_items(case):
        findings = [
            finding
            for finding in findings
            if finding.category not in {"비용누락", "鍮꾩슜?꾨씫"}
        ]
        findings.extend(check_required_charges_with_rules(case, db))

    findings = [
        finding
        for finding in findings
        if finding.category not in {"자사자원", "?먯궗?먯썝"}
    ]
    internal_resource_findings = check_internal_resource_rules(case, db)
    if internal_resource_findings:
        findings.extend(internal_resource_findings)
    else:
        port = case.port.upper() if case.port is not None else None
        customs_ports = _db_internal_ports(db, "CUSTOMS") or SELF_CUSTOMS_PRIORITY_PORTS
        if case.has_customs and port in customs_ports and not case.self_customs:
            findings.append(
                Finding(
                    category="자사자원",
                    status="WARN",
                    message=f"{port}는 자사통관 우선 이용 대상입니다.",
                )
            )

    decision = _determine_decision(
        result.code,
        result.gp_jpy,
        minimum_gp_jpy,
        findings,
    )

    return result.model_copy(
        update={
            "point": point,
            "minimum_gp_jpy": minimum_gp_jpy,
            "findings": findings,
            "decision": decision,
            "executive_comment": _build_executive_comment(
                case=case,
                code=result.code,
                gp_jpy=result.gp_jpy,
                gp_rate=result.gp_rate,
                net_gp_rate_ex_tax=result.net_gp_rate_ex_tax,
                decision=decision,
                findings=findings,
            ),
        }
    )
