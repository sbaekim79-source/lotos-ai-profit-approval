from fastapi.testclient import TestClient

from app.main import app


def _quote_payload() -> dict[str, object]:
    return {
        "customer_name": "TEST CUSTOMER",
        "trade_type": "SHIPPER",
        "partner_name": None,
        "mode": "SEA",
        "direction": "IMPORT",
        "code": "SI++",
        "pol": "BUSAN",
        "pod": "TOKYO",
        "port": "TOKYO",
        "origin": "BUSAN",
        "destination": "TOKYO",
        "container_type": "20DC",
        "container_count": 1,
        "include_customs": True,
        "include_transport": True,
    }


def test_generate_quote_uses_tariff_and_master_rules() -> None:
    with TestClient(app) as client:
        seed_response = client.post("/api/masters/seed-defaults")
        assert seed_response.status_code == 200

        save_response = client.post(
            "/api/approvals/analyze-sample-and-save/TOWA_SI_PLUS_PLUS"
        )
        assert save_response.status_code == 200

        quote_response = client.post("/api/quotes/generate", json=_quote_payload())

        assert quote_response.status_code == 200
        quote = quote_response.json()
        assert quote["code"] == "SI++"
        assert quote["minimum_gp_jpy"] == 30800
        assert quote["target_gp_rate"] == 0.15
        assert quote["total_recommended_revenue_jpy"] >= quote["total_estimated_cost_jpy"]
        assert quote["expected_gp_jpy"] >= quote["minimum_gp_jpy"]
        assert any(item["category"] == "TRANSPORT" for item in quote["items"])
        assert any(item["category"] == "CUSTOMS" for item in quote["items"])


def test_generate_and_save_quote_lists_and_returns_detail() -> None:
    with TestClient(app) as client:
        client.post("/api/masters/seed-defaults")
        client.post("/api/approvals/analyze-sample-and-save/TOWA_SI_PLUS_PLUS")

        save_response = client.post(
            "/api/quotes/generate-and-save",
            json=_quote_payload(),
        )

        assert save_response.status_code == 200
        saved = save_response.json()
        quote_case_id = saved["quote_case_id"]
        assert quote_case_id > 0
        assert saved["result"]["decision_hint"] in {"QUOTABLE", "NEED_REVIEW"}

        list_response = client.get("/api/quotes")
        assert list_response.status_code == 200
        assert any(item["id"] == quote_case_id for item in list_response.json())

        detail_response = client.get(f"/api/quotes/{quote_case_id}")
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["id"] == quote_case_id
        assert detail["container_type"] == "20DC"
        assert len(detail["items"]) >= 2


def test_generate_quote_partner_fee_master_usd_conversion() -> None:
    with TestClient(app) as client:
        client.post("/api/masters/seed-defaults")

        payload = {
            **_quote_payload(),
            "trade_type": "PARTNER",
            "partner_name": "PNS NETWORKS",
            "direction": "EXPORT",
            "code": "SE",
            "container_type": "40HC",
            "include_customs": False,
            "include_transport": False,
        }
        response = client.post("/api/quotes/generate", json=payload)

        assert response.status_code == 200
        result = response.json()
        partner_fee_items = [
            item for item in result["items"] if item["category"] == "PARTNER_FEE"
        ]
        assert partner_fee_items
        assert partner_fee_items[0]["source"] == "MASTER"
        assert partner_fee_items[0]["recommended_revenue_jpy"] == 2400
