from datetime import datetime
from pathlib import Path
from shutil import copy2

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.database import DB_PATH, get_db
from app.schemas import BackupFileItem, BackupResponse, SystemStatusResponse
from app.services.auth import actor_name, ensure_role, get_current_user
from app.services.audit_service import create_audit_log


router = APIRouter(prefix="/api/admin", tags=["Admin"])

BACKUP_DIR = settings.backup_dir
UPLOAD_DIR = settings.upload_dir
REPORT_DIR = settings.report_dir
LOG_DIR = settings.log_dir


@router.post("/backup-db", response_model=BackupResponse)
def backup_database(
    request: Request,
    db: Session = Depends(get_db),
) -> BackupResponse:
    user = get_current_user(request, db)
    ensure_role(user, {"ADMIN"})
    if settings.database_type == "postgresql":
        return BackupResponse(
            status="manual_required",
            backup_file=None,
            message="PostgreSQL backup requires pg_dump. See README.",
        )
    if DB_PATH is None or not DB_PATH.exists():
        raise HTTPException(status_code=404, detail="SQLite DB file not found")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_name = f"lotos_ai_approval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = BACKUP_DIR / backup_name
    copy2(DB_PATH, backup_path)
    create_audit_log(
        db,
        user_name=actor_name(user),
        action="BACKUP_DB",
        entity_type="DATABASE",
        detail=backup_name,
        ip_address=_client_ip(request),
    )
    return BackupResponse(status="ok", backup_file=str(backup_path))


@router.get("/backups", response_model=list[BackupFileItem])
def list_backups(
    request: Request,
    db: Session = Depends(get_db),
) -> list[BackupFileItem]:
    user = get_current_user(request, db)
    ensure_role(user, {"ADMIN"})
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(BACKUP_DIR.glob("*.db"), key=lambda path: path.stat().st_mtime, reverse=True)
    return [
        BackupFileItem(
            file_name=path.name,
            file_path=str(path),
            file_size=path.stat().st_size,
            created_at=datetime.fromtimestamp(path.stat().st_mtime),
        )
        for path in files
    ]


@router.get("/system-status", response_model=SystemStatusResponse)
def system_status(
    request: Request,
    db: Session = Depends(get_db),
) -> SystemStatusResponse:
    user = get_current_user(request, db)
    ensure_role(user, {"ADMIN"})
    database_status = "ok"
    try:
        db.execute(text("SELECT 1")).scalar_one()
    except Exception:
        database_status = "error"

    return SystemStatusResponse(
        database=database_status,
        database_type=settings.database_type,
        database_url_masked=settings.database_url_masked,
        app_env=settings.app_env,
        upload_folder_exists=UPLOAD_DIR.exists(),
        generated_reports_folder_exists=REPORT_DIR.exists(),
        logs_folder_exists=LOG_DIR.exists(),
        backup_folder_exists=BACKUP_DIR.exists(),
        approval_case_count=_count(db, models.ApprovalCase),
        workflow_count=_count(db, models.ApprovalWorkflow),
        quote_count=_count(db, models.QuoteCase),
        report_file_count=_count(db, models.ApprovalReportFile),
    )


def _count(db: Session, model: type) -> int:
    return int(db.execute(select(func.count()).select_from(model)).scalar_one())


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None
