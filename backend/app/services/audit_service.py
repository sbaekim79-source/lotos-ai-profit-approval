from sqlalchemy.orm import Session

from app import models


def create_audit_log(
    db: Session,
    user_name: str | None,
    action: str,
    entity_type: str,
    entity_id: int | str | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
) -> models.AuditLog:
    audit_log = models.AuditLog(
        user_name=user_name,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log
