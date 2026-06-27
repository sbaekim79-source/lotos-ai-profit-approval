from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import AuditLogRead


router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    user_name: str | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
) -> list[AuditLogRead]:
    statement = select(models.AuditLog).order_by(models.AuditLog.created_at.desc())
    if user_name:
        statement = statement.where(models.AuditLog.user_name == user_name)
    if action:
        statement = statement.where(models.AuditLog.action == action)
    if entity_type:
        statement = statement.where(models.AuditLog.entity_type == entity_type)
    if start_date:
        statement = statement.where(models.AuditLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        statement = statement.where(
            models.AuditLog.created_at
            <= datetime.fromisoformat(end_date).replace(hour=23, minute=59, second=59)
        )
    logs = db.execute(statement.limit(500)).scalars()
    return [
        AuditLogRead(
            id=log.id,
            user_name=log.user_name,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            detail=log.detail,
            ip_address=log.ip_address,
            created_at=log.created_at,
        )
        for log in logs
    ]
