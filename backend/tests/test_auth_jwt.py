from fastapi.testclient import TestClient

from app.main import app


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == username
    return data["access_token"]


def test_login_me_workflow_authorization_and_password_change() -> None:
    with TestClient(app) as client:
        seed_response = client.post("/api/masters/seed-defaults")
        assert seed_response.status_code == 200

        admin_token = _login(client, "admin", "admin1234")
        staff_token = _login(client, "staff", "staff1234")
        team_token = _login(client, "team_manager", "manager1234")

        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["role"] == "ADMIN"

        save_response = client.post(
            "/api/approvals/analyze-sample-and-save/HUMAN_MADE_SE_PLUS_PLUS",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert save_response.status_code == 200
        approval_case_id = save_response.json()["approval_case_id"]
        workflows = client.get("/api/workflows").json()
        workflow = next(item for item in workflows if item["approval_case_id"] == approval_case_id)

        submit_response = client.post(
            f"/api/workflows/{workflow['workflow_id']}/submit",
            headers={"Authorization": f"Bearer {staff_token}"},
            json={"request_comment": "submit"},
        )
        assert submit_response.status_code == 200

        staff_approve_response = client.post(
            f"/api/workflows/{workflow['workflow_id']}/team-approve",
            headers={"Authorization": f"Bearer {staff_token}"},
            json={"comment": "approve"},
        )
        assert staff_approve_response.status_code == 403

        team_approve_response = client.post(
            f"/api/workflows/{workflow['workflow_id']}/team-approve",
            headers={"Authorization": f"Bearer {team_token}"},
            json={"comment": "approve"},
        )
        assert team_approve_response.status_code == 200

        change_response = client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"current_password": "admin1234", "new_password": "newpassword123"},
        )
        assert change_response.status_code == 200

        old_login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin1234"},
        )
        assert old_login_response.status_code == 401

        new_login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "newpassword123"},
        )
        assert new_login_response.status_code == 200
