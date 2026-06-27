from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import models
from app.database import get_db
from app.schemas import (
    ApprovalDetail,
    Finding,
    WorkflowApproveRequest,
    WorkflowDetail,
    WorkflowInfo,
    WorkflowListItem,
    WorkflowRejectRequest,
    WorkflowReturnRequest,
    WorkflowSubmitRequest,
)
from app.services.auth import actor_name, ensure_role, get_current_user
from app.services.audit_service import create_audit_log


router = APIRouter(prefix="/api/workflows", tags=["Workflows"])


def now_utc() -> datetime:
    return datetime.now(UTC)


@router.get("", response_model=list[WorkflowListItem])
def list_workflows(
    status: str | None = None,
    pic: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
) -> list[WorkflowListItem]:
    statement = (
        select(models.ApprovalWorkflow)
        .join(models.ApprovalWorkflow.approval_case)
        .options(selectinload(models.ApprovalWorkflow.approval_case))
        .order_by(models.ApprovalWorkflow.created_at.desc())
    )
    if status is not None:
        statement = statement.where(models.ApprovalWorkflow.current_status == status)
    if pic is not None:
        statement = statement.where(models.ApprovalCase.pic == pic)
    if start_date is not None:
        statement = statement.where(
            models.ApprovalWorkflow.created_at
            >= datetime.fromisoformat(start_date)
        )
    if end_date is not None:
        statement = statement.where(
            models.ApprovalWorkflow.created_at
            <= datetime.fromisoformat(end_date).replace(hour=23, minute=59, second=59)
        )
    return [_to_workflow_list_item(workflow) for workflow in db.execute(statement).scalars()]


@router.get("/{workflow_id}", response_model=WorkflowDetail)
def get_workflow_detail(
    workflow_id: int,
    db: Session = Depends(get_db),
) -> WorkflowDetail:
    workflow = _get_workflow_or_404(db, workflow_id)
    return _to_workflow_detail(workflow)


@router.post("/{workflow_id}/submit", response_model=WorkflowInfo)
def submit_workflow(
    workflow_id: int,
    payload: WorkflowSubmitRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> WorkflowInfo:
    user = get_current_user(request, db)
    ensure_role(user, {"STAFF"})
    workflow = _get_workflow_or_404(db, workflow_id)
    _ensure_status(workflow, {"DRAFT", "RETURNED"}, "submit")
    workflow.current_status = "SUBMITTED"
    workflow.requested_by = actor_name(user)
    workflow.request_comment = payload.request_comment
    workflow.submitted_at = now_utc()
    db.commit()
    db.refresh(workflow)
    _audit_workflow(db, request, actor_name(user), "WORKFLOW_SUBMIT", workflow, payload.request_comment)
    return _to_workflow_info(workflow)


@router.post("/{workflow_id}/team-approve", response_model=WorkflowInfo)
def team_approve_workflow(
    workflow_id: int,
    payload: WorkflowApproveRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> WorkflowInfo:
    user = get_current_user(request, db)
    ensure_role(user, {"TEAM_MANAGER"})
    workflow = _get_workflow_or_404(db, workflow_id)
    _ensure_status(workflow, {"SUBMITTED"}, "team approve")
    workflow.current_status = "TEAM_APPROVED"
    workflow.team_approved_by = actor_name(user)
    workflow.team_comment = payload.comment
    workflow.team_approved_at = now_utc()
    db.commit()
    db.refresh(workflow)
    _audit_workflow(db, request, actor_name(user), "WORKFLOW_TEAM_APPROVE", workflow, payload.comment)
    return _to_workflow_info(workflow)


@router.post("/{workflow_id}/director-approve", response_model=WorkflowInfo)
def director_approve_workflow(
    workflow_id: int,
    payload: WorkflowApproveRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> WorkflowInfo:
    user = get_current_user(request, db)
    ensure_role(user, {"DIRECTOR"})
    workflow = _get_workflow_or_404(db, workflow_id)
    _ensure_status(workflow, {"TEAM_APPROVED"}, "director approve")
    workflow.current_status = "DIRECTOR_APPROVED"
    workflow.director_approved_by = actor_name(user)
    workflow.director_comment = payload.comment
    workflow.director_approved_at = now_utc()
    db.commit()
    db.refresh(workflow)
    _audit_workflow(db, request, actor_name(user), "WORKFLOW_DIRECTOR_APPROVE", workflow, payload.comment)
    return _to_workflow_info(workflow)


@router.post("/{workflow_id}/ceo-approve", response_model=WorkflowInfo)
def ceo_approve_workflow(
    workflow_id: int,
    payload: WorkflowApproveRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> WorkflowInfo:
    user = get_current_user(request, db)
    ensure_role(user, {"CEO"})
    workflow = _get_workflow_or_404(db, workflow_id)
    _ensure_status(workflow, {"DIRECTOR_APPROVED"}, "ceo approve")
    workflow.current_status = "CEO_APPROVED"
    workflow.ceo_approved_by = actor_name(user)
    workflow.ceo_comment = payload.comment
    workflow.ceo_approved_at = now_utc()
    db.commit()
    db.refresh(workflow)
    _audit_workflow(db, request, actor_name(user), "WORKFLOW_CEO_APPROVE", workflow, payload.comment)
    return _to_workflow_info(workflow)


@router.post("/{workflow_id}/reject", response_model=WorkflowInfo)
def reject_workflow(
    workflow_id: int,
    payload: WorkflowRejectRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> WorkflowInfo:
    user = get_current_user(request, db)
    ensure_role(user, {"TEAM_MANAGER", "DIRECTOR", "CEO"})
    workflow = _get_workflow_or_404(db, workflow_id)
    if workflow.current_status == "CEO_APPROVED":
        raise HTTPException(status_code=400, detail="CEO approved workflow cannot be rejected")
    workflow.current_status = "REJECTED"
    workflow.rejected_by = actor_name(user)
    workflow.reject_reason = payload.reject_reason
    workflow.rejected_at = now_utc()
    db.commit()
    db.refresh(workflow)
    _audit_workflow(db, request, actor_name(user), "WORKFLOW_REJECT", workflow, payload.reject_reason)
    return _to_workflow_info(workflow)


@router.post("/{workflow_id}/return", response_model=WorkflowInfo)
def return_workflow(
    workflow_id: int,
    payload: WorkflowReturnRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> WorkflowInfo:
    user = get_current_user(request, db)
    ensure_role(user, {"TEAM_MANAGER", "DIRECTOR", "CEO"})
    workflow = _get_workflow_or_404(db, workflow_id)
    _ensure_status(
        workflow,
        {"SUBMITTED", "TEAM_APPROVED", "DIRECTOR_APPROVED"},
        "return",
    )
    workflow.current_status = "RETURNED"
    workflow.returned_by = actor_name(user)
    workflow.return_reason = payload.return_reason
    workflow.returned_at = now_utc()
    db.commit()
    db.refresh(workflow)
    _audit_workflow(db, request, actor_name(user), "WORKFLOW_RETURN", workflow, payload.return_reason)
    return _to_workflow_info(workflow)


def _audit_workflow(
    db: Session,
    request: Request,
    user_name: str,
    action: str,
    workflow: models.ApprovalWorkflow,
    detail: str | None,
) -> None:
    create_audit_log(
        db,
        user_name=user_name,
        action=action,
        entity_type="APPROVAL_WORKFLOW",
        entity_id=workflow.id,
        detail=detail,
        ip_address=request.client.host if request.client else None,
    )


def _get_workflow_or_404(db: Session, workflow_id: int) -> models.ApprovalWorkflow:
    workflow = db.execute(
        select(models.ApprovalWorkflow)
        .options(
            selectinload(models.ApprovalWorkflow.approval_case).selectinload(
                models.ApprovalCase.findings
            )
        )
        .where(models.ApprovalWorkflow.id == workflow_id)
    ).scalar_one_or_none()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


def _ensure_status(
    workflow: models.ApprovalWorkflow,
    allowed: set[str],
    action: str,
) -> None:
    if workflow.current_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot {action} workflow in {workflow.current_status} status",
        )


def _to_workflow_list_item(workflow: models.ApprovalWorkflow) -> WorkflowListItem:
    approval_case = workflow.approval_case
    return WorkflowListItem(
        workflow_id=workflow.id,
        approval_case_id=workflow.approval_case_id,
        customer_name=approval_case.customer_name,
        code=approval_case.code,
        gp_jpy=approval_case.gp_jpy,
        decision=approval_case.decision,
        current_status=workflow.current_status,
        requested_by=workflow.requested_by,
        created_at=workflow.created_at,
        submitted_at=workflow.submitted_at,
    )


def _to_workflow_info(workflow: models.ApprovalWorkflow) -> WorkflowInfo:
    return WorkflowInfo(
        workflow_id=workflow.id,
        approval_case_id=workflow.approval_case_id,
        current_status=workflow.current_status,
        requested_by=workflow.requested_by,
        team_approved_by=workflow.team_approved_by,
        director_approved_by=workflow.director_approved_by,
        ceo_approved_by=workflow.ceo_approved_by,
        rejected_by=workflow.rejected_by,
        returned_by=workflow.returned_by,
        request_comment=workflow.request_comment,
        team_comment=workflow.team_comment,
        director_comment=workflow.director_comment,
        ceo_comment=workflow.ceo_comment,
        reject_reason=workflow.reject_reason,
        return_reason=workflow.return_reason,
        submitted_at=workflow.submitted_at,
        team_approved_at=workflow.team_approved_at,
        director_approved_at=workflow.director_approved_at,
        ceo_approved_at=workflow.ceo_approved_at,
        rejected_at=workflow.rejected_at,
        returned_at=workflow.returned_at,
        created_at=workflow.created_at,
    )


def _to_approval_detail(approval_case: models.ApprovalCase) -> ApprovalDetail:
    return ApprovalDetail(
        id=approval_case.id,
        case_no=approval_case.case_no,
        customer_name=approval_case.customer_name,
        trade_type=approval_case.trade_type,
        partner_name=approval_case.partner_name,
        shipper_name=approval_case.shipper_name,
        pic=approval_case.pic,
        mode=approval_case.mode,
        direction=approval_case.direction,
        code=approval_case.code,
        point=approval_case.point,
        pol=approval_case.pol,
        pod=approval_case.pod,
        port=approval_case.port,
        cargo_description=approval_case.cargo_description,
        container_type=approval_case.container_type,
        container_count=approval_case.container_count,
        total_revenue_jpy=approval_case.total_revenue_jpy,
        total_expense_jpy=approval_case.total_expense_jpy,
        gp_jpy=approval_case.gp_jpy,
        gp_rate=approval_case.gp_rate,
        net_revenue_ex_tax_jpy=approval_case.net_revenue_ex_tax_jpy,
        net_expense_ex_tax_jpy=approval_case.net_expense_ex_tax_jpy,
        net_gp_rate_ex_tax=approval_case.net_gp_rate_ex_tax,
        minimum_gp_jpy=approval_case.minimum_gp_jpy,
        decision=approval_case.decision,
        executive_comment=approval_case.executive_comment,
        created_at=approval_case.created_at,
        findings=[
            Finding(
                category=finding.category,
                status=finding.status,
                message=finding.message,
                amount_jpy=finding.amount_jpy,
            )
            for finding in approval_case.findings
        ],
    )


def _to_workflow_detail(workflow: models.ApprovalWorkflow) -> WorkflowDetail:
    approval_case = workflow.approval_case
    findings = [
        Finding(
            category=finding.category,
            status=finding.status,
            message=finding.message,
            amount_jpy=finding.amount_jpy,
        )
        for finding in approval_case.findings
    ]
    return WorkflowDetail(
        workflow=_to_workflow_info(workflow),
        approval_case=_to_approval_detail(approval_case),
        findings=findings,
    )
