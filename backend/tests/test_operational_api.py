from io import BytesIO

from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.main import app


def _profit_sheet_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Profit"
    sheet.append(["CUSTOMER", "OPER TEST CUSTOMER"])
    sheet.append(["MODE", "SEA EXPORT B/L POL BUSAN POD TOKYO"])
    sheet.append(["CONTAINER", "40HC x 1"])
    sheet.append(["REVENUE"])
    sheet.append(["TRUCKING", "JPY 61,000"])
    sheet.append(["CUSTOMS", "11,800"])
    sheet.append(["TOTAL REVENUE", "150,000"])
    sheet.append(["EXPENSE"])
    sheet.append(["TRUCKING COST", "50,000"])
    sheet.append(["TOTAL EXPENSE", "100,000"])
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def test_operational_api_flow() -> None:
    client = TestClient(app)

    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/api/db/status").json() == {"database": "ok"}

    seed_response = client.post("/api/masters/seed-defaults")
    assert seed_response.status_code == 200
    assert client.get("/api/masters/partner-fees").status_code == 200
    assert client.get("/api/masters/minimum-gp").status_code == 200
    assert client.get("/api/masters/gp-rate-rules").status_code == 200
    assert client.get("/api/masters/work-code-rules").status_code == 200
    assert client.get("/api/masters/internal-resource-rules").status_code == 200

    upload_response = client.post(
        "/api/uploads/profit-sheet",
        files={
            "file": (
                "oper_profit.xlsx",
                _profit_sheet_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert upload_response.status_code == 200
    upload_id = upload_response.json()["upload_id"]

    parse_response = client.post(f"/api/uploads/{upload_id}/parse")
    assert parse_response.status_code == 200
    assert parse_response.json()["parse_result"]["status"] == "parsed"

    map_response = client.post(f"/api/uploads/{upload_id}/map-to-case")
    assert map_response.status_code == 200
    candidate = map_response.json()["candidate"]
    assert candidate["customer_name"] == "OPER TEST CUSTOMER"

    analyze_upload_response = client.post(f"/api/uploads/{upload_id}/analyze")
    assert analyze_upload_response.status_code == 200
    assert analyze_upload_response.json()["code"] == "SE++"

    save_upload_response = client.post(f"/api/uploads/{upload_id}/analyze-and-save")
    assert save_upload_response.status_code == 200
    approval_case_id = save_upload_response.json()["approval_case_id"]

    approvals_response = client.get("/api/approvals")
    assert approvals_response.status_code == 200
    assert any(item["id"] == approval_case_id for item in approvals_response.json())

    detail_response = client.get(f"/api/approvals/{approval_case_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == approval_case_id

    report_response = client.get(f"/api/approvals/{approval_case_id}/report")
    assert report_response.status_code == 200
    assert "# LOTOS AI 결재심사서" in report_response.text

    edited_response = client.post("/api/approvals/analyze", json=candidate)
    assert edited_response.status_code == 200

    edited_save_response = client.post("/api/approvals/analyze-and-save", json=candidate)
    assert edited_save_response.status_code == 200

    assert client.get("/api/dashboard/summary").status_code == 200
    assert client.get("/api/dashboard/monthly").status_code == 200
    assert client.get("/api/dashboard/productivity").status_code == 200
    assert client.get("/api/dashboard/low-margin").status_code == 200

    assert client.get("/api/tariffs/transport").status_code == 200
    assert client.get("/api/tariffs/transport/summary").status_code == 200
    assert client.get("/api/tariffs/customs").status_code == 200
    assert client.get("/api/tariffs/customs/summary").status_code == 200
