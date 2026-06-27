from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel


TradeType = Literal["PARTNER", "SHIPPER", "FORWARDER"]
TransportMode = Literal["SEA", "AIR"]
Direction = Literal["EXPORT", "IMPORT"]
FindingStatus = Literal["OK", "WARN", "NG"]
Decision = Literal[
    "APPROVED",
    "CONDITIONAL_APPROVED",
    "CEO_REVIEW",
    "REJECTED",
]


class HealthResponse(BaseModel):
    status: str


class ChargeItem(BaseModel):
    name: str
    amount_jpy: float


class PartnerFeeInput(BaseModel):
    partner_name: str | None = None
    actual_fee_jpy: float = 0
    actual_fee_usd: float = 0
    bl_count: int = 1
    container_type: str | None = None
    container_count: int = 1
    special_condition: str | None = None


class ApprovalCaseInput(BaseModel):
    case_no: str | None = None
    customer_name: str
    trade_type: TradeType
    partner_name: str | None = None
    shipper_name: str | None = None
    pic: str | None = None

    mode: TransportMode
    direction: Direction

    has_customs: bool = False
    has_transport: bool = False
    has_work: bool = False
    is_project: bool = False

    pol: str | None = None
    pod: str | None = None
    port: str | None = None
    cargo_description: str | None = None
    container_type: str | None = None
    container_count: int = 1
    weight_kg: float | None = None
    cbm: float | None = None

    revenue_items: list[ChargeItem]
    expense_items: list[ChargeItem]

    customs_duty_jpy: float = 0
    consumption_tax_jpy: float = 0

    transport_revenue_jpy: float = 0
    transport_expense_jpy: float = 0
    customs_revenue_jpy: float = 0
    customs_expense_jpy: float = 0
    self_customs: bool = True
    customs_vendor_name: str | None = None
    warehouse_vendor_name: str | None = None
    transport_vendor_name: str | None = None
    external_customs_reason: str | None = None
    external_warehouse_reason: str | None = None
    external_transport_reason: str | None = None

    partner_fee: PartnerFeeInput | None = None


class Finding(BaseModel):
    category: str
    status: FindingStatus
    message: str
    amount_jpy: float | None = None


class ApprovalResult(BaseModel):
    customer_name: str
    code: str
    point: float
    total_revenue_jpy: float
    total_expense_jpy: float
    gp_jpy: float
    gp_rate: float
    net_revenue_ex_tax_jpy: float
    net_expense_ex_tax_jpy: float
    net_gp_rate_ex_tax: float
    minimum_gp_jpy: float
    decision: Decision
    findings: list[Finding]
    executive_comment: str


class ApprovalSaveResponse(BaseModel):
    approval_case_id: int
    result: ApprovalResult


class ApprovalListItem(BaseModel):
    id: int
    customer_name: str
    trade_type: str
    partner_name: str | None
    pic: str | None
    code: str
    point: float
    total_revenue_jpy: float
    total_expense_jpy: float
    gp_jpy: float
    gp_rate: float
    decision: str
    created_at: datetime


class ApprovalDetail(BaseModel):
    id: int
    case_no: str | None
    customer_name: str
    trade_type: str
    partner_name: str | None
    shipper_name: str | None
    pic: str | None
    mode: str
    direction: str
    code: str
    point: float
    pol: str | None
    pod: str | None
    port: str | None
    cargo_description: str | None
    container_type: str | None
    container_count: int
    total_revenue_jpy: float
    total_expense_jpy: float
    gp_jpy: float
    gp_rate: float
    net_revenue_ex_tax_jpy: float
    net_expense_ex_tax_jpy: float
    net_gp_rate_ex_tax: float
    minimum_gp_jpy: float
    decision: str
    executive_comment: str
    created_at: datetime
    findings: list[Finding]


class DecisionCounts(BaseModel):
    APPROVED: int = 0
    CONDITIONAL_APPROVED: int = 0
    CEO_REVIEW: int = 0
    REJECTED: int = 0


class ProductivityByPic(BaseModel):
    pic: str
    total_point: float
    case_count: int


class ProductivityMonthlyItem(BaseModel):
    pic: str
    work_month: str
    total_point: float
    case_count: int
    grade: str


class GpByCustomer(BaseModel):
    customer_name: str
    case_count: int
    total_revenue_jpy: float
    total_gp_jpy: float
    average_gp_rate: float


class PartnerSummary(BaseModel):
    partner_name: str
    case_count: int
    total_revenue_jpy: float
    total_gp_jpy: float
    average_gp_rate: float


class DashboardSummary(BaseModel):
    period_label: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    filters: dict[str, Any] = {}
    period_start: date | None = None
    period_end: date | None = None
    total_cases: int
    total_revenue_jpy: float
    total_expense_jpy: float
    total_gp_jpy: float
    average_gp_rate: float
    decision_counts: DecisionCounts
    code_counts: dict[str, int]
    productivity_by_pic: list[ProductivityByPic]
    gp_by_customer: list[GpByCustomer]
    partner_summary: list[PartnerSummary]


class MonthlyPerformanceItem(BaseModel):
    work_month: str
    case_count: int = 0
    total_cases: int
    total_revenue_jpy: float
    total_expense_jpy: float
    total_gp_jpy: float
    average_gp_rate: float
    approved_count: int
    conditional_count: int = 0
    conditional_approved_count: int
    ceo_review_count: int
    rejected_count: int


class LowMarginItem(BaseModel):
    id: int
    customer_name: str
    partner_name: str | None
    trade_type: str
    code: str
    gp_jpy: float
    gp_rate: float
    net_gp_rate_ex_tax: float
    decision: str
    executive_comment: str
    created_at: datetime


class PartnerFeeRuleCreate(BaseModel):
    partner_name: str
    mode: str
    direction: str
    container_type: str | None = None
    unit_type: str
    currency: str
    amount: float
    settlement_direction: str
    special_condition: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    is_active: bool = True
    note: str | None = None


class PartnerFeeRuleRead(PartnerFeeRuleCreate):
    id: int


class MinimumGPRuleCreate(BaseModel):
    code: str
    minimum_gp_jpy: float
    description: str | None = None
    is_active: bool = True


class MinimumGPRuleRead(MinimumGPRuleCreate):
    id: int


class GPRateRuleCreate(BaseModel):
    trade_type: str
    minimum_gp_rate: float
    description: str | None = None
    is_active: bool = True


class GPRateRuleRead(GPRateRuleCreate):
    id: int


class WorkCodeRuleCreate(BaseModel):
    code: str
    name: str
    mode: str | None = None
    direction: str | None = None
    has_customs: bool = False
    has_transport: bool = False
    has_work: bool = False
    point: float
    description: str | None = None
    is_active: bool = True


class WorkCodeRuleRead(WorkCodeRuleCreate):
    id: int


class InternalResourceRuleCreate(BaseModel):
    resource_type: str
    port: str
    location_name: str | None = None
    vendor_name: str | None = None
    priority: int = 1
    mandatory: bool = True
    description: str | None = None
    is_active: bool = True


class InternalResourceRuleRead(InternalResourceRuleCreate):
    id: int


class RequiredChargeRuleCreate(BaseModel):
    code: str
    mode: str = "ANY"
    direction: str = "ANY"
    charge_name: str
    keywords: str
    required_when: str
    severity: str = "WARN"
    description: str | None = None
    is_active: bool = True


class RequiredChargeRuleRead(RequiredChargeRuleCreate):
    id: int


class ParserTemplateCreate(BaseModel):
    template_name: str
    description: str | None = None
    mode: str | None = None
    direction: str | None = None
    file_type: str = "ANY"
    customer_keyword: str | None = None
    partner_keyword: str | None = None
    revenue_section_keywords: str
    expense_section_keywords: str
    profit_keywords: str
    duty_keywords: str
    consumption_tax_keywords: str
    transport_keywords: str
    customs_keywords: str
    partner_fee_keywords: str
    food_keywords: str
    is_default: bool = False
    is_active: bool = True


class ParserTemplateRead(ParserTemplateCreate):
    id: int


class SeedDefaultsResponse(BaseModel):
    partner_fee_rules_created: int
    minimum_gp_rules_upserted: int
    gp_rate_rules_upserted: int = 0
    work_code_rules_upserted: int = 0
    internal_resource_rules_upserted: int = 0
    required_charge_rules_upserted: int = 0
    parser_templates_upserted: int = 0
    users_upserted: int = 0
    parser_validation_cases_upserted: int = 0


class TransportTariffItem(BaseModel):
    id: int
    approval_case_id: int | None
    port: str | None
    origin: str | None
    destination: str | None
    distance_km: float | None
    container_type: str | None
    container_count: int
    vendor_name: str | None
    transport_cost_jpy: float
    highway_cost_jpy: float
    transport_revenue_jpy: float
    transport_gp_jpy: float
    created_at: datetime


class TransportTariffSummary(BaseModel):
    origin: str | None
    destination: str | None
    container_type: str | None
    case_count: int
    avg_transport_cost_jpy: float
    min_transport_cost_jpy: float
    max_transport_cost_jpy: float
    avg_transport_revenue_jpy: float
    avg_transport_gp_jpy: float


class CustomsTariffItem(BaseModel):
    id: int
    approval_case_id: int | None
    port: str | None
    direction: str
    self_customs: bool
    vendor_name: str | None
    customs_revenue_jpy: float
    customs_expense_jpy: float
    customs_gp_jpy: float
    food_declaration_fee_jpy: float
    inspection_fee_jpy: float
    created_at: datetime


class CustomsTariffSummary(BaseModel):
    port: str | None
    direction: str
    self_customs: bool
    case_count: int
    avg_customs_revenue_jpy: float
    avg_customs_expense_jpy: float
    avg_customs_gp_jpy: float
    avg_food_declaration_fee_jpy: float
    avg_inspection_fee_jpy: float


class ProfitUploadResponse(BaseModel):
    upload_id: str
    original_filename: str
    saved_filename: str
    file_ext: str
    status: str


class ProfitUploadItem(BaseModel):
    upload_id: str
    original_filename: str
    saved_filename: str
    file_ext: str
    file_size: int
    created_at: datetime


class ProfitParseResponse(BaseModel):
    upload_id: str
    original_filename: str
    parse_result: dict[str, Any]


class ProfitMapResponse(BaseModel):
    upload_id: str
    original_filename: str
    candidate: ApprovalCaseInput
    parsing_confidence: float
    confidence: float | None = None
    warnings: list[str]
    template_used: dict[str, Any] | None = None


class QuoteRequest(BaseModel):
    customer_name: str | None = None
    trade_type: TradeType
    partner_name: str | None = None
    mode: TransportMode
    direction: Direction
    code: str
    pol: str | None = None
    pod: str | None = None
    port: str | None = None
    origin: str | None = None
    destination: str | None = None
    container_type: str | None = None
    container_count: int = 1
    cbm: float | None = None
    weight_kg: float | None = None
    cargo_description: str | None = None
    include_customs: bool = False
    include_transport: bool = False
    include_warehouse: bool = False
    target_gp_rate: float | None = None
    manual_transport_cost_jpy: float | None = None
    manual_customs_cost_jpy: float | None = None
    manual_partner_fee_jpy: float | None = None


class QuoteCostItem(BaseModel):
    category: str
    name: str
    basis: str
    estimated_cost_jpy: float
    recommended_revenue_jpy: float
    gp_jpy: float
    source: str
    note: str | None = None


class QuoteResult(BaseModel):
    customer_name: str | None = None
    code: str
    trade_type: str
    total_estimated_cost_jpy: float
    total_recommended_revenue_jpy: float
    expected_gp_jpy: float
    expected_gp_rate: float
    minimum_gp_jpy: float
    target_gp_rate: float
    decision_hint: str
    items: list[QuoteCostItem]
    warnings: list[str]
    executive_summary: str


class QuoteSaveResponse(BaseModel):
    quote_case_id: int
    result: QuoteResult


class QuoteListItem(BaseModel):
    id: int
    customer_name: str | None
    trade_type: str
    partner_name: str | None
    mode: str
    direction: str
    code: str
    origin: str | None = None
    destination: str | None = None
    container_type: str | None = None
    total_estimated_cost_jpy: float
    total_recommended_revenue_jpy: float
    expected_gp_jpy: float
    expected_gp_rate: float
    minimum_gp_jpy: float
    target_gp_rate: float
    decision_hint: str
    created_at: datetime


class QuoteDetail(QuoteListItem):
    pol: str | None
    pod: str | None
    port: str | None
    origin: str | None
    destination: str | None
    container_type: str | None
    container_count: int
    executive_summary: str
    items: list[QuoteCostItem]


class WorkflowListItem(BaseModel):
    workflow_id: int
    approval_case_id: int
    customer_name: str
    code: str
    gp_jpy: float
    decision: str
    current_status: str
    requested_by: str | None
    created_at: datetime
    submitted_at: datetime | None


class WorkflowInfo(BaseModel):
    workflow_id: int
    approval_case_id: int
    current_status: str
    requested_by: str | None = None
    team_approved_by: str | None = None
    director_approved_by: str | None = None
    ceo_approved_by: str | None = None
    rejected_by: str | None = None
    returned_by: str | None = None
    request_comment: str | None = None
    team_comment: str | None = None
    director_comment: str | None = None
    ceo_comment: str | None = None
    reject_reason: str | None = None
    return_reason: str | None = None
    submitted_at: datetime | None = None
    team_approved_at: datetime | None = None
    director_approved_at: datetime | None = None
    ceo_approved_at: datetime | None = None
    rejected_at: datetime | None = None
    returned_at: datetime | None = None
    created_at: datetime


class WorkflowDetail(BaseModel):
    workflow: WorkflowInfo
    approval_case: ApprovalDetail
    findings: list[Finding]


class WorkflowSubmitRequest(BaseModel):
    requested_by: str | None = None
    request_comment: str | None = None


class WorkflowApproveRequest(BaseModel):
    approved_by: str | None = None
    comment: str | None = None


class WorkflowRejectRequest(BaseModel):
    rejected_by: str | None = None
    reject_reason: str


class WorkflowReturnRequest(BaseModel):
    returned_by: str | None = None
    return_reason: str


class UserCreate(BaseModel):
    username: str
    display_name: str
    email: str | None = None
    role: Literal["STAFF", "TEAM_MANAGER", "DIRECTOR", "CEO", "ADMIN"]
    department: str | None = None
    password: str | None = None
    is_active: bool = True


class UserRead(BaseModel):
    id: int
    username: str
    display_name: str
    email: str | None = None
    role: Literal["STAFF", "TEAM_MANAGER", "DIRECTOR", "CEO", "ADMIN"]
    department: str | None = None
    is_active: bool = True


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthUser(BaseModel):
    username: str
    display_name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUser


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ApprovalReportFileRead(BaseModel):
    report_file_id: int
    approval_case_id: int
    report_type: str
    file_name: str
    download_url: str
    created_by: str | None = None
    created_at: datetime | None = None


class AuditLogRead(BaseModel):
    id: int
    user_name: str | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    detail: str | None = None
    ip_address: str | None = None
    created_at: datetime


class BackupResponse(BaseModel):
    status: str
    backup_file: str | None = None
    message: str | None = None


class BackupFileItem(BaseModel):
    file_name: str
    file_path: str
    file_size: int
    created_at: datetime


class SystemStatusResponse(BaseModel):
    database: str
    database_type: str
    database_url_masked: str
    app_env: str
    upload_folder_exists: bool
    generated_reports_folder_exists: bool
    logs_folder_exists: bool
    backup_folder_exists: bool
    approval_case_count: int
    workflow_count: int
    quote_count: int
    report_file_count: int


class IntegrationSettingCreate(BaseModel):
    integration_name: str
    integration_type: Literal["FILE_EXPORT", "API", "WEBHOOK"]
    endpoint_url: str | None = None
    export_format: Literal["JSON", "CSV", "EXCEL"] = "JSON"
    is_active: bool = True
    description: str | None = None


class IntegrationSettingRead(IntegrationSettingCreate):
    id: int
    created_at: datetime


class IntegrationLogRead(BaseModel):
    id: int
    integration_name: str
    entity_type: Literal["APPROVAL", "QUOTE", "TARIFF", "WORKFLOW"]
    entity_id: int
    status: Literal["SUCCESS", "FAIL", "PENDING"]
    request_payload: str | None = None
    response_payload: str | None = None
    error_message: str | None = None
    created_by: str | None = None
    created_at: datetime


class IntegrationExportRequest(BaseModel):
    integration_name: str
    export_format: Literal["JSON", "CSV", "EXCEL"] = "JSON"


class IntegrationExportResponse(BaseModel):
    status: Literal["SUCCESS", "FAIL", "PENDING"]
    file_name: str | None = None
    download_url: str | None = None
    log_id: int


class OperationTestResultCreate(BaseModel):
    test_case_id: str
    test_name: str
    tester: str | None = None
    result: Literal["PASS", "FAIL", "HOLD"]
    issue: str | None = None
    action_taken: str | None = None
    tested_at: datetime | None = None


class OperationTestResultRead(OperationTestResultCreate):
    id: int
    created_at: datetime


class ParserValidationCaseCreate(BaseModel):
    case_name: str
    upload_id: str | None = None
    original_filename: str | None = None
    expected_customer_name: str | None = None
    expected_code: str | None = None
    expected_gp_jpy: float | None = None
    expected_decision: str | None = None
    expected_transport_revenue_jpy: float | None = None
    expected_transport_expense_jpy: float | None = None
    expected_customs_revenue_jpy: float | None = None
    expected_customs_duty_jpy: float | None = None
    expected_consumption_tax_jpy: float | None = None
    expected_partner_fee_jpy: float | None = None
    expected_partner_fee_usd: float | None = None
    tolerance_jpy: float = 100
    is_active: bool = True


class ParserValidationCaseRead(ParserValidationCaseCreate):
    id: int
    created_at: datetime


class ParserValidationRunRequest(BaseModel):
    upload_id: str


class ParserValidationRunAllRequest(BaseModel):
    upload_mapping: dict[str, str]


class ParserValidationResultRead(BaseModel):
    id: int
    validation_case_id: int
    upload_id: str | None = None
    parsed_customer_name: str | None = None
    parsed_code: str | None = None
    parsed_gp_jpy: float | None = None
    parsed_decision: str | None = None
    parsed_transport_revenue_jpy: float | None = None
    parsed_transport_expense_jpy: float | None = None
    parsed_customs_revenue_jpy: float | None = None
    parsed_customs_duty_jpy: float | None = None
    parsed_consumption_tax_jpy: float | None = None
    parsed_partner_fee_jpy: float | None = None
    parsed_partner_fee_usd: float | None = None
    confidence: float | None = None
    result: Literal["PASS", "FAIL", "PARTIAL"]
    diff_summary: str | None = None
    created_at: datetime


class ParserImprovementSuggestionRead(BaseModel):
    id: int
    validation_result_id: int
    template_id: int | None = None
    case_name: str
    issue_type: Literal[
        "MISSING_KEYWORD",
        "WRONG_SECTION",
        "AMOUNT_MISMATCH",
        "CODE_MISMATCH",
        "PARTNER_FEE_MISMATCH",
        "TAX_MISMATCH",
        "TRANSPORT_MISMATCH",
        "CUSTOMS_MISMATCH",
    ]
    field_name: str
    current_value: str | None = None
    expected_value: str | None = None
    suggested_keyword: str | None = None
    suggestion_text: str
    status: Literal["OPEN", "APPLIED", "REJECTED"]
    created_at: datetime
    applied_at: datetime | None = None
