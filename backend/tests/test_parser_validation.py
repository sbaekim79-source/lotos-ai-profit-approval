from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.main import app


def _profit_sheet_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Profit"
    sheet.append(["CUSTOMER", "VALIDATION CUSTOMER"])
    sheet.append(["MODE", "SEA EXPORT B/L POL BUSAN POD TOKYO"])
    sheet.append(["CONTAINER", "40HC x 1"])
    sheet.append(["REVENUE"])
    sheet.append(["TRUCKING", "JPY 31,000"])
    sheet.append(["CUSTOMS", "11,800"])
    sheet.append(["TOTAL REVENUE", "120,510"])
    sheet.append(["EXPENSE"])
    sheet.append(["TRUCKING COST", "25,000"])
    sheet.append(["TOTAL EXPENSE", "87,710"])
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def _upload_profit_sheet(client: TestClient) -> str:
    response = client.post(
        "/api/uploads/profit-sheet",
        files={
            "file": (
                "validation_profit.xlsx",
                _profit_sheet_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    return response.json()["upload_id"]


def test_parser_validation_case_and_run_flow() -> None:
    with TestClient(app) as client:
        seed_response = client.post("/api/masters/seed-defaults")
        assert seed_response.status_code == 200
        assert seed_response.json()["parser_validation_cases_upserted"] == 5

        cases_response = client.get("/api/parser-validation/cases")
        assert cases_response.status_code == 200
        assert any(item["case_name"] == "HUMAN_MADE_SE_PLUS_PLUS" for item in cases_response.json())

        upload_id = _upload_profit_sheet(client)
        case_name = f"VALIDATION_TEST_CASE_{uuid4().hex}"
        payload = {
            "case_name": case_name,
            "expected_customer_name": "VALIDATION CUSTOMER",
            "expected_code": "SE++",
            "expected_gp_jpy": 32800,
            "expected_decision": "APPROVED",
            "expected_transport_revenue_jpy": 31000,
            "expected_transport_expense_jpy": 25000,
            "expected_customs_revenue_jpy": 11800,
            "tolerance_jpy": 500,
            "is_active": True,
        }
        create_response = client.post("/api/parser-validation/cases", json=payload)
        assert create_response.status_code == 200
        case_id = create_response.json()["id"]

        run_response = client.post(
            f"/api/parser-validation/cases/{case_id}/run",
            json={"upload_id": upload_id},
        )
        assert run_response.status_code == 200
        result = run_response.json()
        assert result["result"] in {"PASS", "PARTIAL", "FAIL"}
        assert result["parsed_code"] == "SE++"
        assert result["parsed_gp_jpy"] == 32800

        results_response = client.get(
            "/api/parser-validation/results",
            params={"case_id": case_id},
        )
        assert results_response.status_code == 200
        assert any(item["id"] == result["id"] for item in results_response.json())

        updated_payload = {**payload, "expected_gp_jpy": 99999}
        update_response = client.put(
            f"/api/parser-validation/cases/{case_id}",
            json=updated_payload,
        )
        assert update_response.status_code == 200
        assert update_response.json()["expected_gp_jpy"] == 99999

        delete_response = client.delete(f"/api/parser-validation/cases/{case_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["is_active"] is False


def test_parser_improvement_suggestions_apply_and_reject() -> None:
    with TestClient(app) as client:
        seed_response = client.post("/api/masters/seed-defaults")
        assert seed_response.status_code == 200

        upload_id = _upload_profit_sheet(client)
        case_name = f"IMPROVEMENT_TEST_CASE_{uuid4().hex}"
        payload = {
            "case_name": case_name,
            "expected_customer_name": "VALIDATION CUSTOMER",
            "expected_code": "SE++",
            "expected_gp_jpy": 32800,
            "expected_decision": "APPROVED",
            "expected_transport_revenue_jpy": 99999,
            "expected_transport_expense_jpy": 25000,
            "expected_customs_revenue_jpy": 99999,
            "tolerance_jpy": 500,
            "is_active": True,
        }
        create_response = client.post("/api/parser-validation/cases", json=payload)
        assert create_response.status_code == 200
        case_id = create_response.json()["id"]

        run_response = client.post(
            f"/api/parser-validation/cases/{case_id}/run",
            json={"upload_id": upload_id},
        )
        assert run_response.status_code == 200
        assert run_response.json()["result"] == "PARTIAL"

        suggestions_response = client.get(
            "/api/parser-improvements/suggestions",
            params={"case_name": case_name},
        )
        assert suggestions_response.status_code == 200
        suggestions = suggestions_response.json()
        transport_suggestion = next(
            item for item in suggestions if item["issue_type"] == "TRANSPORT_MISMATCH"
        )
        customs_suggestion = next(
            item for item in suggestions if item["issue_type"] == "CUSTOMS_MISMATCH"
        )

        templates_before = client.get("/api/masters/parser-templates").json()
        template_before = next(
            item for item in templates_before if item["id"] == transport_suggestion["template_id"]
        )
        before_keywords = template_before["transport_keywords"].split(",")

        apply_response = client.post(
            f"/api/parser-improvements/suggestions/{transport_suggestion['id']}/apply",
            headers={"X-USER-NAME": "admin"},
        )
        assert apply_response.status_code == 200
        assert apply_response.json()["status"] == "APPLIED"

        templates_after = client.get("/api/masters/parser-templates").json()
        template_after = next(
            item for item in templates_after if item["id"] == transport_suggestion["template_id"]
        )
        after_keywords = template_after["transport_keywords"].split(",")
        assert len(after_keywords) == len(set(keyword.upper() for keyword in after_keywords))
        assert set(keyword.upper() for keyword in before_keywords).issubset(
            {keyword.upper() for keyword in after_keywords}
        )

        reject_response = client.post(
            f"/api/parser-improvements/suggestions/{customs_suggestion['id']}/reject",
            headers={"X-USER-NAME": "admin"},
        )
        assert reject_response.status_code == 200
        assert reject_response.json()["status"] == "REJECTED"
