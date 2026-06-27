from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import ApprovalReportFileRead
from app.services.auth import actor_name, ensure_role, get_current_user
from app.services.audit_service import create_audit_log
from app.services.pdf_report_service import generate_approval_pdf


router = APIRouter(tags=["Reports"])


@router.post(
    "/api/approvals/{approval_case_id}/report/pdf",
    response_model=ApprovalReportFileRead,
)
def create_approval_pdf_report(
    approval_case_id: int,
    request: Request,
    report_type: str = "DETAIL",
    db: Session = Depends(get_db),
) -> ApprovalReportFileRead:
    user = get_current_user(request, db)
    ensure_role(user, {"TEAM_MANAGER", "DIRECTOR", "CEO"})
    report_file = generate_approval_pdf(
        db,
        approval_case_id=approval_case_id,
        report_type=report_type,
        created_by=actor_name(user),
    )
    create_audit_log(
        db,
        user_name=actor_name(user),
        action="CREATE_PDF_REPORT",
        entity_type="APPROVAL_REPORT_FILE",
        entity_id=report_file.id,
        detail=f"{report_file.report_type} approval_case_id={approval_case_id}",
        ip_address=request.client.host if request.client else None,
    )
    return _to_report_file_read(report_file)


@router.get(
    "/api/approvals/{approval_case_id}/report/files",
    response_model=list[ApprovalReportFileRead],
)
def list_approval_pdf_reports(
    approval_case_id: int,
    db: Session = Depends(get_db),
) -> list[ApprovalReportFileRead]:
    reports = db.execute(
        select(models.ApprovalReportFile)
        .where(models.ApprovalReportFile.approval_case_id == approval_case_id)
        .order_by(models.ApprovalReportFile.created_at.desc())
    ).scalars()
    return [_to_report_file_read(report) for report in reports]


@router.get("/api/reports/files/{report_file_id}/download")
def download_report_file(
    report_file_id: int,
    db: Session = Depends(get_db),
) -> FileResponse:
    report_file = db.get(models.ApprovalReportFile, report_file_id)
    if report_file is None:
        raise HTTPException(status_code=404, detail="Report file not found")

    path = Path(report_file.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file does not exist")

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=report_file.file_name,
    )


def _to_report_file_read(
    report_file: models.ApprovalReportFile,
) -> ApprovalReportFileRead:
    return ApprovalReportFileRead(
        report_file_id=report_file.id,
        approval_case_id=report_file.approval_case_id,
        report_type=report_file.report_type,
        file_name=report_file.file_name,
        download_url=f"/api/reports/files/{report_file.id}/download",
        created_by=report_file.created_by,
        created_at=report_file.created_at,
    )
