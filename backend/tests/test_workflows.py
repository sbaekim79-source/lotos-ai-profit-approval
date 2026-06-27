from fastapi.testclient import TestClient

from app.main import app


def _headers(username: str) -> dict[str, str]:
    return {"X-USER-NAME": username}


def _create_workflow(client: TestClient) -> int:
    seed_response = client.post("/api/masters/seed-defaults")
    assert seed_response.status_code == 200

    save_response = client.post(
        "/api/approvals/analyze-sample-and-save/KANGKOKU_HIROBA_SI_PLUS_PLUS"
    )
    assert save_response.status_code == 200
    approval_case_id = save_response.json()["approval_case_id"]

    workflows_response = client.get("/api/workflows")
    assert workflows_response.status_code == 200
    workflow = next(
        item
        for item in workflows_response.json()
        if item["approval_case_id"] == approval_case_id
    )
    assert workflow["current_status"] == "DRAFT"
    return workflow["workflow_id"]


def test_workflow_full_approval_flow_with_roles() -> None:
    with TestClient(app) as client:
        workflow_id = _create_workflow(client)

        submit_response = client.post(
            f"/api/workflows/{workflow_id}/submit",
            headers=_headers("staff"),
            json={"request_comment": "결재 요청드립니다."},
        )
        assert submit_response.status_code == 200
        assert submit_response.json()["current_status"] == "SUBMITTED"
        assert submit_response.json()["requested_by"] == "담당자"

        team_response = client.post(
            f"/api/workflows/{workflow_id}/team-approve",
            headers=_headers("team_manager"),
            json={"comment": "승인합니다."},
        )
        assert team_response.status_code == 200
        assert team_response.json()["current_status"] == "TEAM_APPROVED"
        assert team_response.json()["team_approved_by"] == "팀장"

        director_response = client.post(
            f"/api/workflows/{workflow_id}/director-approve",
            headers=_headers("director"),
            json={"comment": "승인합니다."},
        )
        assert director_response.status_code == 200
        assert director_response.json()["current_status"] == "DIRECTOR_APPROVED"
        assert director_response.json()["director_approved_by"] == "본부장"

        ceo_response = client.post(
            f"/api/workflows/{workflow_id}/ceo-approve",
            headers=_headers("ceo"),
            json={"comment": "최종 승인합니다."},
        )
        assert ceo_response.status_code == 200
        assert ceo_response.json()["current_status"] == "CEO_APPROVED"
        assert ceo_response.json()["ceo_approved_by"] == "대표"

        detail_response = client.get(f"/api/workflows/{workflow_id}")
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["workflow"]["current_status"] == "CEO_APPROVED"
        assert detail["approval_case"]["customer_name"] == "KANGKOKU HIROBA"


def test_workflow_rejects_invalid_transition_even_with_valid_role() -> None:
    with TestClient(app) as client:
        workflow_id = _create_workflow(client)

        ceo_response = client.post(
            f"/api/workflows/{workflow_id}/ceo-approve",
            headers=_headers("ceo"),
            json={"comment": "bad transition"},
        )

        assert ceo_response.status_code == 400


def test_workflow_rejects_unauthorized_role() -> None:
    with TestClient(app) as client:
        workflow_id = _create_workflow(client)

        submit_response = client.post(
            f"/api/workflows/{workflow_id}/submit",
            headers=_headers("staff"),
            json={"request_comment": "상신"},
        )
        assert submit_response.status_code == 200

        forbidden_response = client.post(
            f"/api/workflows/{workflow_id}/team-approve",
            headers=_headers("staff"),
            json={"comment": "권한 없음"},
        )
        assert forbidden_response.status_code == 403


def test_admin_can_run_all_workflow_actions() -> None:
    with TestClient(app) as client:
        workflow_id = _create_workflow(client)

        assert client.post(
            f"/api/workflows/{workflow_id}/submit",
            headers=_headers("admin"),
            json={"request_comment": "admin submit"},
        ).status_code == 200
        assert client.post(
            f"/api/workflows/{workflow_id}/team-approve",
            headers=_headers("admin"),
            json={"comment": "admin team"},
        ).status_code == 200
        assert client.post(
            f"/api/workflows/{workflow_id}/director-approve",
            headers=_headers("admin"),
            json={"comment": "admin director"},
        ).status_code == 200
        ceo_response = client.post(
            f"/api/workflows/{workflow_id}/ceo-approve",
            headers=_headers("admin"),
            json={"comment": "admin ceo"},
        )
        assert ceo_response.status_code == 200
        assert ceo_response.json()["current_status"] == "CEO_APPROVED"


def test_workflow_return_and_resubmit() -> None:
    with TestClient(app) as client:
        workflow_id = _create_workflow(client)

        submit_response = client.post(
            f"/api/workflows/{workflow_id}/submit",
            headers=_headers("staff"),
            json={"request_comment": "상신"},
        )
        assert submit_response.status_code == 200

        return_response = client.post(
            f"/api/workflows/{workflow_id}/return",
            headers=_headers("team_manager"),
            json={"return_reason": "운송마진 재확인 필요"},
        )
        assert return_response.status_code == 200
        assert return_response.json()["current_status"] == "RETURNED"
        assert return_response.json()["returned_by"] == "팀장"

        resubmit_response = client.post(
            f"/api/workflows/{workflow_id}/submit",
            headers=_headers("staff"),
            json={"request_comment": "보완 후 재상신"},
        )
        assert resubmit_response.status_code == 200
        assert resubmit_response.json()["current_status"] == "SUBMITTED"
