from fastapi.testclient import TestClient

from app.main import app
from app.sample_cases import SAMPLE_CASES
from app.services.approval_engine import analyze_case


EXPECTED_SAMPLE_RESULTS = {
    "TOWA_SI_PLUS_PLUS": ("SI++", 24493, "CEO_REVIEW"),
    "KANGKOKU_HIROBA_SI_PLUS_PLUS": ("SI++", 145177, "APPROVED"),
    "HUMAN_MADE_SE_PLUS_PLUS": ("SE++", 32800, "APPROVED"),
    "PNS_SE": ("SE", 20798, "APPROVED"),
    "PNS_SE_FEE_MISSING": ("SE", 20798, "CONDITIONAL_APPROVED"),
    "DONGSHIN_SI": ("SI", 11128, "APPROVED"),
}


def test_sample_cases_have_expected_codes_and_gp() -> None:
    assert set(SAMPLE_CASES) == set(EXPECTED_SAMPLE_RESULTS)

    for sample_key, (
        expected_code,
        expected_gp,
        expected_decision,
    ) in EXPECTED_SAMPLE_RESULTS.items():
        result = analyze_case(SAMPLE_CASES[sample_key])

        assert result.code == expected_code
        assert result.gp_jpy == expected_gp
        assert result.decision == expected_decision


def test_sample_list_api_returns_sample_keys() -> None:
    client = TestClient(app)

    response = client.get("/api/samples")

    assert response.status_code == 200
    assert set(response.json()) == set(EXPECTED_SAMPLE_RESULTS)


def test_get_sample_api_returns_sample_case() -> None:
    client = TestClient(app)

    response = client.get("/api/samples/PNS_SE")

    assert response.status_code == 200
    assert response.json()["customer_name"] == "SUMITOMO CHEMICAL"
    assert response.json()["partner_fee"]["actual_fee_usd"] == 30


def test_analyze_sample_api_returns_approval_result() -> None:
    client = TestClient(app)

    response = client.post("/api/approvals/analyze-sample/DONGSHIN_SI")

    assert response.status_code == 200
    assert response.json()["code"] == "SI"
    assert response.json()["gp_jpy"] == 11128
    assert response.json()["decision"] == "APPROVED"


def test_partner_fee_ok_for_pns_and_dongshin_samples() -> None:
    for sample_key in ("PNS_SE", "DONGSHIN_SI"):
        result = analyze_case(SAMPLE_CASES[sample_key])
        partner_fee_finding = next(
            finding for finding in result.findings if finding.category == "Partner Fee"
        )

        assert partner_fee_finding.status == "OK"
        assert "정상 반영" in partner_fee_finding.message


def test_partner_fee_missing_sample_is_conditional_approved() -> None:
    result = analyze_case(SAMPLE_CASES["PNS_SE_FEE_MISSING"])
    partner_fee_finding = next(
        finding for finding in result.findings if finding.category == "Partner Fee"
    )

    assert partner_fee_finding.status == "WARN"
    assert "부족 또는 누락" in partner_fee_finding.message
    assert result.decision == "CONDITIONAL_APPROVED"


def test_sample_apis_return_404_for_unknown_key() -> None:
    client = TestClient(app)

    sample_response = client.get("/api/samples/UNKNOWN")
    analyze_response = client.post("/api/approvals/analyze-sample/UNKNOWN")

    assert sample_response.status_code == 404
    assert analyze_response.status_code == 404
