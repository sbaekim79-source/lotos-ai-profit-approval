from fastapi.testclient import TestClient

from app.main import app


def _headers(username: str) -> dict[str, str]:
    return {"X-USER-NAME": username}


def _create_approval_case(client: TestClient) -> int:
    seed_response = client.post("/api/masters/seed-defaults")
    assert seed_response.status_code == 200
    save_response = client.post(
        "/api/approvals/analyze-sample-and-save/KANGKOKU_HIROBA_SI_PLUS_PLUS"
    )
    assert save_response.status_code == 200
    return save_response.json()["approval_case_id"]


def test_create_and_download_summary_pdf_report() -> None:
    with TestClient(app) as client:
        approval_case_id = _create_approval_case(client)

        workflows = client.get("/api/workflows").json()
        workflow = next(
            item
            for item in workflows
            if item["approval_case_id"] == approval_case_id
        )
        submit_response = client.post(
            f"/api/workflows/{workflow['workflow_id']}/submit",
            headers=_headers("staff"),
            json={"request_comment": "결재 요청"},
        )
        assert submit_response.status_code == 200

        create_response = client.post(
            f"/api/approvals/{approval_case_id}/report/pdf",
            params={"report_type": "SUMMARY"},
            headers=_headers("team_manager"),
        )
        assert create_response.status_code == 200
        payload = create_response.json()
        assert payload["report_type"] == "SUMMARY"
        assert payload["download_url"].startswith("/api/reports/files/")

        list_response = client.get(f"/api/approvals/{approval_case_id}/report/files")
        assert list_response.status_code == 200
        assert any(
            item["report_file_id"] == payload["report_file_id"]
            for item in list_response.json()
        )

        download_response = client.get(payload["download_url"])
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/pdf"
        assert download_response.content.startswith(b"%PDF")


def test_staff_cannot_create_detail_pdf_report() -> None:
    with TestClient(app) as client:
        approval_case_id = _create_approval_case(client)
        response = client.post(
            f"/api/approvals/{approval_case_id}/report/pdf",
            params={"report_type": "DETAIL"},
            headers=_headers("staff"),
        )
        assert response.status_code == 403
