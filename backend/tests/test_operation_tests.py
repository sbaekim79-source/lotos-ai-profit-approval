from fastapi.testclient import TestClient

from app.main import app


def test_operation_test_result_crud_flow() -> None:
    with TestClient(app) as client:
        payload = {
            "test_case_id": "TC-001",
            "test_name": "Health Check",
            "tester": "QA",
            "result": "PASS",
            "issue": None,
            "action_taken": None,
            "tested_at": "2026-06-26T10:00:00",
        }
        create_response = client.post(
            "/api/operation-tests",
            json=payload,
            headers={"X-USER-NAME": "admin"},
        )
        assert create_response.status_code == 200
        created = create_response.json()
        assert created["test_case_id"] == "TC-001"
        assert created["result"] == "PASS"

        list_response = client.get("/api/operation-tests", params={"result": "PASS"})
        assert list_response.status_code == 200
        assert any(item["id"] == created["id"] for item in list_response.json())

        update_payload = {
            **payload,
            "result": "FAIL",
            "issue": "temporary issue",
            "action_taken": "retry required",
        }
        update_response = client.put(
            f"/api/operation-tests/{created['id']}",
            json=update_payload,
            headers={"X-USER-NAME": "admin"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["result"] == "FAIL"

        hold_response = client.delete(
            f"/api/operation-tests/{created['id']}",
            headers={"X-USER-NAME": "admin"},
        )
        assert hold_response.status_code == 200
        assert hold_response.json()["result"] == "HOLD"

        audit_response = client.get(
            "/api/audit-logs",
            params={"entity_type": "OPERATION_TEST_RESULT"},
        )
        assert audit_response.status_code == 200
        actions = {item["action"] for item in audit_response.json()}
        assert "CREATE_OPERATION_TEST_RESULT" in actions
        assert "UPDATE_OPERATION_TEST_RESULT" in actions
        assert "HOLD_OPERATION_TEST_RESULT" in actions
