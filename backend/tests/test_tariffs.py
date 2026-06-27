from fastapi.testclient import TestClient

from app.main import app


def save_tariff_samples(client: TestClient) -> None:
    for sample_key in (
        "TOWA_SI_PLUS_PLUS",
        "KANGKOKU_HIROBA_SI_PLUS_PLUS",
        "HUMAN_MADE_SE_PLUS_PLUS",
    ):
        response = client.post(f"/api/approvals/analyze-sample-and-save/{sample_key}")
        assert response.status_code == 200


def test_transport_tariff_list_and_summary() -> None:
    client = TestClient(app)
    save_tariff_samples(client)

    list_response = client.get("/api/tariffs/transport")
    assert list_response.status_code == 200
    transport_tariffs = list_response.json()
    assert transport_tariffs
    assert {
        "id",
        "approval_case_id",
        "port",
        "origin",
        "destination",
        "container_type",
        "transport_cost_jpy",
        "transport_revenue_jpy",
        "transport_gp_jpy",
        "created_at",
    }.issubset(transport_tariffs[0])

    filtered_response = client.get(
        "/api/tariffs/transport",
        params={"port": "TOKYO", "origin": "BUSAN"},
    )
    assert filtered_response.status_code == 200
    assert filtered_response.json()

    summary_response = client.get("/api/tariffs/transport/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary
    assert {
        "origin",
        "destination",
        "container_type",
        "case_count",
        "avg_transport_cost_jpy",
        "min_transport_cost_jpy",
        "max_transport_cost_jpy",
        "avg_transport_revenue_jpy",
        "avg_transport_gp_jpy",
    }.issubset(summary[0])


def test_customs_tariff_list_summary_and_warehouse_placeholder() -> None:
    client = TestClient(app)
    save_tariff_samples(client)

    list_response = client.get("/api/tariffs/customs")
    assert list_response.status_code == 200
    customs_tariffs = list_response.json()
    assert customs_tariffs
    assert {
        "id",
        "approval_case_id",
        "port",
        "direction",
        "self_customs",
        "customs_revenue_jpy",
        "customs_expense_jpy",
        "customs_gp_jpy",
        "created_at",
    }.issubset(customs_tariffs[0])

    filtered_response = client.get(
        "/api/tariffs/customs",
        params={"port": "TOKYO", "direction": "IMPORT", "self_customs": True},
    )
    assert filtered_response.status_code == 200
    assert filtered_response.json()

    summary_response = client.get("/api/tariffs/customs/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary
    assert {
        "port",
        "direction",
        "self_customs",
        "case_count",
        "avg_customs_revenue_jpy",
        "avg_customs_expense_jpy",
        "avg_customs_gp_jpy",
        "avg_food_declaration_fee_jpy",
        "avg_inspection_fee_jpy",
    }.issubset(summary[0])

    warehouse_response = client.get("/api/tariffs/warehouse")
    assert warehouse_response.status_code == 200
    assert warehouse_response.json() == {
        "message": "warehouse tariff API will be implemented in next step"
    }
