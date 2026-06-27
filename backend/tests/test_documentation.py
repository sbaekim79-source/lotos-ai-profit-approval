from fastapi.testclient import TestClient

from app.main import app


def test_documentation_download_apis() -> None:
    with TestClient(app) as client:
        for path, expected_title in [
            ("/api/docs/user-manual", "LOTOS AI Profit Approval System 사용자 매뉴얼"),
            ("/api/docs/admin-manual", "LOTOS AI Profit Approval System 관리자 매뉴얼"),
            ("/api/docs/training-guide", "LOTOS AI Profit Approval System 교육자료"),
        ]:
            response = client.get(path)
            assert response.status_code == 200
            assert expected_title in response.text
            assert response.headers["content-disposition"].endswith(".md\"")
