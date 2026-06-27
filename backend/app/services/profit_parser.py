from pathlib import Path
import shutil
import subprocess
from typing import Any

import pandas as pd
import pdfplumber


OCR_LANGUAGES = "eng+jpn+kor"
PROJECT_TESSDATA_DIR = Path(__file__).resolve().parents[2] / "tessdata"
COMMON_TESSERACT_PATHS = [
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
]


def parse_profit_file(file_path: str, file_ext: str) -> dict[str, Any]:
    normalized_ext = file_ext.lower()
    if normalized_ext == ".pdf":
        return _parse_pdf(file_path, normalized_ext)
    if normalized_ext in {".xlsx", ".xls"}:
        return _parse_excel(file_path, normalized_ext)
    raise ValueError(f"Unsupported file extension: {file_ext}")


def _parse_pdf(file_path: str, file_ext: str) -> dict[str, Any]:
    raw_text_parts: list[str] = []
    raw_tables: list[dict[str, Any]] = []
    warnings: list[str] = []
    page_diagnostics: list[dict[str, Any]] = []
    text_page_count = 0
    image_only_page_count = 0

    with pdfplumber.open(file_path) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text:
                raw_text_parts.append(page_text)
                text_page_count += 1

            tables = page.extract_tables() or []
            for table in tables:
                raw_tables.append(
                    {
                        "page_no": page_index,
                        "rows": _normalize_rows(table),
                    }
                )

            chars = getattr(page, "chars", []) or []
            images = getattr(page, "images", []) or []
            if not page_text.strip() and not tables and images:
                image_only_page_count += 1

            page_diagnostics.append(
                {
                    "page_no": page_index,
                    "text_length": len(page_text),
                    "char_count": len(chars),
                    "table_count": len(tables),
                    "image_count": len(images),
                }
            )

        if not raw_text_parts and not raw_tables and image_only_page_count > 0:
            ocr_result = _try_ocr_pdf(pdf)
            raw_text = ocr_result["raw_text"]
            if raw_text.strip():
                raw_text_parts.append(raw_text)
            warnings.extend(ocr_result["warnings"])

    raw_text = "\n".join(raw_text_parts)
    if not raw_text.strip() and not raw_tables:
        warnings.append(
            "PDF에서 텍스트/테이블을 추출하지 못했습니다. 스캔 이미지 PDF일 가능성이 높습니다."
        )

    return {
        "file_ext": file_ext,
        "raw_text": raw_text,
        "raw_tables": raw_tables,
        "status": "parsed",
        "ocr_status": _ocr_status(raw_text, warnings, image_only_page_count),
        "warnings": warnings,
        "page_count": len(page_diagnostics),
        "text_page_count": text_page_count,
        "image_only_page_count": image_only_page_count,
        "page_diagnostics": page_diagnostics,
    }


def _parse_excel(file_path: str, file_ext: str) -> dict[str, Any]:
    sheets = pd.read_excel(Path(file_path), sheet_name=None, header=None)
    raw_text_parts: list[str] = []
    raw_tables: list[dict[str, Any]] = []

    for sheet_name, dataframe in sheets.items():
        rows = _normalize_rows(dataframe.values.tolist())
        raw_tables.append(
            {
                "sheet_name": sheet_name,
                "rows": rows,
            }
        )
        for row in rows:
            raw_text_parts.append(" ".join(cell for cell in row if cell))

    return {
        "file_ext": file_ext,
        "raw_text": "\n".join(raw_text_parts),
        "raw_tables": raw_tables,
        "status": "parsed",
        "ocr_status": "not_applicable",
        "warnings": [],
    }


def _try_ocr_pdf(pdf: pdfplumber.PDF) -> dict[str, Any]:
    warnings: list[str] = []
    tesseract_cmd = _find_tesseract_cmd()
    if tesseract_cmd is None:
        return {
            "raw_text": "",
            "warnings": [
                "이 PDF는 이미지형 PDF로 보입니다. OCR을 위해 서버에 Tesseract 설치가 필요합니다."
            ],
        }

    try:
        import pytesseract
    except ImportError:
        return {
            "raw_text": "",
            "warnings": [
                "이 PDF는 이미지형 PDF로 보입니다. OCR을 위해 pytesseract 패키지 설치가 필요합니다."
            ],
        }

    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    tessdata_dir = _select_tessdata_dir(tesseract_cmd)
    languages = _select_ocr_languages(tesseract_cmd, tessdata_dir)
    if not languages:
        return {
            "raw_text": "",
            "warnings": [
                "Tesseract OCR 언어 데이터가 없습니다. eng, jpn, kor traineddata 설치가 필요합니다."
            ],
        }
    if set(languages.split("+")) < {"eng", "jpn", "kor"}:
        warnings.append(
            f"설치된 OCR 언어 데이터가 제한적입니다. 사용 언어: {languages}"
        )

    config = f"--tessdata-dir {tessdata_dir}" if tessdata_dir else ""
    ocr_text_parts: list[str] = []
    for page_index, page in enumerate(pdf.pages, start=1):
        try:
            image = page.to_image(resolution=220).original
            page_text = (
                pytesseract.image_to_string(image, lang=languages, config=config) or ""
            )
            if page_text.strip():
                ocr_text_parts.append(f"[OCR PAGE {page_index}]\n{page_text.strip()}")
        except Exception as exc:
            warnings.append(f"{page_index}페이지 OCR 처리 실패: {exc}")

    if not ocr_text_parts and not warnings:
        warnings.append("OCR을 실행했지만 추출된 텍스트가 없습니다.")
    return {
        "raw_text": "\n\n".join(ocr_text_parts),
        "warnings": warnings,
    }


def _find_tesseract_cmd() -> str | None:
    found = shutil.which("tesseract")
    if found:
        return found
    for path in COMMON_TESSERACT_PATHS:
        if path.exists():
            return str(path)
    return None


def _select_tessdata_dir(tesseract_cmd: str) -> Path | None:
    if PROJECT_TESSDATA_DIR.exists():
        return PROJECT_TESSDATA_DIR
    executable_tessdata = Path(tesseract_cmd).resolve().parent / "tessdata"
    if executable_tessdata.exists():
        return executable_tessdata
    return None


def _select_ocr_languages(tesseract_cmd: str, tessdata_dir: Path | None) -> str:
    available = _available_ocr_languages(tesseract_cmd, tessdata_dir)
    selected = [language for language in OCR_LANGUAGES.split("+") if language in available]
    return "+".join(selected)


def _available_ocr_languages(
    tesseract_cmd: str,
    tessdata_dir: Path | None,
) -> set[str]:
    command = [tesseract_cmd, "--list-langs"]
    if tessdata_dir:
        command.extend(["--tessdata-dir", str(tessdata_dir)])
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
    except Exception:
        return set()
    output = f"{completed.stdout}\n{completed.stderr}"
    return {
        line.strip()
        for line in output.splitlines()
        if line.strip() and not line.lower().startswith("list of available")
    }


def _ocr_status(raw_text: str, warnings: list[str], image_only_page_count: int) -> str:
    if image_only_page_count <= 0:
        return "not_required"
    if raw_text.strip():
        return "ocr_applied"
    if any("Tesseract" in warning or "pytesseract" in warning for warning in warnings):
        return "ocr_unavailable"
    return "ocr_failed"


def _normalize_rows(rows: list[list[Any]]) -> list[list[str]]:
    normalized_rows: list[list[str]] = []
    for row in rows:
        normalized_rows.append([_normalize_cell(cell) for cell in row])
    return normalized_rows


def _normalize_cell(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)
