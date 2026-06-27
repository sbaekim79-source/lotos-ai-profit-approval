from fastapi.testclient import TestClient

from app.main import app


def test_seed_defaults_and_list_master_rules() -> None:
    client = TestClient(app)

    seed_response = client.post("/api/masters/seed-defaults")
    assert seed_response.status_code == 200
    seed_data = seed_response.json()
    assert seed_data["minimum_gp_rules_upserted"] == 16

    minimum_gp_response = client.get("/api/masters/minimum-gp")
    assert minimum_gp_response.status_code == 200
    minimum_gp_rules = minimum_gp_response.json()
    assert len(minimum_gp_rules) >= 16
    assert any(
        rule["code"] == "SI++" and rule["minimum_gp_jpy"] == 30800
        for rule in minimum_gp_rules
    )

    partner_fee_response = client.get("/api/masters/partner-fees")
    assert partner_fee_response.status_code == 200
    partner_fee_rules = partner_fee_response.json()
    assert len(partner_fee_rules) >= 10
    assert any(
        rule["partner_name"] == "PNS NETWORKS" and rule["amount"] == 15
        for rule in partner_fee_rules
    )


def test_create_and_filter_partner_fee_rule() -> None:
    client = TestClient(app)

    create_response = client.post(
        "/api/masters/partner-fees",
        json={
            "partner_name": "TEST PARTNER",
            "mode": "SEA",
            "direction": "EXPORT",
            "container_type": "20DC",
            "unit_type": "CNTR",
            "currency": "USD",
            "amount": 12,
            "settlement_direction": "LOTOS_COLLECT",
            "special_condition": None,
            "valid_from": None,
            "valid_to": None,
            "is_active": True,
            "note": "test rule",
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["partner_name"] == "TEST PARTNER"

    list_response = client.get(
        "/api/masters/partner-fees",
        params={"partner_name": "TEST", "is_active": True},
    )
    assert list_response.status_code == 200
    assert any(rule["id"] == created["id"] for rule in list_response.json())


def test_upsert_minimum_gp_rule() -> None:
    client = TestClient(app)

    create_response = client.post(
        "/api/masters/minimum-gp",
        json={
            "code": "TEST",
            "minimum_gp_jpy": 1000,
            "description": "first",
            "is_active": True,
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()

    update_response = client.post(
        "/api/masters/minimum-gp",
        json={
            "code": "TEST",
            "minimum_gp_jpy": 2000,
            "description": "updated",
            "is_active": False,
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["id"] == created["id"]
    assert updated["minimum_gp_jpy"] == 2000
    assert updated["is_active"] is False


def test_db_minimum_gp_rule_changes_saved_approval_decision() -> None:
    client = TestClient(app)

    seed_response = client.post("/api/masters/seed-defaults")
    assert seed_response.status_code == 200

    approved_response = client.post(
        "/api/approvals/analyze-sample-and-save/KANGKOKU_HIROBA_SI_PLUS_PLUS"
    )
    assert approved_response.status_code == 200
    assert approved_response.json()["result"]["decision"] == "APPROVED"

    update_response = client.post(
        "/api/masters/minimum-gp",
        json={
            "code": "SI++",
            "minimum_gp_jpy": 200000,
            "description": "test override",
            "is_active": True,
        },
    )
    assert update_response.status_code == 200

    reviewed_response = client.post(
        "/api/approvals/analyze-sample-and-save/KANGKOKU_HIROBA_SI_PLUS_PLUS"
    )
    assert reviewed_response.status_code == 200
    result = reviewed_response.json()["result"]
    assert result["minimum_gp_jpy"] == 200000
    assert result["decision"] in {"CEO_REVIEW", "CONDITIONAL_APPROVED"}
    assert any(
        finding["category"] == "Minimum GP" and finding["status"] == "NG"
        for finding in result["findings"]
    )


def test_update_work_code_rule_changes_productivity_point() -> None:
    client = TestClient(app)

    seed_response = client.post("/api/masters/seed-defaults")
    assert seed_response.status_code == 200

    rules_response = client.get("/api/masters/work-code-rules")
    assert rules_response.status_code == 200
    se_plus_plus = next(
        rule for rule in rules_response.json() if rule["code"] == "SE++"
    )

    update_payload = {
        **{key: se_plus_plus[key] for key in [
            "code",
            "name",
            "mode",
            "direction",
            "has_customs",
            "has_transport",
            "has_work",
            "description",
            "is_active",
        ]},
        "point": 2.2,
    }
    update_response = client.put(
        f"/api/masters/work-code-rules/{se_plus_plus['id']}",
        json=update_payload,
    )
    assert update_response.status_code == 200
    assert update_response.json()["point"] == 2.2

    save_response = client.post(
        "/api/approvals/analyze-sample-and-save/HUMAN_MADE_SE_PLUS_PLUS"
    )
    assert save_response.status_code == 200
    saved = save_response.json()
    assert saved["result"]["code"] == "SE++"
    assert saved["result"]["point"] == 2.2

    productivity_response = client.get("/api/dashboard/productivity")
    assert productivity_response.status_code == 200
    assert any(
        row["pic"] == "J.W.PARK" and row["total_point"] >= 2.2
        for row in productivity_response.json()
    )


def test_work_code_rule_validation_and_deactivate() -> None:
    client = TestClient(app)
    client.post("/api/masters/seed-defaults")

    invalid_response = client.post(
        "/api/masters/work-code-rules",
        json={
            "code": "BAD",
            "name": "Bad",
            "mode": "SEA",
            "direction": "EXPORT",
            "has_customs": False,
            "has_transport": False,
            "has_work": False,
            "point": 1,
            "description": None,
            "is_active": True,
        },
    )
    assert invalid_response.status_code == 400

    rules = client.get("/api/masters/work-code-rules").json()
    pjt_rule = next(rule for rule in rules if rule["code"] == "PJT")
    delete_response = client.delete(f"/api/masters/work-code-rules/{pjt_rule['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json()["is_active"] is False


def test_required_charge_rules_seed_and_list() -> None:
    client = TestClient(app)

    seed_response = client.post("/api/masters/seed-defaults")
    assert seed_response.status_code == 200
    assert seed_response.json()["required_charge_rules_upserted"] >= 1

    rules_response = client.get("/api/masters/required-charge-rules")
    assert rules_response.status_code == 200
    rules = rules_response.json()
    assert any(rule["code"] == "SI++" and rule["charge_name"] == "D/O" for rule in rules)
    assert any(rule["charge_name"] == "FOOD_DECLARATION" for rule in rules)


def test_parser_templates_seed_list_update_and_deactivate() -> None:
    client = TestClient(app)

    seed_response = client.post("/api/masters/seed-defaults")
    assert seed_response.status_code == 200
    assert seed_response.json()["parser_templates_upserted"] >= 4

    list_response = client.get("/api/masters/parser-templates")
    assert list_response.status_code == 200
    templates = list_response.json()
    assert any(template["template_name"] == "LOTOS_STANDARD_PDF" for template in templates)
    import_template = next(
        template for template in templates if template["template_name"] == "LOTOS_IMPORT_PDF"
    )

    update_payload = {
        **{key: import_template[key] for key in [
            "template_name",
            "description",
            "mode",
            "direction",
            "file_type",
            "customer_keyword",
            "partner_keyword",
            "revenue_section_keywords",
            "expense_section_keywords",
            "profit_keywords",
            "duty_keywords",
            "consumption_tax_keywords",
            "transport_keywords",
            "customs_keywords",
            "partner_fee_keywords",
            "food_keywords",
            "is_default",
            "is_active",
        ]},
        "description": "updated import template",
    }
    update_response = client.put(
        f"/api/masters/parser-templates/{import_template['id']}",
        json=update_payload,
    )
    assert update_response.status_code == 200
    assert update_response.json()["description"] == "updated import template"

    delete_response = client.delete(
        f"/api/masters/parser-templates/{import_template['id']}"
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["is_active"] is False


def test_required_charge_rule_warns_missing_do_for_si_plus_plus() -> None:
    client = TestClient(app)
    client.post("/api/masters/seed-defaults")

    response = client.post(
        "/api/approvals/analyze-and-save",
        json={
            "customer_name": "TEST SI++",
            "trade_type": "SHIPPER",
            "mode": "SEA",
            "direction": "IMPORT",
            "has_customs": True,
            "has_transport": True,
            "pol": "BUSAN",
            "pod": "TOKYO",
            "port": "TOKYO",
            "container_count": 1,
            "revenue_items": [
                {"name": "TOTAL", "amount_jpy": 500000},
                {"name": "THC", "amount_jpy": 1},
                {"name": "DOC", "amount_jpy": 1},
                {"name": "CUSTOMS", "amount_jpy": 1},
                {"name": "DUTY", "amount_jpy": 1},
                {"name": "CONSUMPTION TAX", "amount_jpy": 1},
                {"name": "TRANSPORT", "amount_jpy": 1},
            ],
            "expense_items": [{"name": "TOTAL", "amount_jpy": 300000}],
            "customs_duty_jpy": 0,
            "consumption_tax_jpy": 0,
            "transport_revenue_jpy": 50000,
            "transport_expense_jpy": 40000,
            "customs_revenue_jpy": 11800,
            "customs_expense_jpy": 0,
        },
    )

    assert response.status_code == 200
    findings = response.json()["result"]["findings"]
    assert any(
        finding["category"] == "비용누락"
        and finding["status"] == "WARN"
        and "D/O" in finding["message"]
        for finding in findings
    )


def test_required_charge_rule_warns_missing_food_declaration() -> None:
    client = TestClient(app)
    client.post("/api/masters/seed-defaults")

    response = client.post(
        "/api/approvals/analyze-and-save",
        json={
            "customer_name": "TEST FROZEN",
            "trade_type": "SHIPPER",
            "mode": "SEA",
            "direction": "EXPORT",
            "has_customs": False,
            "has_transport": False,
            "cargo_description": "FROZEN FOOD",
            "pol": "TOKYO",
            "pod": "BUSAN",
            "port": "TOKYO",
            "container_count": 1,
            "revenue_items": [
                {"name": "TOTAL", "amount_jpy": 200000},
                {"name": "THC", "amount_jpy": 1},
                {"name": "DOC", "amount_jpy": 1},
                {"name": "B/L", "amount_jpy": 1},
                {"name": "AFR", "amount_jpy": 1},
            ],
            "expense_items": [{"name": "TOTAL", "amount_jpy": 100000}],
        },
    )

    assert response.status_code == 200
    findings = response.json()["result"]["findings"]
    assert any(
        finding["category"] == "비용누락"
        and finding["status"] == "WARN"
        and "FOOD_DECLARATION" in finding["message"]
        for finding in findings
    )


def _internal_resource_case(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "customer_name": "INTERNAL RESOURCE TEST",
        "trade_type": "SHIPPER",
        "mode": "SEA",
        "direction": "IMPORT",
        "has_customs": True,
        "has_transport": False,
        "has_work": False,
        "pol": "BUSAN",
        "pod": "TOKYO",
        "port": "TOKYO",
        "container_count": 1,
        "revenue_items": [
            {"name": "TOTAL", "amount_jpy": 200000},
            {"name": "THC", "amount_jpy": 1},
            {"name": "DOC", "amount_jpy": 1},
            {"name": "D/O", "amount_jpy": 1},
            {"name": "DUTY", "amount_jpy": 1},
            {"name": "CONSUMPTION TAX", "amount_jpy": 1},
            {"name": "CUSTOMS", "amount_jpy": 1},
        ],
        "expense_items": [{"name": "TOTAL", "amount_jpy": 100000}],
        "customs_revenue_jpy": 11800,
        "customs_expense_jpy": 0,
        "self_customs": True,
    }
    data.update(overrides)
    return data


def test_internal_resource_customs_self_customs_ok() -> None:
    client = TestClient(app)
    client.post("/api/masters/seed-defaults")

    response = client.post(
        "/api/approvals/analyze-and-save",
        json=_internal_resource_case(self_customs=True),
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert any(
        finding["category"] == "자사자원" and finding["status"] == "OK"
        for finding in result["findings"]
    )


def test_internal_resource_customs_external_without_reason_is_ceo_review() -> None:
    client = TestClient(app)
    client.post("/api/masters/seed-defaults")

    response = client.post(
        "/api/approvals/analyze-and-save",
        json=_internal_resource_case(
            self_customs=False,
            customs_vendor_name="OUTSIDE CUSTOMS",
            external_customs_reason=None,
        ),
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["decision"] == "CEO_REVIEW"
    assert any(
        finding["category"] == "자사자원" and finding["status"] == "NG"
        for finding in result["findings"]
    )


def test_internal_resource_customs_external_with_reason_is_conditional() -> None:
    client = TestClient(app)
    client.post("/api/masters/seed-defaults")

    response = client.post(
        "/api/approvals/analyze-and-save",
        json=_internal_resource_case(
            self_customs=False,
            customs_vendor_name="OUTSIDE CUSTOMS",
            external_customs_reason="temporary capacity shortage",
        ),
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["decision"] == "CONDITIONAL_APPROVED"
    assert any(
        finding["category"] == "자사자원" and finding["status"] == "WARN"
        for finding in result["findings"]
    )


def test_internal_resource_warehouse_external_without_reason_is_ng() -> None:
    client = TestClient(app)
    client.post("/api/masters/seed-defaults")

    response = client.post(
        "/api/approvals/analyze-and-save",
        json=_internal_resource_case(
            direction="EXPORT",
            has_customs=False,
            has_work=True,
            port="HAKATA",
            pod="BUSAN",
            warehouse_vendor_name="OUTSIDE WAREHOUSE",
            external_warehouse_reason=None,
            customs_revenue_jpy=0,
        ),
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert any(
        finding["category"] == "자사자원"
        and finding["status"] == "NG"
        and "외부창고" in finding["message"]
        for finding in result["findings"]
    )
