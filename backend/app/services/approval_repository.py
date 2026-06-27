from sqlalchemy.orm import Session

from app import models
from app.schemas import ApprovalCaseInput, ApprovalResult


def save_approval_case(
    db: Session,
    case_input: ApprovalCaseInput,
    result: ApprovalResult,
) -> models.ApprovalCase:
    approval_case = models.ApprovalCase(
        case_no=case_input.case_no,
        customer_name=case_input.customer_name,
        trade_type=case_input.trade_type,
        partner_name=case_input.partner_name,
        shipper_name=case_input.shipper_name,
        pic=case_input.pic,
        mode=case_input.mode,
        direction=case_input.direction,
        code=result.code,
        point=result.point,
        pol=case_input.pol,
        pod=case_input.pod,
        port=case_input.port,
        cargo_description=case_input.cargo_description,
        container_type=case_input.container_type,
        container_count=case_input.container_count,
        total_revenue_jpy=result.total_revenue_jpy,
        total_expense_jpy=result.total_expense_jpy,
        gp_jpy=result.gp_jpy,
        gp_rate=result.gp_rate,
        net_revenue_ex_tax_jpy=result.net_revenue_ex_tax_jpy,
        net_expense_ex_tax_jpy=result.net_expense_ex_tax_jpy,
        net_gp_rate_ex_tax=result.net_gp_rate_ex_tax,
        minimum_gp_jpy=result.minimum_gp_jpy,
        decision=result.decision,
        executive_comment=result.executive_comment,
    )
    db.add(approval_case)
    db.flush()

    db.add(
        models.ApprovalWorkflow(
            approval_case_id=approval_case.id,
            current_status="DRAFT",
        )
    )

    for finding in result.findings:
        db.add(
            models.ApprovalFinding(
                approval_case_id=approval_case.id,
                category=finding.category,
                status=finding.status,
                message=finding.message,
                amount_jpy=finding.amount_jpy,
            )
        )

    if case_input.pic:
        created_at = approval_case.created_at
        db.add(
            models.ProductivityPoint(
                approval_case_id=approval_case.id,
                pic=case_input.pic,
                code=result.code,
                point=result.point,
                work_month=created_at.strftime("%Y-%m"),
            )
        )

    if (
        case_input.has_transport
        or case_input.transport_revenue_jpy > 0
        or case_input.transport_expense_jpy > 0
    ):
        db.add(
            models.TransportTariff(
                approval_case_id=approval_case.id,
                port=case_input.port,
                origin=case_input.pol,
                destination=case_input.pod,
                distance_km=None,
                container_type=case_input.container_type,
                container_count=case_input.container_count,
                vendor_name=case_input.transport_vendor_name,
                transport_cost_jpy=case_input.transport_expense_jpy,
                highway_cost_jpy=0,
                transport_revenue_jpy=case_input.transport_revenue_jpy,
                transport_gp_jpy=(
                    case_input.transport_revenue_jpy
                    - case_input.transport_expense_jpy
                ),
            )
        )

    if (
        case_input.has_customs
        or case_input.customs_revenue_jpy > 0
        or case_input.customs_expense_jpy > 0
    ):
        db.add(
            models.CustomsTariff(
                approval_case_id=approval_case.id,
                port=case_input.port,
                direction=case_input.direction,
                self_customs=case_input.self_customs,
                vendor_name=case_input.customs_vendor_name,
                customs_revenue_jpy=case_input.customs_revenue_jpy,
                customs_expense_jpy=case_input.customs_expense_jpy,
                customs_gp_jpy=(
                    case_input.customs_revenue_jpy - case_input.customs_expense_jpy
                ),
                food_declaration_fee_jpy=0,
                inspection_fee_jpy=0,
            )
        )

    db.commit()
    db.refresh(approval_case)
    return approval_case
