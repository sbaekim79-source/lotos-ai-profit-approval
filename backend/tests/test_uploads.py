from pathlib import Path
from io import BytesIO

from fastapi.testclient import TestClient
from openpyxl import Workbook
from PIL import Image, ImageDraw

from app.main import app
from app.routers.uploads import UPLOAD_DIR
from app.services.approval_engine import analyze_case
from app.services.profit_mapper import map_parse_result_to_case
from app.services.profit_mapper import map_parse_result_with_metadata
from app.services.profit_parser import parse_profit_file


def make_xlsx_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"
    sheet.append(["CUSTOMER", "TEST CUSTOMER"])
    sheet.append(["MODE", "SEA EXPORT B/L POL BUSAN POD TOKYO"])
    sheet.append(["CONTAINER", "40HC x 2"])
    sheet.append(["REVENUE"])
    sheet.append(["TRUCKING", 61000])
    sheet.append(["CUSTOMS", 11800])
    sheet.append(["TOTAL REVENUE", 100000])
    sheet.append(["EXPENSE"])
    sheet.append(["TRUCKING COST", 50000])
    sheet.append(["CUSTOMS COST", 0])
    sheet.append(["TOTAL EXPENSE", 70000])
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def test_profit_sheet_upload_list_and_detail() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/uploads/profit-sheet",
        files={"file": ("sample.pdf", b"%PDF-1.4\nsample", "application/pdf")},
    )

    assert response.status_code == 200
    uploaded = response.json()
    assert uploaded["original_filename"] == "sample.pdf"
    assert uploaded["file_ext"] == ".pdf"
    assert uploaded["status"] == "uploaded"
    assert uploaded["upload_id"] in uploaded["saved_filename"]
    assert (Path(UPLOAD_DIR) / uploaded["saved_filename"]).exists()

    list_response = client.get("/api/uploads")
    assert list_response.status_code == 200
    assert any(
        item["upload_id"] == uploaded["upload_id"] for item in list_response.json()
    )

    detail_response = client.get(f"/api/uploads/{uploaded['upload_id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["upload_id"] == uploaded["upload_id"]
    assert detail["file_size"] == len(b"%PDF-1.4\nsample")


def test_profit_sheet_upload_rejects_unsupported_extension() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/uploads/profit-sheet",
        files={"file": ("sample.txt", b"not allowed", "text/plain")},
    )

    assert response.status_code == 400


def test_get_upload_returns_404_for_unknown_upload_id() -> None:
    client = TestClient(app)

    response = client.get("/api/uploads/not-found")

    assert response.status_code == 404


def test_parse_profit_file_extracts_excel_text_and_tables(tmp_path: Path) -> None:
    file_path = tmp_path / "profit.xlsx"
    file_path.write_bytes(make_xlsx_bytes())

    result = parse_profit_file(str(file_path), ".xlsx")

    assert result["file_ext"] == ".xlsx"
    assert result["status"] == "parsed"
    assert "TRUCKING" in result["raw_text"]
    assert result["raw_tables"][0]["sheet_name"] == "Sheet1"
    assert result["raw_tables"][0]["rows"][0] == ["CUSTOMER", "TEST CUSTOMER"]
    assert result["raw_tables"][0]["rows"][4] == ["TRUCKING", "61000"]


def test_parse_profit_file_detects_image_only_pdf_needing_ocr(tmp_path: Path) -> None:
    file_path = tmp_path / "scanned_profit.pdf"
    image = Image.new("RGB", (600, 300), "white")
    draw = ImageDraw.Draw(image)
    draw.text((40, 80), "CUSTOMER TEST CUSTOMER", fill="black")
    image.save(file_path, "PDF")

    result = parse_profit_file(str(file_path), ".pdf")

    assert result["file_ext"] == ".pdf"
    assert result["status"] == "parsed"
    assert result["page_count"] == 1
    assert result["image_only_page_count"] == 1
    assert result["ocr_status"] in {"ocr_unavailable", "ocr_failed", "ocr_applied"}
    assert result["warnings"] or result["raw_text"]


def test_map_parse_result_to_case_creates_candidate() -> None:
    parse_result = {
        "file_ext": ".xlsx",
        "raw_text": "",
        "raw_tables": [
            {
                "sheet_name": "Sheet1",
                "rows": [
                    ["CUSTOMER", "TEST CUSTOMER"],
                    ["SEA EXPORT B/L POL BUSAN POD TOKYO"],
                    ["40HC x 2"],
                    ["REVENUE"],
                    ["TRUCKING", "61,000"],
                    ["CUSTOMS", "11,800"],
                    ["EXPENSE"],
                    ["TRUCKING COST", "50,000"],
                    ["CUSTOMS COST", "0"],
                ],
            }
        ],
        "status": "parsed",
    }

    candidate = map_parse_result_to_case(parse_result)

    assert candidate.customer_name == "TEST CUSTOMER"
    assert candidate.mode == "SEA"
    assert candidate.direction == "EXPORT"
    assert candidate.has_transport is True
    assert candidate.has_customs is True
    assert candidate.container_type == "40HC"
    assert candidate.container_count == 2
    assert candidate.transport_revenue_jpy == 61000
    assert candidate.transport_expense_jpy == 50000
    assert candidate.customs_revenue_jpy == 11800


def test_map_parse_result_prioritizes_totals_and_extracts_detail_amounts() -> None:
    parse_result = {
        "file_ext": ".xlsx",
        "raw_text": "",
        "raw_tables": [
            {
                "sheet_name": "TOWA",
                "rows": [
                    ["CUSTOMER", "TOWA CO., LTD."],
                    ["SEA IMPORT D/O POD TOKYO ETA"],
                    ["CONTAINER", "20DC x 1"],
                    ["REVENUE"],
                    ["TRUCKING", "JPY 61,000"],
                    ["CUSTOMS", "11,800"],
                    ["CONSUMPTION TAX", "300,300"],
                    ["TOTAL REVENUE", "468,146"],
                    ["EXPENSE"],
                    ["TRUCKING COST", "60,000"],
                    ["TOTAL EXPENSE", "443,653"],
                    ["GROSS PROFIT", "24,493"],
                ],
            }
        ],
        "status": "parsed",
    }

    mapped = map_parse_result_with_metadata(parse_result)
    candidate = mapped["candidate"]
    result = analyze_case(candidate)

    assert candidate.customer_name == "TOWA CO., LTD."
    assert candidate.mode == "SEA"
    assert candidate.direction == "IMPORT"
    assert candidate.has_transport is True
    assert candidate.has_customs is True
    assert candidate.container_type == "20DC"
    assert candidate.revenue_items[0].amount_jpy == 468146
    assert candidate.expense_items[0].amount_jpy == 443653
    assert candidate.transport_revenue_jpy == 61000
    assert candidate.transport_expense_jpy == 60000
    assert candidate.customs_revenue_jpy == 11800
    assert candidate.consumption_tax_jpy == 300300
    assert result.code == "SI++"
    assert result.gp_jpy == 24493
    assert mapped["parsing_confidence"] > 0.8


def test_map_parse_result_separates_usd_partner_fee_from_jpy_amounts() -> None:
    parse_result = {
        "file_ext": ".xlsx",
        "raw_text": "",
        "raw_tables": [
            {
                "sheet_name": "PNS",
                "rows": [
                    ["CUSTOMER", "SUMITOMO CHEMICAL"],
                    ["SEA EXPORT B/L POL KOBE POD BUSAN"],
                    ["CONTAINER", "40HC x 2"],
                    ["REVENUE"],
                    ["TOTAL REVENUE", "144,798"],
                    ["EXPENSE"],
                    ["TOTAL EXPENSE", "124,000"],
                    ["PARTNER FEE", "PNS NETWORKS CO., LTD", "USD 30"],
                ],
            }
        ],
        "status": "parsed",
    }

    candidate = map_parse_result_to_case(parse_result)
    result = analyze_case(candidate)

    assert candidate.partner_fee is not None
    assert candidate.partner_fee.actual_fee_usd == 30
    assert candidate.partner_fee.actual_fee_jpy == 0
    assert candidate.partner_fee.container_type == "40HC"
    assert candidate.partner_fee.container_count == 2
    assert candidate.revenue_items[0].amount_jpy == 144798
    assert candidate.expense_items[0].amount_jpy == 124000
    assert result.code == "SE"
    assert result.gp_jpy == 20798
    assert any(
        finding.category == "Partner Fee" and finding.status == "OK"
        for finding in result.findings
    )


def test_upload_parse_api_returns_raw_text_and_tables() -> None:
    client = TestClient(app)

    upload_response = client.post(
        "/api/uploads/profit-sheet",
        files={
            "file": (
                "profit.xlsx",
                make_xlsx_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert upload_response.status_code == 200
    upload_id = upload_response.json()["upload_id"]

    parse_response = client.post(f"/api/uploads/{upload_id}/parse")

    assert parse_response.status_code == 200
    parsed = parse_response.json()
    assert parsed["upload_id"] == upload_id
    assert parsed["original_filename"] == "profit.xlsx"
    assert parsed["parse_result"]["file_ext"] == ".xlsx"
    assert parsed["parse_result"]["status"] == "parsed"
    assert "TRUCKING" in parsed["parse_result"]["raw_text"]
    assert parsed["parse_result"]["raw_tables"][0]["rows"][4] == ["TRUCKING", "61000"]


def test_upload_parse_api_returns_404_for_unknown_upload_id() -> None:
    client = TestClient(app)

    response = client.post("/api/uploads/not-found/parse")

    assert response.status_code == 404


def test_upload_map_analyze_and_save_flow() -> None:
    client = TestClient(app)
    client.post("/api/masters/seed-defaults")

    upload_response = client.post(
        "/api/uploads/profit-sheet",
        files={
            "file": (
                "profit.xlsx",
                make_xlsx_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert upload_response.status_code == 200
    upload_id = upload_response.json()["upload_id"]

    map_response = client.post(f"/api/uploads/{upload_id}/map-to-case")
    assert map_response.status_code == 200
    mapped = map_response.json()
    assert mapped["candidate"]["customer_name"] == "TEST CUSTOMER"
    assert mapped["parsing_confidence"] > 0
    assert mapped["template_used"]["template_name"] in {
        "LOTOS_EXCEL",
        "LOTOS_STANDARD_PDF",
        "CODE_FALLBACK_STANDARD",
    }

    analyze_response = client.post(f"/api/uploads/{upload_id}/analyze")
    assert analyze_response.status_code == 200
    analyzed = analyze_response.json()
    assert analyzed["customer_name"] == "TEST CUSTOMER"
    assert analyzed["code"] == "SE++"

    save_response = client.post(f"/api/uploads/{upload_id}/analyze-and-save")
    assert save_response.status_code == 200
    saved = save_response.json()
    assert saved["approval_case_id"] > 0
    assert saved["result"]["code"] == "SE++"
