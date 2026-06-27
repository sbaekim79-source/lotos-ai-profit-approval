from pathlib import Path

from fastapi.testclient import TestClient

from app.logging_config import APP_LOG_PATH, ERROR_LOG_PATH
from app.main import app


ADMIN_HEADERS = {"X-USER-NAME": "admin"}
STAFF_HEADERS = {"X-USER-NAME": "staff"}
TEAM_HEADERS = {"X-USER-NAME": "team_manager"}


def test_admin_status_backup_and_audit_logs() -> None:
    with TestClient(app) as client:
        seed_response = client.post("/api/masters/seed-defaults", headers=ADMIN_HEADERS)
        assert seed_response.status_code == 200

        status_response = client.get("/api/admin/system-status", headers=ADMIN_HEADERS)
        assert status_response.status_code == 200
        status = status_response.json()
        assert status["database"] == "ok"
        assert status["database_type"] in {"sqlite", "postgresql"}
        assert "database_url_masked" in status
        assert "app_env" in status
        assert status["logs_folder_exists"] is True
        assert "approval_case_count" in status

        forbidden_response = client.post("/api/admin/backup-db", headers=STAFF_HEADERS)
        assert forbidden_response.status_code == 403

        backup_response = client.post("/api/admin/backup-db", headers=ADMIN_HEADERS)
        assert backup_response.status_code == 200
        backup_path = Path(backup_response.json()["backup_file"])
        assert backup_path.exists()

        backups_response = client.get("/api/admin/backups", headers=ADMIN_HEADERS)
        assert backups_response.status_code == 200
        assert any(item["file_name"] == backup_path.name for item in backups_response.json())

        save_response = client.post(
            "/api/approvals/analyze-sample-and-save/KANGKOKU_HIROBA_SI_PLUS_PLUS",
            headers=STAFF_HEADERS,
        )
        assert save_response.status_code == 200
        approval_case_id = save_response.json()["approval_case_id"]
        workflow = next(
            item
            for item in client.get("/api/workflows").json()
            if item["approval_case_id"] == approval_case_id
        )
        submit_response = client.post(
            f"/api/workflows/{workflow['workflow_id']}/submit",
            headers=STAFF_HEADERS,
            json={"request_comment": "상신"},
        )
        assert submit_response.status_code == 200
        approve_response = client.post(
            f"/api/workflows/{workflow['workflow_id']}/team-approve",
            headers=TEAM_HEADERS,
            json={"comment": "승인"},
        )
        assert approve_response.status_code == 200

        audit_response = client.get("/api/audit-logs", params={"entity_type": "APPROVAL_WORKFLOW"})
        assert audit_response.status_code == 200
        actions = {item["action"] for item in audit_response.json()}
        assert "WORKFLOW_SUBMIT" in actions
        assert "WORKFLOW_TEAM_APPROVE" in actions

        client.get("/health")
        assert APP_LOG_PATH.exists()
        assert ERROR_LOG_PATH.exists()
