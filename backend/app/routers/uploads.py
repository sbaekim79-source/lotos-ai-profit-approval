from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.database import get_db
from app.schemas import (
    ApprovalResult,
    ApprovalSaveResponse,
    ProfitMapResponse,
    ProfitParseResponse,
    ProfitUploadItem,
    ProfitUploadResponse,
)
from app.services.approval_engine import analyze_case, analyze_case_with_rules
from app.services.approval_repository import save_approval_case
from app.services.audit_service import create_audit_log
from app.services.profit_mapper import map_parse_result_with_metadata
from app.services.profit_parser import parse_profit_file


router = APIRouter(prefix="/api/uploads", tags=["Uploads"])

UPLOAD_DIR = settings.upload_dir
ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls"}


def _safe_filename(filename: str) -> str:
    return Path(filename).name.replace(" ", "_")


def _to_upload_item(upload: models.ProfitUpload) -> ProfitUploadItem:
    return ProfitUploadItem(
        upload_id=upload.upload_id,
        original_filename=upload.original_filename,
        saved_filename=upload.saved_filename,
        file_ext=upload.file_ext,
        file_size=upload.file_size,
        created_at=upload.created_at,
    )


def _get_upload_or_404(upload_id: str, db: Session) -> models.ProfitUpload:
    upload = db.execute(
        select(models.ProfitUpload).where(models.ProfitUpload.upload_id == upload_id)
    ).scalar_one_or_none()
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload


def _parse_upload_or_error(upload: models.ProfitUpload) -> dict:
    file_path = Path(upload.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded file not found")
    try:
        return parse_profit_file(str(file_path), upload.file_ext)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to parse file: {exc}")


@router.post("/profit-sheet", response_model=ProfitUploadResponse)
async def upload_profit_sheet(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ProfitUploadResponse:
    original_filename = file.filename or "uploaded_file"
    file_ext = Path(original_filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only .pdf, .xlsx, and .xls files are allowed",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    upload_id = str(uuid4())
    saved_filename = f"{upload_id}_{_safe_filename(original_filename)}"
    file_path = UPLOAD_DIR / saved_filename

    contents = await file.read()
    file_path.write_bytes(contents)

    upload = models.ProfitUpload(
        upload_id=upload_id,
        original_filename=original_filename,
        saved_filename=saved_filename,
        file_ext=file_ext,
        file_path=str(file_path),
        file_size=file_path.stat().st_size,
        status="uploaded",
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    return ProfitUploadResponse(
        upload_id=upload.upload_id,
        original_filename=upload.original_filename,
        saved_filename=upload.saved_filename,
        file_ext=upload.file_ext,
        status=upload.status,
    )


@router.get("", response_model=list[ProfitUploadItem])
def list_uploads(db: Session = Depends(get_db)) -> list[ProfitUploadItem]:
    uploads = db.execute(
        select(models.ProfitUpload).order_by(models.ProfitUpload.created_at.desc())
    ).scalars()
    return [_to_upload_item(upload) for upload in uploads]


@router.get("/{upload_id}", response_model=ProfitUploadItem)
def get_upload(upload_id: str, db: Session = Depends(get_db)) -> ProfitUploadItem:
    upload = _get_upload_or_404(upload_id, db)
    return _to_upload_item(upload)


@router.post("/{upload_id}/parse", response_model=ProfitParseResponse)
def parse_upload(
    upload_id: str,
    db: Session = Depends(get_db),
) -> ProfitParseResponse:
    upload = _get_upload_or_404(upload_id, db)
    parse_result = _parse_upload_or_error(upload)

    return ProfitParseResponse(
        upload_id=upload.upload_id,
        original_filename=upload.original_filename,
        parse_result=parse_result,
    )


@router.post("/{upload_id}/map-to-case", response_model=ProfitMapResponse)
def map_upload_to_case(
    upload_id: str,
    db: Session = Depends(get_db),
) -> ProfitMapResponse:
    upload = _get_upload_or_404(upload_id, db)
    parse_result = _parse_upload_or_error(upload)
    mapped = map_parse_result_with_metadata(parse_result, db=db, file_ext=upload.file_ext)
    return ProfitMapResponse(
        upload_id=upload.upload_id,
        original_filename=upload.original_filename,
        candidate=mapped["candidate"],
        parsing_confidence=mapped["parsing_confidence"],
        confidence=mapped["confidence"],
        warnings=mapped["warnings"],
        template_used=mapped["template_used"],
    )


@router.post("/{upload_id}/analyze", response_model=ApprovalResult)
def analyze_upload(
    upload_id: str,
    db: Session = Depends(get_db),
) -> ApprovalResult:
    upload = _get_upload_or_404(upload_id, db)
    parse_result = _parse_upload_or_error(upload)
    mapped = map_parse_result_with_metadata(parse_result, db=db, file_ext=upload.file_ext)
    return analyze_case(mapped["candidate"])


@router.post("/{upload_id}/analyze-and-save", response_model=ApprovalSaveResponse)
def analyze_and_save_upload(
    upload_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> ApprovalSaveResponse:
    upload = _get_upload_or_404(upload_id, db)
    parse_result = _parse_upload_or_error(upload)
    mapped = map_parse_result_with_metadata(parse_result, db=db, file_ext=upload.file_ext)
    candidate = mapped["candidate"]
    result = analyze_case_with_rules(candidate, db)
    approval_case = save_approval_case(db, candidate, result)
    create_audit_log(
        db,
        user_name=request.headers.get("X-USER-NAME"),
        action="SAVE_APPROVAL_UPLOAD",
        entity_type="APPROVAL_CASE",
        entity_id=approval_case.id,
        detail=upload_id,
        ip_address=request.client.host if request.client else None,
    )
    return ApprovalSaveResponse(approval_case_id=approval_case.id, result=result)
