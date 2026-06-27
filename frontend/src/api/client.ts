import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8010",
});

export const DEFAULT_USERNAME = "admin";

export const USER_ROLES: Record<string, string> = {
  admin: "ADMIN",
  staff: "STAFF",
  team_manager: "TEAM_MANAGER",
  director: "DIRECTOR",
  ceo: "CEO",
};

export type AuthUser = {
  username: string;
  display_name: string;
  role: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: AuthUser;
};

export function getAccessToken() {
  return localStorage.getItem("lotos_access_token");
}

export function getStoredAuthUser(): AuthUser | null {
  const raw = localStorage.getItem("lotos_auth_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function storeAuthSession(token: string, user: AuthUser) {
  localStorage.setItem("lotos_access_token", token);
  localStorage.setItem("lotos_auth_user", JSON.stringify(user));
  localStorage.setItem("lotos_username", user.username);
}

export function clearAuthSession() {
  localStorage.removeItem("lotos_access_token");
  localStorage.removeItem("lotos_auth_user");
}

export function getCurrentUsername() {
  return getStoredAuthUser()?.username ?? localStorage.getItem("lotos_username") ?? DEFAULT_USERNAME;
}

export function getCurrentRole() {
  return getStoredAuthUser()?.role ?? USER_ROLES[getCurrentUsername()] ?? "ADMIN";
}

api.interceptors.request.use((config) => {
  config.headers = config.headers ?? {};
  const headers = config.headers as Record<string, string>;
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  headers["X-USER-NAME"] = getCurrentUsername();
  return config;
});

export type Finding = {
  category: string;
  status: "OK" | "WARN" | "NG";
  message: string;
  amount_jpy: number | null;
};

export type ChargeItem = {
  name: string;
  amount_jpy: number;
};

export type PartnerFeeInput = {
  partner_name: string | null;
  actual_fee_jpy: number;
  actual_fee_usd: number;
  bl_count: number;
  container_type: string | null;
  container_count: number;
  special_condition: string | null;
};

export type ApprovalCaseInput = {
  case_no?: string | null;
  customer_name: string;
  trade_type: "PARTNER" | "SHIPPER" | "FORWARDER";
  partner_name: string | null;
  shipper_name: string | null;
  pic: string | null;
  mode: "SEA" | "AIR";
  direction: "EXPORT" | "IMPORT";
  has_customs: boolean;
  has_transport: boolean;
  has_work: boolean;
  is_project: boolean;
  pol: string | null;
  pod: string | null;
  port: string | null;
  cargo_description: string | null;
  container_type: string | null;
  container_count: number;
  weight_kg?: number | null;
  cbm?: number | null;
  revenue_items: ChargeItem[];
  expense_items: ChargeItem[];
  customs_duty_jpy: number;
  consumption_tax_jpy: number;
  transport_revenue_jpy: number;
  transport_expense_jpy: number;
  customs_revenue_jpy: number;
  customs_expense_jpy: number;
  self_customs: boolean;
  customs_vendor_name: string | null;
  warehouse_vendor_name: string | null;
  transport_vendor_name: string | null;
  external_customs_reason: string | null;
  external_warehouse_reason: string | null;
  external_transport_reason: string | null;
  partner_fee: PartnerFeeInput | null;
};

export type ApprovalResult = {
  customer_name: string;
  code: string;
  point: number;
  total_revenue_jpy: number;
  total_expense_jpy: number;
  gp_jpy: number;
  gp_rate: number;
  net_revenue_ex_tax_jpy: number;
  net_expense_ex_tax_jpy: number;
  net_gp_rate_ex_tax: number;
  minimum_gp_jpy: number;
  decision: string;
  findings: Finding[];
  executive_comment: string;
};

export type ApprovalListItem = {
  id: number;
  customer_name: string;
  trade_type: string;
  partner_name: string | null;
  pic: string | null;
  code: string;
  point: number;
  total_revenue_jpy: number;
  total_expense_jpy: number;
  gp_jpy: number;
  gp_rate: number;
  decision: string;
  created_at: string;
};

export type ApprovalDetail = ApprovalListItem & {
  case_no: string | null;
  shipper_name: string | null;
  mode: string;
  direction: string;
  pol: string | null;
  pod: string | null;
  port: string | null;
  cargo_description: string | null;
  container_type: string | null;
  container_count: number;
  net_revenue_ex_tax_jpy: number;
  net_expense_ex_tax_jpy: number;
  net_gp_rate_ex_tax: number;
  minimum_gp_jpy: number;
  executive_comment: string;
  findings: Finding[];
};

export type DashboardSummary = {
  period_label: string | null;
  start_date: string | null;
  end_date: string | null;
  filters: Record<string, string>;
  period_start: string | null;
  period_end: string | null;
  total_cases: number;
  total_revenue_jpy: number;
  total_expense_jpy: number;
  total_gp_jpy: number;
  average_gp_rate: number;
  decision_counts: Record<string, number>;
  productivity_by_pic: Array<{ pic: string; total_point: number; case_count: number }>;
  gp_by_customer: Array<{
    customer_name: string;
    case_count: number;
    total_revenue_jpy: number;
    total_gp_jpy: number;
    average_gp_rate: number;
  }>;
  partner_summary: Array<{
    partner_name: string;
    case_count: number;
    total_revenue_jpy: number;
    total_gp_jpy: number;
    average_gp_rate: number;
  }>;
};

export type MonthlyPerformanceItem = {
  work_month: string;
  case_count: number;
  total_cases: number;
  total_revenue_jpy: number;
  total_expense_jpy: number;
  total_gp_jpy: number;
  average_gp_rate: number;
  approved_count: number;
  conditional_count: number;
  conditional_approved_count: number;
  ceo_review_count: number;
  rejected_count: number;
};

export type ProductivityMonthlyItem = {
  pic: string;
  work_month: string;
  total_point: number;
  case_count: number;
  grade: string;
};

export type WorkCodeRule = {
  id: number;
  code: string;
  name: string;
  mode: string | null;
  direction: string | null;
  has_customs: boolean;
  has_transport: boolean;
  has_work: boolean;
  point: number;
  description: string | null;
  is_active: boolean;
};

export type RequiredChargeRule = {
  id: number;
  code: string;
  mode: string;
  direction: string;
  charge_name: string;
  keywords: string;
  required_when: string;
  severity: string;
  description: string | null;
  is_active: boolean;
};

export type InternalResourceRule = {
  id: number;
  resource_type: string;
  port: string;
  location_name: string | null;
  vendor_name: string | null;
  priority: number;
  mandatory: boolean;
  description: string | null;
  is_active: boolean;
};

export type ParserTemplate = {
  id: number;
  template_name: string;
  description: string | null;
  mode: string | null;
  direction: string | null;
  file_type: string;
  customer_keyword: string | null;
  partner_keyword: string | null;
  revenue_section_keywords: string;
  expense_section_keywords: string;
  profit_keywords: string;
  duty_keywords: string;
  consumption_tax_keywords: string;
  transport_keywords: string;
  customs_keywords: string;
  partner_fee_keywords: string;
  food_keywords: string;
  is_default: boolean;
  is_active: boolean;
};

export type QuoteRequest = {
  customer_name: string | null;
  trade_type: "PARTNER" | "SHIPPER" | "FORWARDER";
  partner_name: string | null;
  mode: "SEA" | "AIR";
  direction: "EXPORT" | "IMPORT";
  code: string;
  pol: string | null;
  pod: string | null;
  port: string | null;
  origin: string | null;
  destination: string | null;
  container_type: string | null;
  container_count: number;
  cbm: number | null;
  weight_kg: number | null;
  cargo_description: string | null;
  include_customs: boolean;
  include_transport: boolean;
  include_warehouse: boolean;
  target_gp_rate: number | null;
  manual_transport_cost_jpy: number | null;
  manual_customs_cost_jpy: number | null;
  manual_partner_fee_jpy: number | null;
};

export type QuoteCostItem = {
  category: string;
  name: string;
  basis: string;
  estimated_cost_jpy: number;
  recommended_revenue_jpy: number;
  gp_jpy: number;
  source: string;
  note: string | null;
};

export type QuoteResult = {
  customer_name: string | null;
  code: string;
  trade_type: string;
  total_estimated_cost_jpy: number;
  total_recommended_revenue_jpy: number;
  expected_gp_jpy: number;
  expected_gp_rate: number;
  minimum_gp_jpy: number;
  target_gp_rate: number;
  decision_hint: string;
  items: QuoteCostItem[];
  warnings: string[];
  executive_summary: string;
};

export type QuoteListItem = {
  id: number;
  customer_name: string | null;
  trade_type: string;
  partner_name: string | null;
  mode: string;
  direction: string;
  code: string;
  origin: string | null;
  destination: string | null;
  container_type: string | null;
  total_estimated_cost_jpy: number;
  total_recommended_revenue_jpy: number;
  expected_gp_jpy: number;
  expected_gp_rate: number;
  minimum_gp_jpy: number;
  target_gp_rate: number;
  decision_hint: string;
  created_at: string;
};

export type QuoteDetail = QuoteListItem & {
  pol: string | null;
  pod: string | null;
  port: string | null;
  origin: string | null;
  destination: string | null;
  container_type: string | null;
  container_count: number;
  executive_summary: string;
  items: QuoteCostItem[];
};

export type WorkflowListItem = {
  workflow_id: number;
  approval_case_id: number;
  customer_name: string;
  code: string;
  gp_jpy: number;
  decision: string;
  current_status: string;
  requested_by: string | null;
  created_at: string;
  submitted_at: string | null;
};

export type WorkflowInfo = {
  workflow_id: number;
  approval_case_id: number;
  current_status: string;
  requested_by: string | null;
  team_approved_by: string | null;
  director_approved_by: string | null;
  ceo_approved_by: string | null;
  rejected_by: string | null;
  returned_by: string | null;
  request_comment: string | null;
  team_comment: string | null;
  director_comment: string | null;
  ceo_comment: string | null;
  reject_reason: string | null;
  return_reason: string | null;
  submitted_at: string | null;
  team_approved_at: string | null;
  director_approved_at: string | null;
  ceo_approved_at: string | null;
  rejected_at: string | null;
  returned_at: string | null;
  created_at: string;
};

export type WorkflowDetail = {
  workflow: WorkflowInfo;
  approval_case: ApprovalDetail;
  findings: Finding[];
};

export type User = {
  id: number;
  username: string;
  display_name: string;
  email: string | null;
  role: "STAFF" | "TEAM_MANAGER" | "DIRECTOR" | "CEO" | "ADMIN";
  department: string | null;
  is_active: boolean;
};

export type UserPayload = Omit<User, "id"> & {
  password?: string | null;
};

export type ApprovalReportFile = {
  report_file_id: number;
  approval_case_id: number;
  report_type: "SUMMARY" | "DETAIL";
  file_name: string;
  download_url: string;
  created_by: string | null;
  created_at: string | null;
};

export type SystemStatus = {
  database: string;
  database_type: string;
  database_url_masked: string;
  app_env: string;
  upload_folder_exists: boolean;
  generated_reports_folder_exists: boolean;
  logs_folder_exists: boolean;
  backup_folder_exists: boolean;
  approval_case_count: number;
  workflow_count: number;
  quote_count: number;
  report_file_count: number;
};

export type BackupFileItem = {
  file_name: string;
  file_path: string;
  file_size: number;
  created_at: string;
};

export type AuditLogItem = {
  id: number;
  user_name: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  detail: string | null;
  ip_address: string | null;
  created_at: string;
};

export type IntegrationSetting = {
  id: number;
  integration_name: string;
  integration_type: "FILE_EXPORT" | "API" | "WEBHOOK";
  endpoint_url: string | null;
  export_format: "JSON" | "CSV" | "EXCEL";
  is_active: boolean;
  description: string | null;
  created_at: string;
};

export type IntegrationSettingPayload = Omit<IntegrationSetting, "id" | "created_at">;

export type IntegrationLogItem = {
  id: number;
  integration_name: string;
  entity_type: "APPROVAL" | "QUOTE" | "TARIFF" | "WORKFLOW";
  entity_id: number;
  status: "SUCCESS" | "FAIL" | "PENDING";
  request_payload: string | null;
  response_payload: string | null;
  error_message: string | null;
  created_by: string | null;
  created_at: string;
};

export type IntegrationExportResponse = {
  status: "SUCCESS" | "FAIL" | "PENDING";
  file_name: string | null;
  download_url: string | null;
  log_id: number;
};

export type OperationTestResult = {
  id: number;
  test_case_id: string;
  test_name: string;
  tester: string | null;
  result: "PASS" | "FAIL" | "HOLD";
  issue: string | null;
  action_taken: string | null;
  tested_at: string | null;
  created_at: string;
};

export type ParserValidationCase = {
  id: number;
  case_name: string;
  upload_id: string | null;
  original_filename: string | null;
  expected_customer_name: string | null;
  expected_code: string | null;
  expected_gp_jpy: number | null;
  expected_decision: string | null;
  expected_transport_revenue_jpy: number | null;
  expected_transport_expense_jpy: number | null;
  expected_customs_revenue_jpy: number | null;
  expected_customs_duty_jpy: number | null;
  expected_consumption_tax_jpy: number | null;
  expected_partner_fee_jpy: number | null;
  expected_partner_fee_usd: number | null;
  tolerance_jpy: number;
  is_active: boolean;
  created_at: string;
};

export type ParserValidationResult = {
  id: number;
  validation_case_id: number;
  upload_id: string | null;
  parsed_customer_name: string | null;
  parsed_code: string | null;
  parsed_gp_jpy: number | null;
  parsed_decision: string | null;
  parsed_transport_revenue_jpy: number | null;
  parsed_transport_expense_jpy: number | null;
  parsed_customs_revenue_jpy: number | null;
  parsed_customs_duty_jpy: number | null;
  parsed_consumption_tax_jpy: number | null;
  parsed_partner_fee_jpy: number | null;
  parsed_partner_fee_usd: number | null;
  confidence: number | null;
  result: "PASS" | "FAIL" | "PARTIAL";
  diff_summary: string | null;
  created_at: string;
};

export type ParserImprovementSuggestion = {
  id: number;
  validation_result_id: number;
  template_id: number | null;
  case_name: string;
  issue_type: string;
  field_name: string;
  current_value: string | null;
  expected_value: string | null;
  suggested_keyword: string | null;
  suggestion_text: string;
  status: "OPEN" | "APPLIED" | "REJECTED";
  created_at: string;
  applied_at: string | null;
};

export async function getDashboardSummary(params?: {
  start_date?: string;
  end_date?: string;
  work_month?: string;
  pic?: string;
  trade_type?: string;
  code?: string;
  partner_name?: string;
  customer_name?: string;
}) {
  const { data } = await api.get<DashboardSummary>("/api/dashboard/summary", {
    params,
  });
  return data;
}

export async function getMonthlyPerformance(params?: {
  start_month?: string;
  end_month?: string;
  pic?: string;
  trade_type?: string;
  code?: string;
}) {
  const { data } = await api.get<MonthlyPerformanceItem[]>(
    "/api/dashboard/monthly-performance",
    { params },
  );
  return data;
}

export async function getProductivityMonthly(params?: {
  start_month?: string;
  end_month?: string;
  pic?: string;
}) {
  const { data } = await api.get<ProductivityMonthlyItem[]>(
    "/api/dashboard/productivity/monthly",
    { params },
  );
  return data;
}

export async function getDashboardProductivity(params?: {
  work_month?: string;
  start_month?: string;
  end_month?: string;
}) {
  const { data } = await api.get<ProductivityMonthlyItem[]>(
    "/api/dashboard/productivity",
    { params },
  );
  return data;
}

export async function getLowMarginCases(params?: {
  start_date?: string;
  end_date?: string;
  work_month?: string;
  pic?: string;
  trade_type?: string;
  code?: string;
  partner_name?: string;
  customer_name?: string;
}) {
  const { data } = await api.get<
    Array<{
      id: number;
      customer_name: string;
      partner_name: string | null;
      trade_type: string;
      code: string;
      gp_jpy: number;
      gp_rate: number;
      net_gp_rate_ex_tax: number;
      decision: string;
      executive_comment: string;
      created_at: string;
    }>
  >("/api/dashboard/low-margin", { params });
  return data;
}

export async function uploadProfitSheet(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/api/uploads/profit-sheet", formData);
  return data;
}

export async function parseUpload(uploadId: string) {
  const { data } = await api.post(`/api/uploads/${uploadId}/parse`);
  return data;
}

export async function mapUploadToCase(uploadId: string) {
  const { data } = await api.post(`/api/uploads/${uploadId}/map-to-case`);
  return data;
}

export async function analyzeUpload(uploadId: string) {
  const { data } = await api.post<ApprovalResult>(`/api/uploads/${uploadId}/analyze`);
  return data;
}

export async function analyzeAndSaveUpload(uploadId: string) {
  const { data } = await api.post<{ approval_case_id: number; result: ApprovalResult }>(
    `/api/uploads/${uploadId}/analyze-and-save`,
  );
  return data;
}

export async function analyzeCase(caseInput: ApprovalCaseInput) {
  const { data } = await api.post<ApprovalResult>("/api/approvals/analyze", caseInput);
  return data;
}

export async function analyzeAndSaveCase(caseInput: ApprovalCaseInput) {
  const { data } = await api.post<{ approval_case_id: number; result: ApprovalResult }>(
    "/api/approvals/analyze-and-save",
    caseInput,
  );
  return data;
}

export async function getApprovals() {
  const { data } = await api.get<ApprovalListItem[]>("/api/approvals");
  return data;
}

export async function getApprovalDetail(id: number) {
  const { data } = await api.get<ApprovalDetail>(`/api/approvals/${id}`);
  return data;
}

export async function getApprovalReport(id: number) {
  const { data } = await api.get<string>(`/api/approvals/${id}/report`, {
    responseType: "text",
  });
  return data;
}

export async function generateApprovalPdfReport(
  id: number,
  reportType: "SUMMARY" | "DETAIL",
) {
  const { data } = await api.post<ApprovalReportFile>(
    `/api/approvals/${id}/report/pdf`,
    null,
    { params: { report_type: reportType } },
  );
  return data;
}

export async function getApprovalReportFiles(id: number) {
  const { data } = await api.get<ApprovalReportFile[]>(
    `/api/approvals/${id}/report/files`,
  );
  return data;
}

export function getReportDownloadUrl(downloadUrl: string) {
  return `${api.defaults.baseURL}${downloadUrl}`;
}

export function getDocumentationDownloadUrl(documentPath: string) {
  return `${api.defaults.baseURL}${documentPath}`;
}

export async function getPartnerFees() {
  const { data } = await api.get("/api/masters/partner-fees");
  return data;
}

export async function getMinimumGpRules() {
  const { data } = await api.get("/api/masters/minimum-gp");
  return data;
}

export async function getGpRateRules() {
  const { data } = await api.get("/api/masters/gp-rate-rules");
  return data;
}

export async function getWorkCodeRules() {
  const { data } = await api.get<WorkCodeRule[]>("/api/masters/work-code-rules");
  return data;
}

export async function saveWorkCodeRule(payload: Omit<WorkCodeRule, "id">) {
  const { data } = await api.post<WorkCodeRule>("/api/masters/work-code-rules", payload);
  return data;
}

export async function updateWorkCodeRule(id: number, payload: Omit<WorkCodeRule, "id">) {
  const { data } = await api.put<WorkCodeRule>(
    `/api/masters/work-code-rules/${id}`,
    payload,
  );
  return data;
}

export async function deactivateWorkCodeRule(id: number) {
  const { data } = await api.delete<WorkCodeRule>(`/api/masters/work-code-rules/${id}`);
  return data;
}

export async function getInternalResourceRules() {
  const { data } = await api.get<InternalResourceRule[]>(
    "/api/masters/internal-resource-rules",
  );
  return data;
}

export async function saveInternalResourceRule(
  payload: Omit<InternalResourceRule, "id">,
) {
  const { data } = await api.post<InternalResourceRule>(
    "/api/masters/internal-resource-rules",
    payload,
  );
  return data;
}

export async function updateInternalResourceRule(
  id: number,
  payload: Omit<InternalResourceRule, "id">,
) {
  const { data } = await api.put<InternalResourceRule>(
    `/api/masters/internal-resource-rules/${id}`,
    payload,
  );
  return data;
}

export async function deactivateInternalResourceRule(id: number) {
  const { data } = await api.delete<InternalResourceRule>(
    `/api/masters/internal-resource-rules/${id}`,
  );
  return data;
}

export async function getRequiredChargeRules(params?: {
  code?: string;
  mode?: string;
  direction?: string;
  is_active?: boolean;
}) {
  const { data } = await api.get<RequiredChargeRule[]>(
    "/api/masters/required-charge-rules",
    { params },
  );
  return data;
}

export async function saveRequiredChargeRule(
  payload: Omit<RequiredChargeRule, "id">,
) {
  const { data } = await api.post<RequiredChargeRule>(
    "/api/masters/required-charge-rules",
    payload,
  );
  return data;
}

export async function updateRequiredChargeRule(
  id: number,
  payload: Omit<RequiredChargeRule, "id">,
) {
  const { data } = await api.put<RequiredChargeRule>(
    `/api/masters/required-charge-rules/${id}`,
    payload,
  );
  return data;
}

export async function deactivateRequiredChargeRule(id: number) {
  const { data } = await api.delete<RequiredChargeRule>(
    `/api/masters/required-charge-rules/${id}`,
  );
  return data;
}

export async function getParserTemplates(params?: {
  file_type?: string;
  mode?: string;
  direction?: string;
  is_active?: boolean;
}) {
  const { data } = await api.get<ParserTemplate[]>("/api/masters/parser-templates", {
    params,
  });
  return data;
}

export async function saveParserTemplate(payload: Omit<ParserTemplate, "id">) {
  const { data } = await api.post<ParserTemplate>(
    "/api/masters/parser-templates",
    payload,
  );
  return data;
}

export async function updateParserTemplate(
  id: number,
  payload: Omit<ParserTemplate, "id">,
) {
  const { data } = await api.put<ParserTemplate>(
    `/api/masters/parser-templates/${id}`,
    payload,
  );
  return data;
}

export async function deactivateParserTemplate(id: number) {
  const { data } = await api.delete<ParserTemplate>(
    `/api/masters/parser-templates/${id}`,
  );
  return data;
}

export async function generateQuote(payload: QuoteRequest) {
  const { data } = await api.post<QuoteResult>("/api/quotes/generate", payload);
  return data;
}

export async function generateAndSaveQuote(payload: QuoteRequest) {
  const { data } = await api.post<{ quote_case_id: number; result: QuoteResult }>(
    "/api/quotes/generate-and-save",
    payload,
  );
  return data;
}

export async function getQuotes() {
  const { data } = await api.get<QuoteListItem[]>("/api/quotes");
  return data;
}

export async function getQuoteDetail(id: number) {
  const { data } = await api.get<QuoteDetail>(`/api/quotes/${id}`);
  return data;
}

export async function getWorkflows(params?: {
  status?: string;
  pic?: string;
  start_date?: string;
  end_date?: string;
}) {
  const { data } = await api.get<WorkflowListItem[]>("/api/workflows", { params });
  return data;
}

export async function getWorkflowDetail(id: number) {
  const { data } = await api.get<WorkflowDetail>(`/api/workflows/${id}`);
  return data;
}

export async function submitWorkflow(
  id: number,
  payload: { request_comment?: string | null },
) {
  const { data } = await api.post<WorkflowInfo>(`/api/workflows/${id}/submit`, payload);
  return data;
}

export async function teamApproveWorkflow(
  id: number,
  payload: { comment?: string | null },
) {
  const { data } = await api.post<WorkflowInfo>(
    `/api/workflows/${id}/team-approve`,
    payload,
  );
  return data;
}

export async function directorApproveWorkflow(
  id: number,
  payload: { comment?: string | null },
) {
  const { data } = await api.post<WorkflowInfo>(
    `/api/workflows/${id}/director-approve`,
    payload,
  );
  return data;
}

export async function ceoApproveWorkflow(
  id: number,
  payload: { comment?: string | null },
) {
  const { data } = await api.post<WorkflowInfo>(
    `/api/workflows/${id}/ceo-approve`,
    payload,
  );
  return data;
}

export async function rejectWorkflow(
  id: number,
  payload: { reject_reason: string },
) {
  const { data } = await api.post<WorkflowInfo>(`/api/workflows/${id}/reject`, payload);
  return data;
}

export async function returnWorkflow(
  id: number,
  payload: { return_reason: string },
) {
  const { data } = await api.post<WorkflowInfo>(`/api/workflows/${id}/return`, payload);
  return data;
}

export async function seedDefaults() {
  const { data } = await api.post("/api/masters/seed-defaults");
  return data;
}

export async function getUsers() {
  const { data } = await api.get<User[]>("/api/users");
  return data;
}

export async function saveUser(payload: UserPayload) {
  const { data } = await api.post<User>("/api/users", payload);
  return data;
}

export async function updateUser(id: number, payload: UserPayload) {
  const { data } = await api.put<User>(`/api/users/${id}`, payload);
  return data;
}

export async function deactivateUser(id: number) {
  const { data } = await api.delete<User>(`/api/users/${id}`);
  return data;
}

export async function login(username: string, password: string) {
  const { data } = await api.post<LoginResponse>("/api/auth/login", {
    username,
    password,
  });
  storeAuthSession(data.access_token, data.user);
  return data;
}

export async function getMe() {
  const { data } = await api.get<AuthUser>("/api/auth/me");
  localStorage.setItem("lotos_auth_user", JSON.stringify(data));
  localStorage.setItem("lotos_username", data.username);
  return data;
}

export async function changePassword(currentPassword: string, newPassword: string) {
  const { data } = await api.post<{ status: string }>("/api/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
  return data;
}

export async function getSystemStatus() {
  const { data } = await api.get<SystemStatus>("/api/admin/system-status");
  return data;
}

export async function backupDatabase() {
  const { data } = await api.post<{ status: string; backup_file: string | null; message?: string | null }>(
    "/api/admin/backup-db",
  );
  return data;
}

export async function getBackups() {
  const { data } = await api.get<BackupFileItem[]>("/api/admin/backups");
  return data;
}

export async function getAuditLogs(params?: {
  user_name?: string;
  action?: string;
  entity_type?: string;
  start_date?: string;
  end_date?: string;
}) {
  const { data } = await api.get<AuditLogItem[]>("/api/audit-logs", { params });
  return data;
}

export async function getIntegrationSettings(params?: { is_active?: boolean }) {
  const { data } = await api.get<IntegrationSetting[]>("/api/integrations/settings", {
    params,
  });
  return data;
}

export async function saveIntegrationSetting(payload: IntegrationSettingPayload) {
  const { data } = await api.post<IntegrationSetting>(
    "/api/integrations/settings",
    payload,
  );
  return data;
}

export async function updateIntegrationSetting(
  id: number,
  payload: IntegrationSettingPayload,
) {
  const { data } = await api.put<IntegrationSetting>(
    `/api/integrations/settings/${id}`,
    payload,
  );
  return data;
}

export async function deactivateIntegrationSetting(id: number) {
  const { data } = await api.delete<IntegrationSetting>(
    `/api/integrations/settings/${id}`,
  );
  return data;
}

export async function getIntegrationLogs(params?: {
  integration_name?: string;
  entity_type?: string;
  status?: string;
}) {
  const { data } = await api.get<IntegrationLogItem[]>("/api/integrations/logs", {
    params,
  });
  return data;
}

export async function getApprovalIntegrationPayload(id: number) {
  const { data } = await api.get<Record<string, unknown>>(
    `/api/integrations/approval/${id}/payload`,
  );
  return data;
}

export async function getQuoteIntegrationPayload(id: number) {
  const { data } = await api.get<Record<string, unknown>>(
    `/api/integrations/quote/${id}/payload`,
  );
  return data;
}

export async function exportApprovalIntegration(
  id: number,
  payload: { integration_name: string; export_format: "JSON" | "CSV" | "EXCEL" },
) {
  const { data } = await api.post<IntegrationExportResponse>(
    `/api/integrations/export/approval/${id}`,
    payload,
  );
  return data;
}

export async function exportQuoteIntegration(
  id: number,
  payload: { integration_name: string; export_format: "JSON" | "CSV" | "EXCEL" },
) {
  const { data } = await api.post<IntegrationExportResponse>(
    `/api/integrations/export/quote/${id}`,
    payload,
  );
  return data;
}

export async function downloadIntegrationFile(downloadUrl: string) {
  const { data } = await api.get<Blob>(downloadUrl, { responseType: "blob" });
  return data;
}

export async function getOperationTests(params?: {
  result?: string;
  tester?: string;
}) {
  const { data } = await api.get<OperationTestResult[]>("/api/operation-tests", {
    params,
  });
  return data;
}

export async function saveOperationTest(
  payload: Omit<OperationTestResult, "id" | "created_at">,
) {
  const { data } = await api.post<OperationTestResult>("/api/operation-tests", payload);
  return data;
}

export async function updateOperationTest(
  id: number,
  payload: Omit<OperationTestResult, "id" | "created_at">,
) {
  const { data } = await api.put<OperationTestResult>(
    `/api/operation-tests/${id}`,
    payload,
  );
  return data;
}

export async function holdOperationTest(id: number) {
  const { data } = await api.delete<OperationTestResult>(`/api/operation-tests/${id}`);
  return data;
}

export async function getParserValidationCases(params?: { is_active?: boolean }) {
  const { data } = await api.get<ParserValidationCase[]>(
    "/api/parser-validation/cases",
    { params },
  );
  return data;
}

export async function saveParserValidationCase(
  payload: Omit<ParserValidationCase, "id" | "created_at">,
) {
  const { data } = await api.post<ParserValidationCase>(
    "/api/parser-validation/cases",
    payload,
  );
  return data;
}

export async function updateParserValidationCase(
  id: number,
  payload: Omit<ParserValidationCase, "id" | "created_at">,
) {
  const { data } = await api.put<ParserValidationCase>(
    `/api/parser-validation/cases/${id}`,
    payload,
  );
  return data;
}

export async function deactivateParserValidationCase(id: number) {
  const { data } = await api.delete<ParserValidationCase>(
    `/api/parser-validation/cases/${id}`,
  );
  return data;
}

export async function runParserValidation(caseId: number, uploadId: string) {
  const { data } = await api.post<ParserValidationResult>(
    `/api/parser-validation/cases/${caseId}/run`,
    { upload_id: uploadId },
  );
  return data;
}

export async function getParserValidationResults(params?: {
  case_id?: number;
  result?: string;
  start_date?: string;
  end_date?: string;
}) {
  const { data } = await api.get<ParserValidationResult[]>(
    "/api/parser-validation/results",
    { params },
  );
  return data;
}

export async function getParserImprovementSuggestions(params?: {
  status?: string;
  issue_type?: string;
  case_name?: string;
}) {
  const { data } = await api.get<ParserImprovementSuggestion[]>(
    "/api/parser-improvements/suggestions",
    { params },
  );
  return data;
}

export async function applyParserImprovementSuggestion(id: number) {
  const { data } = await api.post<ParserImprovementSuggestion>(
    `/api/parser-improvements/suggestions/${id}/apply`,
  );
  return data;
}

export async function rejectParserImprovementSuggestion(id: number) {
  const { data } = await api.post<ParserImprovementSuggestion>(
    `/api/parser-improvements/suggestions/${id}/reject`,
  );
  return data;
}

type ExportParams = Record<string, string | number | boolean | null | undefined>;

async function downloadExcel(path: string, params?: ExportParams) {
  const { data } = await api.get<Blob>(path, {
    params,
    responseType: "blob",
  });
  return data;
}

export async function downloadApprovalsExcel(params?: ExportParams) {
  return downloadExcel("/api/exports/approvals.xlsx", params);
}

export async function downloadDashboardExcel(params?: ExportParams) {
  return downloadExcel("/api/exports/dashboard.xlsx", params);
}

export async function downloadTransportTariffExcel(params?: ExportParams) {
  return downloadExcel("/api/exports/tariffs/transport.xlsx", params);
}

export async function downloadCustomsTariffExcel(params?: ExportParams) {
  return downloadExcel("/api/exports/tariffs/customs.xlsx", params);
}

export async function downloadQuotesExcel(params?: ExportParams) {
  return downloadExcel("/api/exports/quotes.xlsx", params);
}

export async function downloadProductivityExcel(params?: ExportParams) {
  return downloadExcel("/api/exports/productivity.xlsx", params);
}
