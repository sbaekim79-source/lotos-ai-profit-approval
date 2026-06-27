import { useState } from "react";
import {
  analyzeAndSaveCase,
  analyzeCase,
  getApprovalReport,
  mapUploadToCase,
  parseUpload,
  uploadProfitSheet,
  type ApprovalCaseInput,
  type ApprovalResult,
  type ChargeItem,
  type PartnerFeeInput,
} from "../api/client";
import { DecisionBadge } from "../components/DecisionBadge";
import { FindingsTable } from "../components/FindingsTable";
import { formatJPY, formatRate } from "../format";
import { getErrorMessage } from "../error";

type CaseField = keyof ApprovalCaseInput;
type PartnerFeeField = keyof PartnerFeeInput;

const emptyPartnerFee: PartnerFeeInput = {
  partner_name: null,
  actual_fee_jpy: 0,
  actual_fee_usd: 0,
  bl_count: 1,
  container_type: null,
  container_count: 1,
  special_condition: null,
};

function toNullable(value: string) {
  return value.trim() === "" ? null : value;
}

function numberValue(value: string) {
  return value === "" ? 0 : Number(value);
}

function normalizeCandidate(candidate: ApprovalCaseInput): ApprovalCaseInput {
  return {
    ...candidate,
    customs_vendor_name: candidate.customs_vendor_name ?? null,
    warehouse_vendor_name: candidate.warehouse_vendor_name ?? null,
    transport_vendor_name: candidate.transport_vendor_name ?? null,
    external_customs_reason: candidate.external_customs_reason ?? null,
    external_warehouse_reason: candidate.external_warehouse_reason ?? null,
    external_transport_reason: candidate.external_transport_reason ?? null,
    partner_fee: candidate.partner_fee ?? { ...emptyPartnerFee },
    revenue_items:
      candidate.revenue_items?.length > 0
        ? candidate.revenue_items
        : [{ name: "TOTAL", amount_jpy: 0 }],
    expense_items:
      candidate.expense_items?.length > 0
        ? candidate.expense_items
        : [{ name: "TOTAL", amount_jpy: 0 }],
  };
}

export function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadId, setUploadId] = useState("");
  const [message, setMessage] = useState("");
  const [parseResult, setParseResult] = useState<any>(null);
  const [confidence, setConfidence] = useState<number | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [templateUsed, setTemplateUsed] = useState<any>(null);
  const [caseInput, setCaseInput] = useState<ApprovalCaseInput | null>(null);
  const [result, setResult] = useState<ApprovalResult | null>(null);
  const [savedApprovalCaseId, setSavedApprovalCaseId] = useState<number | null>(null);
  const [report, setReport] = useState("");
  const [error, setError] = useState("");

  async function runUpload() {
    if (!file) return;
    try {
      setError("");
      const uploaded = await uploadProfitSheet(file);
      setUploadId(uploaded.upload_id);
      setParseResult(null);
      setCaseInput(null);
      setResult(null);
      setSavedApprovalCaseId(null);
      setReport("");
      setConfidence(null);
      setWarnings([]);
      setTemplateUsed(null);
      setMessage(`Uploaded: ${uploaded.original_filename}`);
    } catch (error) {
      const message = getErrorMessage(error, "파일 업로드 실패");
      setError(message);
      alert(message);
    }
  }

  async function runParse() {
    try {
      setError("");
      const parsed = await parseUpload(uploadId);
      setParseResult(parsed.parse_result);
      setMessage("Parsed preview loaded");
    } catch (error) {
      const message = getErrorMessage(error, "파싱 실패");
      setError(message);
      alert(message);
    }
  }

  async function runMap() {
    try {
      setError("");
      const mapped = await mapUploadToCase(uploadId);
      setCaseInput(normalizeCandidate(mapped.candidate));
      setConfidence(mapped.parsing_confidence ?? mapped.confidence ?? null);
      setWarnings(mapped.warnings ?? []);
      setTemplateUsed(mapped.template_used ?? null);
      setResult(null);
      setSavedApprovalCaseId(null);
      setReport("");
      setMessage("Mapped to editable case");
    } catch (error) {
      const message = getErrorMessage(error, "자동 매핑 실패");
      setError(message);
      alert(message);
    }
  }

  async function runAnalyzeEdited() {
    if (!caseInput) return;
    try {
      setError("");
      const analyzed = await analyzeCase(caseInput);
      setResult(analyzed);
      setReport("");
      setMessage("Edited case analyzed");
    } catch (error) {
      const message = getErrorMessage(error, "결재심사 실패");
      setError(message);
      alert(message);
    }
  }

  async function runAnalyzeAndSaveEdited() {
    if (!caseInput) return;
    try {
      setError("");
      const saved = await analyzeAndSaveCase(caseInput);
      setResult(saved.result);
      setSavedApprovalCaseId(saved.approval_case_id);
      setReport("");
      setMessage(`Saved approval_case_id: ${saved.approval_case_id}`);
    } catch (error) {
      const message = getErrorMessage(error, "저장 실패");
      setError(message);
      alert(message);
    }
  }

  async function showSavedReport() {
    if (!savedApprovalCaseId) return;
    try {
      setError("");
      const reportText = await getApprovalReport(savedApprovalCaseId);
      setReport(reportText);
    } catch (error) {
      const message = getErrorMessage(error, "결재심사서 조회 실패");
      setError(message);
      alert(message);
    }
  }

  async function downloadSavedReport() {
    if (!savedApprovalCaseId) return;
    try {
      setError("");
      const reportText = report || (await getApprovalReport(savedApprovalCaseId));
      const blob = new Blob([reportText], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `approval_report_${savedApprovalCaseId}.md`;
      anchor.click();
      URL.revokeObjectURL(url);
      setReport(reportText);
    } catch (error) {
      const message = getErrorMessage(error, "Markdown 다운로드 실패");
      setError(message);
      alert(message);
    }
  }

  function updateCase(field: CaseField, value: ApprovalCaseInput[CaseField]) {
    setCaseInput((current) => (current ? { ...current, [field]: value } : current));
  }

  function updatePartnerFee(field: PartnerFeeField, value: PartnerFeeInput[PartnerFeeField]) {
    setCaseInput((current) => {
      if (!current) return current;
      return {
        ...current,
        partner_fee: {
          ...(current.partner_fee ?? emptyPartnerFee),
          [field]: value,
        },
      };
    });
  }

  function updateItem(
    listName: "revenue_items" | "expense_items",
    index: number,
    field: keyof ChargeItem,
    value: string | number,
  ) {
    setCaseInput((current) => {
      if (!current) return current;
      const items = current[listName].map((item, itemIndex) =>
        itemIndex === index ? { ...item, [field]: value } : item,
      );
      return { ...current, [listName]: items };
    });
  }

  function addItem(listName: "revenue_items" | "expense_items") {
    setCaseInput((current) => {
      if (!current) return current;
      return {
        ...current,
        [listName]: [...current[listName], { name: "", amount_jpy: 0 }],
      };
    });
  }

  function removeItem(listName: "revenue_items" | "expense_items", index: number) {
    setCaseInput((current) => {
      if (!current) return current;
      const nextItems = current[listName].filter((_, itemIndex) => itemIndex !== index);
      return {
        ...current,
        [listName]: nextItems.length > 0 ? nextItems : [{ name: "TOTAL", amount_jpy: 0 }],
      };
    });
  }

  const partnerFee = caseInput?.partner_fee ?? emptyPartnerFee;

  return (
    <div className="stack">
      {error && <div className="error-box">{error}</div>}
      <section className="panel">
        <h2>Profit Sheet Upload</h2>
        <div className="toolbar">
          <input
            type="file"
            accept=".pdf,.xlsx,.xls"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
          <button type="button" onClick={runUpload} disabled={!file}>
            Upload
          </button>
          <button type="button" onClick={runParse} disabled={!uploadId}>
            Parse Preview
          </button>
          <button type="button" onClick={runMap} disabled={!uploadId}>
            Map to Case
          </button>
          <button type="button" onClick={runAnalyzeEdited} disabled={!caseInput}>
            Analyze Edited Case
          </button>
          <button type="button" onClick={runAnalyzeAndSaveEdited} disabled={!caseInput}>
            Analyze & Save Edited Case
          </button>
        </div>
        <div className="meta-line">upload_id: {uploadId || "-"}</div>
        <div className="meta-line">{message}</div>
      </section>

      {caseInput && (
        <>
          <section className="panel">
            <h2>Parsing Confidence</h2>
            <div className="detail-grid">
              <div>
                Template: {templateUsed?.template_name ?? "-"}
              </div>
              <div>Confidence: {confidence ?? "-"}</div>
              <div>File Type: {templateUsed?.file_type ?? "-"}</div>
              <div>Direction: {templateUsed?.direction ?? "-"}</div>
              <div>Warnings: {warnings.length}</div>
            </div>
            {warnings.length > 0 && (
              <ul className="warning-list">
                {warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            )}
          </section>

          <section className="panel">
            <h2>기본정보</h2>
            <div className="form-grid">
              <TextField
                label="Customer"
                value={caseInput.customer_name}
                onChange={(value) => updateCase("customer_name", value)}
              />
              <SelectField
                label="Trade Type"
                value={caseInput.trade_type}
                options={["PARTNER", "SHIPPER", "FORWARDER"]}
                onChange={(value) => updateCase("trade_type", value as ApprovalCaseInput["trade_type"])}
              />
              <TextField
                label="Partner"
                value={caseInput.partner_name}
                onChange={(value) => updateCase("partner_name", toNullable(value))}
              />
              <TextField
                label="Shipper"
                value={caseInput.shipper_name}
                onChange={(value) => updateCase("shipper_name", toNullable(value))}
              />
              <TextField
                label="PIC"
                value={caseInput.pic}
                onChange={(value) => updateCase("pic", toNullable(value))}
              />
            </div>
          </section>

          <section className="panel">
            <h2>업무구분</h2>
            <div className="form-grid compact">
              <SelectField
                label="Mode"
                value={caseInput.mode}
                options={["SEA", "AIR"]}
                onChange={(value) => updateCase("mode", value as ApprovalCaseInput["mode"])}
              />
              <SelectField
                label="Direction"
                value={caseInput.direction}
                options={["EXPORT", "IMPORT"]}
                onChange={(value) => updateCase("direction", value as ApprovalCaseInput["direction"])}
              />
              <CheckboxField
                label="Customs"
                checked={caseInput.has_customs}
                onChange={(checked) => updateCase("has_customs", checked)}
              />
              <CheckboxField
                label="Transport"
                checked={caseInput.has_transport}
                onChange={(checked) => updateCase("has_transport", checked)}
              />
              <CheckboxField
                label="Work"
                checked={caseInput.has_work}
                onChange={(checked) => updateCase("has_work", checked)}
              />
              <CheckboxField
                label="Project"
                checked={caseInput.is_project}
                onChange={(checked) => updateCase("is_project", checked)}
              />
            </div>
          </section>

          <section className="panel">
            <h2>운송정보</h2>
            <div className="form-grid">
              <TextField label="POL" value={caseInput.pol} onChange={(value) => updateCase("pol", toNullable(value))} />
              <TextField label="POD" value={caseInput.pod} onChange={(value) => updateCase("pod", toNullable(value))} />
              <TextField label="Port" value={caseInput.port} onChange={(value) => updateCase("port", toNullable(value))} />
              <TextField
                label="Container Type"
                value={caseInput.container_type}
                onChange={(value) => updateCase("container_type", toNullable(value))}
              />
              <NumberField
                label="Container Count"
                value={caseInput.container_count}
                onChange={(value) => updateCase("container_count", value)}
              />
              <TextField
                label="Cargo"
                value={caseInput.cargo_description}
                onChange={(value) => updateCase("cargo_description", toNullable(value))}
              />
            </div>
          </section>

          <section className="panel">
            <h2>금액정보</h2>
            <div className="form-grid">
              <NumberField
                label="Customs Duty"
                value={caseInput.customs_duty_jpy}
                onChange={(value) => updateCase("customs_duty_jpy", value)}
              />
              <NumberField
                label="Consumption Tax"
                value={caseInput.consumption_tax_jpy}
                onChange={(value) => updateCase("consumption_tax_jpy", value)}
              />
              <NumberField
                label="Transport Revenue"
                value={caseInput.transport_revenue_jpy}
                onChange={(value) => updateCase("transport_revenue_jpy", value)}
              />
              <NumberField
                label="Transport Expense"
                value={caseInput.transport_expense_jpy}
                onChange={(value) => updateCase("transport_expense_jpy", value)}
              />
              <NumberField
                label="Customs Revenue"
                value={caseInput.customs_revenue_jpy}
                onChange={(value) => updateCase("customs_revenue_jpy", value)}
              />
              <NumberField
                label="Customs Expense"
                value={caseInput.customs_expense_jpy}
                onChange={(value) => updateCase("customs_expense_jpy", value)}
              />
              <CheckboxField
                label="Self Customs"
                checked={caseInput.self_customs}
                onChange={(checked) => updateCase("self_customs", checked)}
              />
            </div>
          </section>

          <section className="panel">
            <h2>Internal Resource</h2>
            <div className="info-box">
              자사자원 우선 대상 PORT에서 외주를 사용하는 경우 사유를 입력해야 합니다.
            </div>
            <div className="form-grid">
              <TextField
                label="Customs Vendor"
                value={caseInput.customs_vendor_name}
                onChange={(value) => updateCase("customs_vendor_name", toNullable(value))}
              />
              <TextField
                label="Warehouse Vendor"
                value={caseInput.warehouse_vendor_name}
                onChange={(value) => updateCase("warehouse_vendor_name", toNullable(value))}
              />
              <TextField
                label="Transport Vendor"
                value={caseInput.transport_vendor_name}
                onChange={(value) => updateCase("transport_vendor_name", toNullable(value))}
              />
              <TextField
                label="External Customs Reason"
                value={caseInput.external_customs_reason}
                onChange={(value) => updateCase("external_customs_reason", toNullable(value))}
              />
              <TextField
                label="External Warehouse Reason"
                value={caseInput.external_warehouse_reason}
                onChange={(value) => updateCase("external_warehouse_reason", toNullable(value))}
              />
              <TextField
                label="External Transport Reason"
                value={caseInput.external_transport_reason}
                onChange={(value) => updateCase("external_transport_reason", toNullable(value))}
              />
            </div>
          </section>

          <ChargeItemsEditor
            title="Revenue Items"
            items={caseInput.revenue_items}
            onAdd={() => addItem("revenue_items")}
            onRemove={(index) => removeItem("revenue_items", index)}
            onChange={(index, field, value) => updateItem("revenue_items", index, field, value)}
          />

          <ChargeItemsEditor
            title="Expense Items"
            items={caseInput.expense_items}
            onAdd={() => addItem("expense_items")}
            onRemove={(index) => removeItem("expense_items", index)}
            onChange={(index, field, value) => updateItem("expense_items", index, field, value)}
          />

          <section className="panel">
            <h2>Partner Fee</h2>
            <div className="form-grid">
              <TextField
                label="Partner"
                value={partnerFee.partner_name}
                onChange={(value) => updatePartnerFee("partner_name", toNullable(value))}
              />
              <NumberField
                label="Actual Fee JPY"
                value={partnerFee.actual_fee_jpy}
                onChange={(value) => updatePartnerFee("actual_fee_jpy", value)}
              />
              <NumberField
                label="Actual Fee USD"
                value={partnerFee.actual_fee_usd}
                onChange={(value) => updatePartnerFee("actual_fee_usd", value)}
              />
              <NumberField
                label="B/L Count"
                value={partnerFee.bl_count}
                onChange={(value) => updatePartnerFee("bl_count", value)}
              />
              <TextField
                label="Container Type"
                value={partnerFee.container_type}
                onChange={(value) => updatePartnerFee("container_type", toNullable(value))}
              />
              <NumberField
                label="Container Count"
                value={partnerFee.container_count}
                onChange={(value) => updatePartnerFee("container_count", value)}
              />
              <TextField
                label="Special Condition"
                value={partnerFee.special_condition}
                onChange={(value) => updatePartnerFee("special_condition", toNullable(value))}
              />
            </div>
          </section>
        </>
      )}

      {parseResult && (
        <section className="panel">
          <h2>Parsed Preview</h2>
          <div className="detail-grid">
            <div>OCR Status: {parseResult.ocr_status ?? "-"}</div>
            <div>Pages: {parseResult.page_count ?? "-"}</div>
            <div>Text Pages: {parseResult.text_page_count ?? "-"}</div>
            <div>Image-only Pages: {parseResult.image_only_page_count ?? "-"}</div>
          </div>
          {Array.isArray(parseResult.warnings) && parseResult.warnings.length > 0 && (
            <ul className="warning-list">
              {parseResult.warnings.map((warning: string) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          )}
          <div className="meta-line">tables: {parseResult.raw_tables?.length ?? 0}</div>
          <pre className="raw-preview">{String(parseResult.raw_text ?? "").slice(0, 1000)}</pre>
        </section>
      )}

      {result && (
        <section className="panel">
          <div className="section-heading">
            <h2>분석결과</h2>
            {savedApprovalCaseId && (
              <div className="toolbar">
                <button type="button" onClick={showSavedReport}>
                  결재심사서 보기
                </button>
                <button type="button" onClick={downloadSavedReport}>
                  Markdown 다운로드
                </button>
              </div>
            )}
          </div>
          <div className="result-grid">
            <div>고객명: {result.customer_name}</div>
            <div>업무코드: {result.code}</div>
            <div>Point: {result.point}</div>
            <div>매출: {formatJPY(result.total_revenue_jpy)}</div>
            <div>원가: {formatJPY(result.total_expense_jpy)}</div>
            <div>GP: {formatJPY(result.gp_jpy)}</div>
            <div>GP율: {formatRate(result.gp_rate)}</div>
            <div>실GP율: {formatRate(result.net_gp_rate_ex_tax)}</div>
            <div>Minimum GP: {formatJPY(result.minimum_gp_jpy)}</div>
            <div>
              Decision: <DecisionBadge decision={result.decision} />
            </div>
          </div>
          <p className="comment">{result.executive_comment}</p>
          <FindingsTable findings={result.findings} />
        </section>
      )}

      {report && (
        <section className="panel">
          <h2>대표이사 결재심사서</h2>
          <pre className="report-preview">{report}</pre>
        </section>
      )}
    </div>
  );
}

function TextField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string | null | undefined;
  onChange: (value: string) => void;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input type="text" value={value ?? ""} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number | null | undefined;
  onChange: (value: number) => void;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        type="number"
        value={value ?? 0}
        onChange={(event) => onChange(numberValue(event.target.value))}
      />
    </label>
  );
}

function SelectField({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function CheckboxField({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="check-field">
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <span>{label}</span>
    </label>
  );
}

function ChargeItemsEditor({
  title,
  items,
  onAdd,
  onRemove,
  onChange,
}: {
  title: string;
  items: ChargeItem[];
  onAdd: () => void;
  onRemove: (index: number) => void;
  onChange: (index: number, field: keyof ChargeItem, value: string | number) => void;
}) {
  return (
    <section className="panel">
      <div className="section-heading">
        <h2>{title}</h2>
        <button type="button" onClick={onAdd}>
          Add Row
        </button>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th className="number">Amount JPY</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={`${title}-${index}`}>
                <td>
                  <input
                    className="table-input"
                    type="text"
                    value={item.name}
                    onChange={(event) => onChange(index, "name", event.target.value)}
                  />
                </td>
                <td>
                  <input
                    className="table-input number-input"
                    type="number"
                    value={item.amount_jpy}
                    onChange={(event) => onChange(index, "amount_jpy", numberValue(event.target.value))}
                  />
                </td>
                <td>
                  <button type="button" className="secondary-button" onClick={() => onRemove(index)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
