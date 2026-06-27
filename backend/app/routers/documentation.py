from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


router = APIRouter(prefix="/api/docs", tags=["Documentation"])

PROJECT_DIR = Path(__file__).resolve().parents[3]
DOCS_DIR = PROJECT_DIR / "docs"

DOCUMENTS = {
    "user-manual": "USER_MANUAL.md",
    "admin-manual": "ADMIN_MANUAL.md",
    "training-guide": "TRAINING_GUIDE.md",
}


def _document_response(document_key: str) -> FileResponse:
    file_name = DOCUMENTS[document_key]
    path = DOCS_DIR / file_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(
        path,
        media_type="text/markdown; charset=utf-8",
        filename=file_name,
    )


@router.get("/user-manual")
def download_user_manual() -> FileResponse:
    return _document_response("user-manual")


@router.get("/admin-manual")
def download_admin_manual() -> FileResponse:
    return _document_response("admin-manual")


@router.get("/training-guide")
def download_training_guide() -> FileResponse:
    return _document_response("training-guide")
