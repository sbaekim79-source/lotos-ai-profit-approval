from fastapi.testclient import TestClient

from app.database import Base, DB_PATH, SessionLocal, engine
from app.main import app
from app.models import (
    ApprovalCase,
    ApprovalFinding,
    CustomsTariff,
    ProductivityPoint,
    TransportTariff,
)
from app.sample_cases import SAMPLE_CASES
from app.services.approval_engine import analyze_case
from app.services.approval_repository import save_approval_case


EXPECTED_TABLES = {
    "approval_cases",
    "approval_findings",
    "partner_fee_rules",
    "minimum_gp_rules",
    "transport_tariffs",
    "customs_tariffs",
    "productivity_points",
    "gp_rate_rules",
    "work_code_rules",
    "internal_resource_rules",
}


def test_db_status_api_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/api/db/status")

    assert response.status_code == 200
    assert response.json() == {"database": "ok"}


def test_database_tables_are_registered_and_created() -> None:
    Base.metadata.create_all(bind=engine)

    assert DB_PATH.exists()
    assert EXPECTED_TABLES.issubset(Base.metadata.tables.keys())


def test_save_approval_case_persists_related_records() -> None:
    Base.metadata.create_all(bind=engine)
    case_input = SAMPLE_CASES["KANGKOKU_HIROBA_SI_PLUS_PLUS"]
    result = analyze_case(case_input)

    db = SessionLocal()
    try:
        approval_case = save_approval_case(db, case_input, result)
        approval_case_id = approval_case.id

        assert db.get(ApprovalCase, approval_case_id) is not None
        assert (
            db.query(ApprovalFinding)
            .filter(ApprovalFinding.approval_case_id == approval_case_id)
            .count()
            == len(result.findings)
        )
        assert (
            db.query(ProductivityPoint)
            .filter(ProductivityPoint.approval_case_id == approval_case_id)
            .count()
            == 1
        )
        assert (
            db.query(TransportTariff)
            .filter(TransportTariff.approval_case_id == approval_case_id)
            .count()
            == 1
        )
        assert (
            db.query(CustomsTariff)
            .filter(CustomsTariff.approval_case_id == approval_case_id)
            .count()
            == 1
        )
    finally:
        db.close()


def test_analyze_sample_and_save_api_can_be_listed_and_retrieved() -> None:
    client = TestClient(app)
    seed_response = client.post("/api/masters/seed-defaults")
    assert seed_response.status_code == 200

    save_response = client.post(
        "/api/approvals/analyze-sample-and-save/KANGKOKU_HIROBA_SI_PLUS_PLUS"
    )

    assert save_response.status_code == 200
    saved = save_response.json()
    approval_case_id = saved["approval_case_id"]
    assert saved["result"]["code"] == "SI++"
    assert saved["result"]["decision"] == "APPROVED"

    list_response = client.get("/api/approvals")
    assert list_response.status_code == 200
    assert any(item["id"] == approval_case_id for item in list_response.json())

    detail_response = client.get(f"/api/approvals/{approval_case_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == approval_case_id
    assert detail["customer_name"] == "KANGKOKU HIROBA"
    assert detail["findings"]

    report_response = client.get(f"/api/approvals/{approval_case_id}/report")
    assert report_response.status_code == 200
    assert "text/markdown" in report_response.headers["content-type"]
    report = report_response.text
    assert "# LOTOS AI 결재심사서" in report
    assert "## 기본정보" in report
    assert "KANGKOKU HIROBA" in report
    assert "## LOTOS 기준 심사" in report
    assert "| 구분 | 상태 | 내용 | 금액 |" in report
    assert "## 최종 결재결과" in report
    assert "APPROVED" in report
