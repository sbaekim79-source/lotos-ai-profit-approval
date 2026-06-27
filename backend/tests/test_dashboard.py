from fastapi.testclient import TestClient

from app.main import app


def save_sample(client: TestClient, sample_key: str) -> None:
    response = client.post(f"/api/approvals/analyze-sample-and-save/{sample_key}")
    assert response.status_code == 200


def test_dashboard_summary_productivity_and_low_margin() -> None:
    client = TestClient(app)
    for sample_key in (
        "TOWA_SI_PLUS_PLUS",
        "KANGKOKU_HIROBA_SI_PLUS_PLUS",
        "HUMAN_MADE_SE_PLUS_PLUS",
        "PNS_SE",
        "DONGSHIN_SI",
    ):
        save_sample(client, sample_key)

    summary_response = client.get("/api/dashboard/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["period_label"]
    assert summary["start_date"]
    assert summary["end_date"]
    assert "filters" in summary
    assert summary["total_cases"] >= 5
    assert summary["decision_counts"]["APPROVED"] >= 4
    assert summary["decision_counts"]["CEO_REVIEW"] >= 1
    assert summary["code_counts"]["SI++"] >= 2
    assert summary["productivity_by_pic"]
    assert summary["gp_by_customer"]
    assert summary["partner_summary"]

    productivity_response = client.get("/api/dashboard/productivity")
    assert productivity_response.status_code == 200
    productivity = productivity_response.json()
    assert productivity
    assert {"pic", "work_month", "total_point", "case_count", "grade"}.issubset(
        productivity[0]
    )

    low_margin_response = client.get("/api/dashboard/low-margin")
    assert low_margin_response.status_code == 200
    low_margin = low_margin_response.json()
    assert any(item["decision"] == "CEO_REVIEW" for item in low_margin)

    work_month = summary["start_date"][:7]
    month_summary_response = client.get(
        "/api/dashboard/summary",
        params={"work_month": work_month},
    )
    assert month_summary_response.status_code == 200
    month_summary = month_summary_response.json()
    assert month_summary["period_label"] == work_month

    monthly_response = client.get(
        "/api/dashboard/monthly-performance",
        params={"start_month": "2026-01", "end_month": "2026-12"},
    )
    assert monthly_response.status_code == 200
    monthly = monthly_response.json()
    assert monthly
    assert {"work_month", "case_count", "conditional_count"}.issubset(monthly[0])

    productivity_monthly_response = client.get(
        "/api/dashboard/productivity/monthly",
        params={"start_month": "2026-01", "end_month": "2026-12"},
    )
    assert productivity_monthly_response.status_code == 200
    productivity_monthly = productivity_monthly_response.json()
    assert productivity_monthly
    assert {"work_month", "pic", "total_point", "grade"}.issubset(
        productivity_monthly[0]
    )

    low_margin_month_response = client.get(
        "/api/dashboard/low-margin",
        params={"work_month": work_month},
    )
    assert low_margin_month_response.status_code == 200


def test_dashboard_productivity_can_filter_by_month() -> None:
    client = TestClient(app)
    save_response = client.post(
        "/api/approvals/analyze-sample-and-save/KANGKOKU_HIROBA_SI_PLUS_PLUS"
    )
    assert save_response.status_code == 200

    all_response = client.get("/api/dashboard/productivity")
    assert all_response.status_code == 200
    work_month = all_response.json()[0]["work_month"]

    filtered_response = client.get(
        "/api/dashboard/productivity",
        params={"work_month": work_month},
    )
    assert filtered_response.status_code == 200
    assert all(item["work_month"] == work_month for item in filtered_response.json())
