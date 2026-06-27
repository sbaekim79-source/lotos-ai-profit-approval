from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.database import get_db
from app.schemas import (
    IntegrationExportRequest,
    IntegrationExportResponse,
    IntegrationLogRead,
    IntegrationSettingCreate,
    IntegrationSettingRead,
)
from app.services.audit_service import create_audit_log
from app.services.auth import actor_name, ensure_role, get_current_user
from app.services.integration_service import (
    build_approval_payload,
    build_quote_payload,
    build_tariff_payload,
)


router = APIRouter(prefix="/api/integrations", tags=["Integrations"])

VIEW_ROLES = {"DIRECTOR", "CEO"}
ADMIN_ROLES = {"ADMIN"}
INTEGRATION_DIR = settings.export_dir / "integration"


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _setting_to_read(setting: models.IntegrationSetting) -> IntegrationSettingRead:
    return IntegrationSettingRead(
        id=setting.id,
        integration_name=setting.integration_name,
        integration_type=setting.integration_type,
        endpoint_url=setting.endpoint_url,
        export_format=setting.export_format,
        is_active=setting.is_active,
        description=setting.description,
        created_at=setting.created_at,
    )


def _log_to_read(log: models.IntegrationLog) -> IntegrationLogRead:
    return IntegrationLogRead(
        id=log.id,
        integration_name=log.integration_name,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        status=log.status,
        request_payload=log.request_payload,
        response_payload=log.response_payload,
        error_message=log.error_message,
        created_by=log.created_by,
        created_at=log.created_at,
    )


def _get_setting(
    db: Session,
    integration_name: str,
) -> models.IntegrationSetting | None:
    return db.execute(
        select(models.IntegrationSetting)
        .where(
            models.IntegrationSetting.integration_name == integration_name,
            models.IntegrationSetting.is_active.is_(True),
        )
        .order_by(models.IntegrationSetting.created_at.desc())
    ).scalars().first()


def _write_json_file(entity_type: str, entity_id: int, payload: dict) -> Path:
    INTEGRATION_DIR.mkdir(parents=True, exist_ok=True)
    file_name = (
        f"{entity_type.lower()}_{entity_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    path = INTEGRATION_DIR / file_name
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def _create_log(
    *,
    db: Session,
    integration_name: str,
    entity_type: str,
    entity_id: int,
    status: str,
    payload: dict,
    user_name: str | None,
    response_payload: dict | None = None,
    error_message: str | None = None,
) -> models.IntegrationLog:
    log = models.IntegrationLog(
        integration_name=integration_name,
        entity_type=entity_type,
        entity_id=entity_id,
        status=status,
        request_payload=json.dumps(payload, ensure_ascii=False),
        response_payload=(
            json.dumps(response_payload, ensure_ascii=False)
            if response_payload is not None
            else None
        ),
        error_message=error_message,
        created_by=user_name,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def _export_payload(
    *,
    db: Session,
    request: Request,
    integration_request: IntegrationExportRequest,
    entity_type: str,
    entity_id: int,
    payload: dict,
) -> IntegrationExportResponse:
    user = get_current_user(request, db)
    ensure_role(user, VIEW_ROLES)
    setting = _get_setting(db, integration_request.integration_name)
    export_format = integration_request.export_format
    if setting is not None:
        export_format = setting.export_format

    if export_format != "JSON":
        raise HTTPException(status_code=400, detail="Only JSON export is implemented")

    if (
        setting is not None
        and setting.integration_type == "WEBHOOK"
        and setting.endpoint_url
    ):
        log = _create_log(
            db=db,
            integration_name=integration_request.integration_name,
            entity_type=entity_type,
            entity_id=entity_id,
            status="PENDING",
            payload=payload,
            user_name=actor_name(user),
            response_payload={"endpoint_url": setting.endpoint_url},
        )
        create_audit_log(
            db,
            user_name=actor_name(user),
            action="INTEGRATION_EXPORT",
            entity_type=entity_type,
            entity_id=entity_id,
            detail=json.dumps(
                {
                    "integration_name": integration_request.integration_name,
                    "export_format": export_format,
                    "status": "PENDING",
                    "endpoint_url": setting.endpoint_url,
                },
                ensure_ascii=False,
            ),
            ip_address=_client_ip(request),
        )
        return IntegrationExportResponse(
            status="PENDING",
            file_name=None,
            download_url=None,
            log_id=log.id,
        )

    path = _write_json_file(entity_type, entity_id, payload)
    response_payload = {
        "file_name": path.name,
        "file_path": str(path),
        "download_url": f"/api/integrations/files/{0}/download",
    }
    log = _create_log(
        db=db,
        integration_name=integration_request.integration_name,
        entity_type=entity_type,
        entity_id=entity_id,
        status="SUCCESS",
        payload=payload,
        user_name=actor_name(user),
        response_payload=response_payload,
    )
    response_payload["download_url"] = f"/api/integrations/files/{log.id}/download"
    log.response_payload = json.dumps(response_payload, ensure_ascii=False)
    db.commit()

    create_audit_log(
        db,
        user_name=actor_name(user),
        action="INTEGRATION_EXPORT",
        entity_type=entity_type,
        entity_id=entity_id,
        detail=json.dumps(
            {
                "integration_name": integration_request.integration_name,
                "export_format": export_format,
                "file_name": path.name,
            },
            ensure_ascii=False,
        ),
        ip_address=_client_ip(request),
    )
    return IntegrationExportResponse(
        status="SUCCESS",
        file_name=path.name,
        download_url=f"/api/integrations/files/{log.id}/download",
        log_id=log.id,
    )


@router.get("/settings", response_model=list[IntegrationSettingRead])
def list_integration_settings(
    request: Request,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
) -> list[IntegrationSettingRead]:
    user = get_current_user(request, db)
    ensure_role(user, VIEW_ROLES)
    statement = select(models.IntegrationSetting).order_by(
        models.IntegrationSetting.created_at.desc()
    )
    if is_active is not None:
        statement = statement.where(models.IntegrationSetting.is_active == is_active)
    return [_setting_to_read(setting) for setting in db.execute(statement).scalars()]


@router.post("/settings", response_model=IntegrationSettingRead)
def create_integration_setting(
    payload: IntegrationSettingCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> IntegrationSettingRead:
    user = get_current_user(request, db)
    ensure_role(user, ADMIN_ROLES)
    setting = models.IntegrationSetting(**payload.model_dump())
    db.add(setting)
    db.commit()
    db.refresh(setting)
    create_audit_log(
        db,
        user_name=actor_name(user),
        action="CREATE_INTEGRATION_SETTING",
        entity_type="INTEGRATION_SETTING",
        entity_id=setting.id,
        detail=setting.integration_name,
        ip_address=_client_ip(request),
    )
    return _setting_to_read(setting)


@router.put("/settings/{setting_id}", response_model=IntegrationSettingRead)
def update_integration_setting(
    setting_id: int,
    payload: IntegrationSettingCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> IntegrationSettingRead:
    user = get_current_user(request, db)
    ensure_role(user, ADMIN_ROLES)
    setting = db.get(models.IntegrationSetting, setting_id)
    if setting is None:
        raise HTTPException(status_code=404, detail="Integration setting not found")
    for key, value in payload.model_dump().items():
        setattr(setting, key, value)
    db.commit()
    db.refresh(setting)
    create_audit_log(
        db,
        user_name=actor_name(user),
        action="UPDATE_INTEGRATION_SETTING",
        entity_type="INTEGRATION_SETTING",
        entity_id=setting.id,
        detail=setting.integration_name,
        ip_address=_client_ip(request),
    )
    return _setting_to_read(setting)


@router.delete("/settings/{setting_id}", response_model=IntegrationSettingRead)
def deactivate_integration_setting(
    setting_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> IntegrationSettingRead:
    user = get_current_user(request, db)
    ensure_role(user, ADMIN_ROLES)
    setting = db.get(models.IntegrationSetting, setting_id)
    if setting is None:
        raise HTTPException(status_code=404, detail="Integration setting not found")
    setting.is_active = False
    db.commit()
    db.refresh(setting)
    create_audit_log(
        db,
        user_name=actor_name(user),
        action="DEACTIVATE_INTEGRATION_SETTING",
        entity_type="INTEGRATION_SETTING",
        entity_id=setting.id,
        detail=setting.integration_name,
        ip_address=_client_ip(request),
    )
    return _setting_to_read(setting)


@router.get("/logs", response_model=list[IntegrationLogRead])
def list_integration_logs(
    request: Request,
    integration_name: str | None = None,
    entity_type: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
) -> list[IntegrationLogRead]:
    user = get_current_user(request, db)
    ensure_role(user, VIEW_ROLES)
    statement = select(models.IntegrationLog).order_by(
        models.IntegrationLog.created_at.desc()
    )
    if integration_name:
        statement = statement.where(models.IntegrationLog.integration_name == integration_name)
    if entity_type:
        statement = statement.where(models.IntegrationLog.entity_type == entity_type)
    if status:
        statement = statement.where(models.IntegrationLog.status == status)
    return [_log_to_read(log) for log in db.execute(statement).scalars()]


@router.get("/approval/{approval_case_id}/payload")
def preview_approval_payload(
    approval_case_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    user = get_current_user(request, db)
    ensure_role(user, VIEW_ROLES)
    return build_approval_payload(db, approval_case_id)


@router.get("/quote/{quote_case_id}/payload")
def preview_quote_payload(
    quote_case_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    user = get_current_user(request, db)
    ensure_role(user, VIEW_ROLES)
    return build_quote_payload(db, quote_case_id)


@router.get("/tariff/{tariff_type}/{tariff_id}/payload")
def preview_tariff_payload(
    tariff_type: str,
    tariff_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    user = get_current_user(request, db)
    ensure_role(user, VIEW_ROLES)
    return build_tariff_payload(db, tariff_type, tariff_id)


@router.post("/export/approval/{approval_case_id}", response_model=IntegrationExportResponse)
def export_approval(
    approval_case_id: int,
    payload: IntegrationExportRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> IntegrationExportResponse:
    return _export_payload(
        db=db,
        request=request,
        integration_request=payload,
        entity_type="APPROVAL",
        entity_id=approval_case_id,
        payload=build_approval_payload(db, approval_case_id),
    )


@router.post("/export/quote/{quote_case_id}", response_model=IntegrationExportResponse)
def export_quote(
    quote_case_id: int,
    payload: IntegrationExportRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> IntegrationExportResponse:
    return _export_payload(
        db=db,
        request=request,
        integration_request=payload,
        entity_type="QUOTE",
        entity_id=quote_case_id,
        payload=build_quote_payload(db, quote_case_id),
    )


@router.get("/files/{log_id}/download")
def download_integration_file(
    log_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    ensure_role(user, VIEW_ROLES)
    log = db.get(models.IntegrationLog, log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Integration log not found")
    if not log.response_payload:
        raise HTTPException(status_code=404, detail="Integration file not found")
    try:
        response_payload = json.loads(log.response_payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=404, detail="Integration file not found") from exc

    file_path = response_payload.get("file_path")
    if not file_path:
        raise HTTPException(status_code=404, detail="Integration file not found")
    path = Path(file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Integration file not found")
    return FileResponse(
        path,
        media_type="application/json",
        filename=response_payload.get("file_name") or path.name,
    )
