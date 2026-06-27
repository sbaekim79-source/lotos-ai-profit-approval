from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class ApprovalCase(Base):
    __tablename__ = "approval_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_no: Mapped[str | None] = mapped_column(String, nullable=True)
    customer_name: Mapped[str] = mapped_column(String, nullable=False)
    trade_type: Mapped[str] = mapped_column(String, nullable=False)
    partner_name: Mapped[str | None] = mapped_column(String, nullable=True)
    shipper_name: Mapped[str | None] = mapped_column(String, nullable=True)
    pic: Mapped[str | None] = mapped_column(String, nullable=True)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    direction: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)
    point: Mapped[float] = mapped_column(Float, nullable=False)
    pol: Mapped[str | None] = mapped_column(String, nullable=True)
    pod: Mapped[str | None] = mapped_column(String, nullable=True)
    port: Mapped[str | None] = mapped_column(String, nullable=True)
    cargo_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    container_type: Mapped[str | None] = mapped_column(String, nullable=True)
    container_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_revenue_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    total_expense_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    gp_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    gp_rate: Mapped[float] = mapped_column(Float, nullable=False)
    net_revenue_ex_tax_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    net_expense_ex_tax_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    net_gp_rate_ex_tax: Mapped[float] = mapped_column(Float, nullable=False)
    minimum_gp_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[str] = mapped_column(String, nullable=False)
    executive_comment: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    findings: Mapped[list[ApprovalFinding]] = relationship(
        back_populates="approval_case",
        cascade="all, delete-orphan",
    )
    transport_tariffs: Mapped[list[TransportTariff]] = relationship(
        back_populates="approval_case"
    )
    customs_tariffs: Mapped[list[CustomsTariff]] = relationship(
        back_populates="approval_case"
    )
    productivity_points: Mapped[list[ProductivityPoint]] = relationship(
        back_populates="approval_case",
        cascade="all, delete-orphan",
    )
    workflow: Mapped[ApprovalWorkflow | None] = relationship(
        back_populates="approval_case",
        cascade="all, delete-orphan",
    )
    report_files: Mapped[list[ApprovalReportFile]] = relationship(
        back_populates="approval_case",
        cascade="all, delete-orphan",
    )


class ApprovalFinding(Base):
    __tablename__ = "approval_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    approval_case_id: Mapped[int] = mapped_column(
        ForeignKey("approval_cases.id"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    amount_jpy: Mapped[float | None] = mapped_column(Float, nullable=True)

    approval_case: Mapped[ApprovalCase] = relationship(back_populates="findings")


class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    approval_case_id: Mapped[int] = mapped_column(
        ForeignKey("approval_cases.id"),
        nullable=False,
        unique=True,
    )
    current_status: Mapped[str] = mapped_column(String, nullable=False)
    requested_by: Mapped[str | None] = mapped_column(String, nullable=True)
    team_approved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    director_approved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    ceo_approved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    rejected_by: Mapped[str | None] = mapped_column(String, nullable=True)
    returned_by: Mapped[str | None] = mapped_column(String, nullable=True)
    request_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    team_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    director_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    ceo_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    return_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    team_approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    director_approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ceo_approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    approval_case: Mapped[ApprovalCase] = relationship(back_populates="workflow")


class ApprovalReportFile(Base):
    __tablename__ = "approval_report_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    approval_case_id: Mapped[int] = mapped_column(
        ForeignKey("approval_cases.id"),
        nullable=False,
    )
    report_type: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    approval_case: Mapped[ApprovalCase] = relationship(back_populates="report_files")


class PartnerFeeRule(Base):
    __tablename__ = "partner_fee_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    partner_name: Mapped[str] = mapped_column(String, nullable=False)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    direction: Mapped[str] = mapped_column(String, nullable=False)
    container_type: Mapped[str | None] = mapped_column(String, nullable=True)
    unit_type: Mapped[str] = mapped_column(String, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    settlement_direction: Mapped[str] = mapped_column(String, nullable=False)
    special_condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class MinimumGPRule(Base):
    __tablename__ = "minimum_gp_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    minimum_gp_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class GPRateRule(Base):
    __tablename__ = "gp_rate_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trade_type: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    minimum_gp_rate: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )


class WorkCodeRule(Base):
    __tablename__ = "work_code_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    mode: Mapped[str | None] = mapped_column(String, nullable=True)
    direction: Mapped[str | None] = mapped_column(String, nullable=True)
    has_customs: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_transport: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_work: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    point: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )


class InternalResourceRule(Base):
    __tablename__ = "internal_resource_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    resource_type: Mapped[str] = mapped_column(String, nullable=False)
    port: Mapped[str] = mapped_column(String, nullable=False)
    location_name: Mapped[str | None] = mapped_column(String, nullable=True)
    vendor_name: Mapped[str | None] = mapped_column(String, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )


class RequiredChargeRule(Base):
    __tablename__ = "required_charge_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String, nullable=False)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    direction: Mapped[str] = mapped_column(String, nullable=False)
    charge_name: Mapped[str] = mapped_column(String, nullable=False)
    keywords: Mapped[str] = mapped_column(Text, nullable=False)
    required_when: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )


class ParserTemplate(Base):
    __tablename__ = "parser_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    template_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    mode: Mapped[str | None] = mapped_column(String, nullable=True)
    direction: Mapped[str | None] = mapped_column(String, nullable=True)
    file_type: Mapped[str] = mapped_column(String, nullable=False)
    customer_keyword: Mapped[str | None] = mapped_column(Text, nullable=True)
    partner_keyword: Mapped[str | None] = mapped_column(Text, nullable=True)
    revenue_section_keywords: Mapped[str] = mapped_column(Text, nullable=False)
    expense_section_keywords: Mapped[str] = mapped_column(Text, nullable=False)
    profit_keywords: Mapped[str] = mapped_column(Text, nullable=False)
    duty_keywords: Mapped[str] = mapped_column(Text, nullable=False)
    consumption_tax_keywords: Mapped[str] = mapped_column(Text, nullable=False)
    transport_keywords: Mapped[str] = mapped_column(Text, nullable=False)
    customs_keywords: Mapped[str] = mapped_column(Text, nullable=False)
    partner_fee_keywords: Mapped[str] = mapped_column(Text, nullable=False)
    food_keywords: Mapped[str] = mapped_column(Text, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    department: Mapped[str | None] = mapped_column(String, nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_name: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String, nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String, nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )


class ExportFile(Base):
    __tablename__ = "export_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    export_type: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )


class IntegrationSetting(Base):
    __tablename__ = "integration_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    integration_name: Mapped[str] = mapped_column(String, nullable=False)
    integration_type: Mapped[str] = mapped_column(String, nullable=False)
    endpoint_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    export_format: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )


class IntegrationLog(Base):
    __tablename__ = "integration_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    integration_name: Mapped[str] = mapped_column(String, nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    request_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )


class TransportTariff(Base):
    __tablename__ = "transport_tariffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    approval_case_id: Mapped[int | None] = mapped_column(
        ForeignKey("approval_cases.id"),
        nullable=True,
    )
    port: Mapped[str | None] = mapped_column(String, nullable=True)
    origin: Mapped[str | None] = mapped_column(String, nullable=True)
    destination: Mapped[str | None] = mapped_column(String, nullable=True)
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    container_type: Mapped[str | None] = mapped_column(String, nullable=True)
    container_count: Mapped[int] = mapped_column(Integer, nullable=False)
    vendor_name: Mapped[str | None] = mapped_column(String, nullable=True)
    transport_cost_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    highway_cost_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    transport_revenue_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    transport_gp_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    approval_case: Mapped[ApprovalCase | None] = relationship(
        back_populates="transport_tariffs"
    )


class CustomsTariff(Base):
    __tablename__ = "customs_tariffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    approval_case_id: Mapped[int | None] = mapped_column(
        ForeignKey("approval_cases.id"),
        nullable=True,
    )
    port: Mapped[str | None] = mapped_column(String, nullable=True)
    direction: Mapped[str] = mapped_column(String, nullable=False)
    self_customs: Mapped[bool] = mapped_column(Boolean, nullable=False)
    vendor_name: Mapped[str | None] = mapped_column(String, nullable=True)
    customs_revenue_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    customs_expense_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    customs_gp_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    food_declaration_fee_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    inspection_fee_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    approval_case: Mapped[ApprovalCase | None] = relationship(
        back_populates="customs_tariffs"
    )


class ProductivityPoint(Base):
    __tablename__ = "productivity_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    approval_case_id: Mapped[int] = mapped_column(
        ForeignKey("approval_cases.id"),
        nullable=False,
    )
    pic: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)
    point: Mapped[float] = mapped_column(Float, nullable=False)
    work_month: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    approval_case: Mapped[ApprovalCase] = relationship(
        back_populates="productivity_points"
    )


class ProfitUpload(Base):
    __tablename__ = "profit_uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    upload_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    saved_filename: Mapped[str] = mapped_column(String, nullable=False)
    file_ext: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )


class QuoteCase(Base):
    __tablename__ = "quote_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    trade_type: Mapped[str] = mapped_column(String, nullable=False)
    partner_name: Mapped[str | None] = mapped_column(String, nullable=True)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    direction: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)
    pol: Mapped[str | None] = mapped_column(String, nullable=True)
    pod: Mapped[str | None] = mapped_column(String, nullable=True)
    port: Mapped[str | None] = mapped_column(String, nullable=True)
    origin: Mapped[str | None] = mapped_column(String, nullable=True)
    destination: Mapped[str | None] = mapped_column(String, nullable=True)
    container_type: Mapped[str | None] = mapped_column(String, nullable=True)
    container_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_estimated_cost_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    total_recommended_revenue_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    expected_gp_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    expected_gp_rate: Mapped[float] = mapped_column(Float, nullable=False)
    minimum_gp_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    target_gp_rate: Mapped[float] = mapped_column(Float, nullable=False)
    decision_hint: Mapped[str] = mapped_column(String, nullable=False)
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    items: Mapped[list[QuoteItem]] = relationship(
        back_populates="quote_case",
        cascade="all, delete-orphan",
    )


class QuoteItem(Base):
    __tablename__ = "quote_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    quote_case_id: Mapped[int] = mapped_column(
        ForeignKey("quote_cases.id"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    basis: Mapped[str] = mapped_column(String, nullable=False)
    estimated_cost_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    recommended_revenue_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    gp_jpy: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    quote_case: Mapped[QuoteCase] = relationship(back_populates="items")


class OperationTestResult(Base):
    __tablename__ = "operation_test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    test_case_id: Mapped[str] = mapped_column(String, nullable=False)
    test_name: Mapped[str] = mapped_column(String, nullable=False)
    tester: Mapped[str | None] = mapped_column(String, nullable=True)
    result: Mapped[str] = mapped_column(String, nullable=False)
    issue: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    tested_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )


class ParserValidationCase(Base):
    __tablename__ = "parser_validation_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    upload_id: Mapped[str | None] = mapped_column(String, nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    expected_customer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    expected_code: Mapped[str | None] = mapped_column(String, nullable=True)
    expected_gp_jpy: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_decision: Mapped[str | None] = mapped_column(String, nullable=True)
    expected_transport_revenue_jpy: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_transport_expense_jpy: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_customs_revenue_jpy: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_customs_duty_jpy: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_consumption_tax_jpy: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_partner_fee_jpy: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_partner_fee_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    tolerance_jpy: Mapped[float] = mapped_column(Float, default=100, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )


class ParserValidationResult(Base):
    __tablename__ = "parser_validation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    validation_case_id: Mapped[int] = mapped_column(
        ForeignKey("parser_validation_cases.id"),
        nullable=False,
    )
    upload_id: Mapped[str | None] = mapped_column(String, nullable=True)
    parsed_customer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    parsed_code: Mapped[str | None] = mapped_column(String, nullable=True)
    parsed_gp_jpy: Mapped[float | None] = mapped_column(Float, nullable=True)
    parsed_decision: Mapped[str | None] = mapped_column(String, nullable=True)
    parsed_transport_revenue_jpy: Mapped[float | None] = mapped_column(Float, nullable=True)
    parsed_transport_expense_jpy: Mapped[float | None] = mapped_column(Float, nullable=True)
    parsed_customs_revenue_jpy: Mapped[float | None] = mapped_column(Float, nullable=True)
    parsed_customs_duty_jpy: Mapped[float | None] = mapped_column(Float, nullable=True)
    parsed_consumption_tax_jpy: Mapped[float | None] = mapped_column(Float, nullable=True)
    parsed_partner_fee_jpy: Mapped[float | None] = mapped_column(Float, nullable=True)
    parsed_partner_fee_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    result: Mapped[str] = mapped_column(String, nullable=False)
    diff_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )


class ParserImprovementSuggestion(Base):
    __tablename__ = "parser_improvement_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    validation_result_id: Mapped[int] = mapped_column(
        ForeignKey("parser_validation_results.id"),
        nullable=False,
    )
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("parser_templates.id"),
        nullable=True,
    )
    case_name: Mapped[str] = mapped_column(String, nullable=False)
    issue_type: Mapped[str] = mapped_column(String, nullable=False)
    field_name: Mapped[str] = mapped_column(String, nullable=False)
    current_value: Mapped[str | None] = mapped_column(String, nullable=True)
    expected_value: Mapped[str | None] = mapped_column(String, nullable=True)
    suggested_keyword: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggestion_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, default="OPEN", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
