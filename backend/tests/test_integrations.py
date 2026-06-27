import json

from fastapi.testclient import TestClient

from app.main import app


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_integration_payload_export_download_and_logs() -> None:
    with TestClient(app) as client:
        assert client.post("/api/masters/seed-defaults").status_code == 200
        admin_token = _login(client, "admin", "admin1234")
        staff_token = _login(client, "staff", "staff1234")

        save_response = client.post(
            "/api/approvals/analyze-sample-and-save/KANGKOKU_HIROBA_SI_PLUS_PLUS",
            headers=_auth(admin_token),
        )
        assert save_response.status_code == 200
        approval_case_id = save_response.json()["approval_case_id"]

        setting_response = client.post(
            "/api/integrations/settings",
            headers=_auth(admin_token),
            json={
                "integration_name": "ERP",
                "integration_type": "FILE_EXPORT",
                "endpoint_url": None,
                "export_format": "JSON",
                "is_active": True,
                "description": "ERP JSON export",
            },
        )
        assert setting_response.status_code == 200
        assert setting_response.json()["integration_name"] == "ERP"

        forbidden_response = client.get(
            f"/api/integrations/approval/{approval_case_id}/payload",
            headers=_auth(staff_token),
        )
        assert forbidden_response.status_code == 403

        payload_response = client.get(
            f"/api/integrations/approval/{approval_case_id}/payload",
            headers=_auth(admin_token),
        )
        assert payload_response.status_code == 200
        payload = payload_response.json()
        assert payload["approval_case_id"] == approval_case_id
        assert payload["customer_name"] == "KANGKOKU HIROBA"
        assert payload["workflow_status"] == "DRAFT"
        assert payload["findings"]

        export_response = client.post(
            f"/api/integrations/export/approval/{approval_case_id}",
            headers=_auth(admin_token),
            json={"integration_name": "ERP", "export_format": "JSON"},
        )
        assert export_response.status_code == 200
        export_payload = export_response.json()
        assert export_payload["status"] == "SUCCESS"
        assert export_payload["file_name"].endswith(".json")
        assert export_payload["download_url"]

        download_response = client.get(
            export_payload["download_url"],
            headers=_auth(admin_token),
        )
        assert download_response.status_code == 200
        downloaded_payload = json.loads(download_response.content.decode("utf-8"))
        assert downloaded_payload["approval_case_id"] == approval_case_id

        logs_response = client.get(
            "/api/integrations/logs",
            headers=_auth(admin_token),
            params={"entity_type": "APPROVAL"},
        )
        assert logs_response.status_code == 200
        logs = logs_response.json()
        assert any(log["id"] == export_payload["log_id"] for log in logs)

        audit_response = client.get(
            "/api/audit-logs",
            params={"action": "INTEGRATION_EXPORT", "entity_type": "APPROVAL"},
        )
        assert audit_response.status_code == 200
        assert audit_response.json()


def test_webhook_integration_is_pending_without_external_send() -> None:
    with TestClient(app) as client:
        assert client.post("/api/masters/seed-defaults").status_code == 200
        admin_token = _login(client, "admin", "admin1234")
        save_response = client.post(
            "/api/approvals/analyze-sample-and-save/HUMAN_MADE_SE_PLUS_PLUS",
            headers=_auth(admin_token),
        )
        approval_case_id = save_response.json()["approval_case_id"]

        setting_response = client.post(
            "/api/integrations/settings",
            headers=_auth(admin_token),
            json={
                "integration_name": "GROUPWARE",
                "integration_type": "WEBHOOK",
                "endpoint_url": "https://example.invalid/webhook",
                "export_format": "JSON",
                "is_active": True,
                "description": "Webhook placeholder",
            },
        )
        assert setting_response.status_code == 200

        export_response = client.post(
            f"/api/integrations/export/approval/{approval_case_id}",
            headers=_auth(admin_token),
            json={"integration_name": "GROUPWARE", "export_format": "JSON"},
        )
        assert export_response.status_code == 200
        payload = export_response.json()
        assert payload["status"] == "PENDING"
        assert payload["download_url"] is None
