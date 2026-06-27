from fastapi.testclient import TestClient

from app.main import app
from app.sample_cases import SAMPLE_CASES
from app.schemas import ApprovalCaseInput
from app.services.approval_engine import (
    analyze_case,
    determine_code,
    expected_partner_fee,
    safe_rate,
    total,
)


def make_case(**overrides: object) -> ApprovalCaseInput:
    data = {
        "customer_name": "LOTOS TEST",
        "trade_type": "SHIPPER",
        "mode": "SEA",
        "direction": "EXPORT",
        "revenue_items": [{"name": "Ocean Freight", "amount_jpy": 100000}],
        "expense_items": [{"name": "Carrier Cost", "amount_jpy": 70000}],
    }
    data.update(overrides)
    return ApprovalCaseInput.model_validate(data)


def has_finding(result: object, category: str, status: str) -> bool:
    return any(
        finding.category == category and finding.status == status
        for finding in result.findings
    )


def test_total_sums_charge_items() -> None:
    case = make_case()

    assert total(case.revenue_items) == 100000


def test_safe_rate_returns_zero_when_denominator_is_zero() -> None:
    assert safe_rate(10, 0) == 0
    assert safe_rate(10, 20) == 0.5


def test_towa_si_plus_plus_requires_review() -> None:
    result = analyze_case(SAMPLE_CASES["TOWA_SI_PLUS_PLUS"])

    assert result.code == "SI++"
    assert result.gp_jpy == 24493
    assert result.minimum_gp_jpy == 30800
    assert result.decision in {"CEO_REVIEW", "CONDITIONAL_APPROVED"}
    assert has_finding(result, "Minimum GP", "NG")
    assert has_finding(result, "운송마진", "NG")


def test_kangkokuk_hiroba_si_plus_plus_is_approved() -> None:
    result = analyze_case(SAMPLE_CASES["KANGKOKU_HIROBA_SI_PLUS_PLUS"])

    assert result.code == "SI++"
    assert result.gp_jpy == 145177
    assert result.decision == "APPROVED"
    assert has_finding(result, "Minimum GP", "OK")
    assert has_finding(result, "운송마진", "OK")


def test_human_made_se_plus_plus_is_approved() -> None:
    result = analyze_case(SAMPLE_CASES["HUMAN_MADE_SE_PLUS_PLUS"])

    assert result.code == "SE++"
    assert result.gp_jpy == 32800
    assert result.decision == "APPROVED"
    assert has_finding(result, "Minimum GP", "OK")
    assert has_finding(result, "운송마진", "OK")


def test_pns_partner_fee_is_ok() -> None:
    result = analyze_case(SAMPLE_CASES["PNS_SE"])

    assert result.code == "SE"
    assert result.gp_jpy == 20798
    assert result.decision == "APPROVED"
    assert has_finding(result, "Partner Fee", "OK")


def test_dongshin_partner_fee_is_ok() -> None:
    result = analyze_case(SAMPLE_CASES["DONGSHIN_SI"])

    assert result.code == "SI"
    assert result.gp_jpy == 11128
    assert result.decision == "APPROVED"
    assert has_finding(result, "Partner Fee", "OK")


def test_pns_partner_fee_missing_is_conditional_approved() -> None:
    result = analyze_case(SAMPLE_CASES["PNS_SE_FEE_MISSING"])

    assert result.code == "SE"
    assert has_finding(result, "Partner Fee", "WARN")
    assert result.decision == "CONDITIONAL_APPROVED"


def test_determine_code_returns_expected_business_codes() -> None:
    cases = [
        ({"mode": "SEA", "direction": "EXPORT"}, "SE"),
        ({"mode": "SEA", "direction": "EXPORT", "has_customs": True}, "SE+"),
        (
            {
                "mode": "SEA",
                "direction": "EXPORT",
                "has_customs": True,
                "has_transport": True,
            },
            "SE++",
        ),
        (
            {
                "mode": "SEA",
                "direction": "EXPORT",
                "has_customs": True,
                "has_transport": True,
                "has_work": True,
            },
            "SE+++",
        ),
        ({"mode": "SEA", "direction": "IMPORT"}, "SI"),
        ({"mode": "SEA", "direction": "IMPORT", "has_customs": True}, "SI+"),
        (
            {
                "mode": "SEA",
                "direction": "IMPORT",
                "has_customs": True,
                "has_transport": True,
            },
            "SI++",
        ),
        (
            {
                "mode": "AIR",
                "direction": "EXPORT",
                "has_customs": True,
                "has_transport": True,
            },
            "AE++",
        ),
        (
            {
                "mode": "AIR",
                "direction": "IMPORT",
                "has_customs": True,
                "has_transport": True,
            },
            "AI++",
        ),
    ]

    for overrides, expected_code in cases:
        assert determine_code(make_case(**overrides)) == expected_code


def test_expected_partner_fee_prioritizes_j2k_mizushima_special_rule() -> None:
    case = make_case(
        partner_name="J2K GLOBAL",
        pol="MIZUSHIMA",
        shipper_name="NAKASHIMA PROPELLER",
        partner_fee={
            "partner_name": "J2K GLOBAL",
            "bl_count": 2,
            "container_type": "40HC",
            "container_count": 1,
        },
    )

    expected = expected_partner_fee(case)

    assert expected is not None
    assert expected.currency == "USD"
    assert expected.amount == 1000
    assert expected.direction == "LOTOS_COLLECT"


def test_expected_partner_fee_j2k_import_credit_rule() -> None:
    case = make_case(
        partner_name="J2K GLOBAL",
        direction="IMPORT",
        shipper_name="HANKUK STEEL",
        container_type="20DC",
        container_count=3,
    )

    expected = expected_partner_fee(case)

    assert expected is not None
    assert expected.currency == "USD"
    assert expected.amount == 150
    assert expected.direction == "PARTNER_CREDIT"


def test_partner_fee_overcharge_warns_but_keeps_conditional_decision() -> None:
    case = make_case(
        partner_name="DONGSHIN SEA & AIR",
        direction="IMPORT",
        partner_fee={
            "partner_name": "DONGSHIN SEA & AIR",
            "actual_fee_jpy": 5000,
        },
    )

    result = analyze_case(case)
    partner_fee_finding = next(
        finding for finding in result.findings if finding.category == "Partner Fee"
    )

    assert partner_fee_finding.status == "WARN"
    assert "과다반영 확인 필요" in partner_fee_finding.message
    assert result.decision == "CONDITIONAL_APPROVED"


def test_analyze_api_returns_approval_result() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/approvals/analyze",
        json={
            "customer_name": "LOTOS TEST",
            "trade_type": "FORWARDER",
            "mode": "AIR",
            "direction": "IMPORT",
            "has_transport": True,
            "revenue_items": [{"name": "Air Freight", "amount_jpy": 50000}],
            "expense_items": [{"name": "Airline Cost", "amount_jpy": 35000}],
        },
    )

    assert response.status_code == 200
    assert response.json()["code"] == "AI++"
