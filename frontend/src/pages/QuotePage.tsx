import { useEffect, useState } from "react";
import {
  downloadQuotesExcel,
  generateAndSaveQuote,
  generateQuote,
  getQuoteDetail,
  getQuotes,
  type QuoteDetail,
  type QuoteListItem,
  type QuoteRequest,
  type QuoteResult,
} from "../api/client";
import { getErrorMessage } from "../error";
import { formatJPY, formatRate } from "../format";
import { saveBlob, todayStamp } from "../download";

const workCodes = [
  "SE",
  "SE+",
  "SE++",
  "SE+++",
  "SI",
  "SI+",
  "SI++",
  "SI+++",
  "AE",
  "AE+",
  "AE++",
  "AE+++",
  "AI",
  "AI+",
  "AI++",
  "AI+++",
];

const initialQuoteRequest: QuoteRequest = {
  customer_name: "TEST CUSTOMER",
  trade_type: "SHIPPER",
  partner_name: null,
  mode: "SEA",
  direction: "IMPORT",
  code: "SI++",
  pol: "BUSAN",
  pod: "TOKYO",
  port: "TOKYO",
  origin: "BUSAN",
  destination: "TOKYO",
  container_type: "20DC",
  container_count: 1,
  cbm: null,
  weight_kg: null,
  cargo_description: null,
  include_customs: true,
  include_transport: true,
  include_warehouse: false,
  target_gp_rate: null,
  manual_transport_cost_jpy: null,
  manual_customs_cost_jpy: null,
  manual_partner_fee_jpy: null,
};

function toNullable(value: string) {
  return value.trim() === "" ? null : value;
}

function numberOrNull(value: string) {
  return value === "" ? null : Number(value);
}

function decisionHintLabel(value: string) {
  if (value === "QUOTABLE") return "견적 가능";
  if (value === "NEED_REVIEW") return "검토 필요";
  return value;
}

export function QuotePage() {
  const [form, setForm] = useState<QuoteRequest>({ ...initialQuoteRequest });
  const [result, setResult] = useState<QuoteResult | null>(null);
  const [quotes, setQuotes] = useState<QuoteListItem[]>([]);
  const [selectedQuote, setSelectedQuote] = useState<QuoteDetail | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadQuotes() {
    try {
      setError("");
      setQuotes(await getQuotes());
    } catch (error) {
      setError(getErrorMessage(error, "견적 이력 조회 실패"));
    }
  }

  useEffect(() => {
    loadQuotes();
  }, []);

  function update<K extends keyof QuoteRequest>(field: K, value: QuoteRequest[K]) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function runGenerate() {
    try {
      setError("");
      const quote = await generateQuote(form);
      setResult(quote);
      setMessage("견적 생성 완료");
    } catch (error) {
      const message = getErrorMessage(error, "견적 생성 실패");
      setError(message);
      alert(message);
    }
  }

  async function runGenerateAndSave() {
    try {
      setError("");
      const saved = await generateAndSaveQuote(form);
      setResult(saved.result);
      setMessage(`견적 저장 완료: quote_case_id ${saved.quote_case_id}`);
      await loadQuotes();
      setSelectedQuote(await getQuoteDetail(saved.quote_case_id));
    } catch (error) {
      const message = getErrorMessage(error, "견적 저장 실패");
      setError(message);
      alert(message);
    }
  }

  async function selectQuote(id: number) {
    try {
      setError("");
      setSelectedQuote(await getQuoteDetail(id));
    } catch (error) {
      const message = getErrorMessage(error, "견적 상세 조회 실패");
      setError(message);
      alert(message);
    }
  }

  async function downloadQuotes() {
    try {
      setError("");
      const blob = await downloadQuotesExcel();
      saveBlob(blob, `quotes_${todayStamp()}.xlsx`);
    } catch (error) {
      const message = getErrorMessage(error, "견적이력 Excel 다운로드 실패");
      setError(message);
      alert(message);
    }
  }

  function resetForm() {
    setForm({ ...initialQuoteRequest });
    setResult(null);
    setSelectedQuote(null);
    setMessage("입력값을 초기화했습니다.");
  }

  return (
    <div className="stack">
      {error && <div className="error-box">{error}</div>}

      <section className="panel">
        <div className="section-heading">
          <h2>Quote Generator</h2>
          <div className="toolbar">
            <button type="button" onClick={runGenerate}>
              견적 생성
            </button>
            <button type="button" onClick={runGenerateAndSave}>
              견적 생성 및 저장
            </button>
            <button type="button" className="secondary-button" onClick={resetForm}>
              입력 초기화
            </button>
            <button type="button" className="secondary-button" onClick={downloadQuotes}>
              Quotes Excel
            </button>
          </div>
        </div>
        <div className="meta-line">{message}</div>
      </section>

      <section className="panel">
        <h2>기본정보</h2>
        <div className="form-grid">
          <TextField
            label="Customer"
            value={form.customer_name}
            onChange={(value) => update("customer_name", toNullable(value))}
          />
          <SelectField
            label="Trade Type"
            value={form.trade_type}
            options={["PARTNER", "SHIPPER", "FORWARDER"]}
            onChange={(value) => update("trade_type", value as QuoteRequest["trade_type"])}
          />
          <TextField
            label="Partner"
            value={form.partner_name}
            onChange={(value) => update("partner_name", toNullable(value))}
          />
        </div>
      </section>

      <section className="panel">
        <h2>업무정보</h2>
        <div className="form-grid">
          <SelectField
            label="Mode"
            value={form.mode}
            options={["SEA", "AIR"]}
            onChange={(value) => update("mode", value as QuoteRequest["mode"])}
          />
          <SelectField
            label="Direction"
            value={form.direction}
            options={["EXPORT", "IMPORT"]}
            onChange={(value) =>
              update("direction", value as QuoteRequest["direction"])
            }
          />
          <SelectField
            label="Code"
            value={form.code}
            options={workCodes}
            onChange={(value) => update("code", value)}
          />
        </div>
      </section>

      <section className="panel">
        <h2>구간정보</h2>
        <div className="form-grid">
          <TextField label="POL" value={form.pol} onChange={(value) => update("pol", toNullable(value))} />
          <TextField label="POD" value={form.pod} onChange={(value) => update("pod", toNullable(value))} />
          <TextField label="PORT" value={form.port} onChange={(value) => update("port", toNullable(value))} />
          <TextField label="Origin" value={form.origin} onChange={(value) => update("origin", toNullable(value))} />
          <TextField label="Destination" value={form.destination} onChange={(value) => update("destination", toNullable(value))} />
        </div>
      </section>

      <section className="panel">
        <h2>화물정보</h2>
        <div className="form-grid">
          <TextField
            label="Container Type"
            value={form.container_type}
            onChange={(value) => update("container_type", toNullable(value))}
          />
          <NumberField
            label="Container Count"
            value={form.container_count}
            onChange={(value) => update("container_count", value ?? 1)}
          />
          <NumberField label="CBM" value={form.cbm} onChange={(value) => update("cbm", value)} />
          <NumberField
            label="Weight KG"
            value={form.weight_kg}
            onChange={(value) => update("weight_kg", value)}
          />
          <TextField
            label="Cargo"
            value={form.cargo_description}
            onChange={(value) => update("cargo_description", toNullable(value))}
          />
        </div>
      </section>

      <section className="panel">
        <h2>포함업무 / 수동원가</h2>
        <div className="form-grid">
          <CheckboxField
            label="Customs"
            checked={form.include_customs}
            onChange={(checked) => update("include_customs", checked)}
          />
          <CheckboxField
            label="Transport"
            checked={form.include_transport}
            onChange={(checked) => update("include_transport", checked)}
          />
          <CheckboxField
            label="Warehouse"
            checked={form.include_warehouse}
            onChange={(checked) => update("include_warehouse", checked)}
          />
          <NumberField
            label="Manual Transport Cost"
            value={form.manual_transport_cost_jpy}
            onChange={(value) => update("manual_transport_cost_jpy", value)}
          />
          <NumberField
            label="Manual Customs Cost"
            value={form.manual_customs_cost_jpy}
            onChange={(value) => update("manual_customs_cost_jpy", value)}
          />
          <NumberField
            label="Manual Partner Fee"
            value={form.manual_partner_fee_jpy}
            onChange={(value) => update("manual_partner_fee_jpy", value)}
          />
          <NumberField
            label="Target GP Rate"
            value={form.target_gp_rate}
            step="0.01"
            onChange={(value) => update("target_gp_rate", value)}
          />
        </div>
      </section>

      {result && <QuoteResultView result={result} />}

      <section className="panel">
        <div className="section-heading">
          <h2>견적 이력</h2>
          <button type="button" className="secondary-button" onClick={loadQuotes}>
            Refresh
          </button>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Customer</th>
                <th>Trade</th>
                <th>Partner</th>
                <th>Mode</th>
                <th>Direction</th>
                <th>Code</th>
                <th>Origin</th>
                <th>Destination</th>
                <th>Container</th>
                <th className="number">Cost</th>
                <th className="number">Revenue</th>
                <th className="number">GP</th>
                <th className="number">GP Rate</th>
                <th>Decision</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {quotes.map((quote) => (
                <tr key={quote.id} onClick={() => selectQuote(quote.id)}>
                  <td>{quote.id}</td>
                  <td>{quote.customer_name ?? "-"}</td>
                  <td>{quote.trade_type}</td>
                  <td>{quote.partner_name ?? "-"}</td>
                  <td>{quote.mode}</td>
                  <td>{quote.direction}</td>
                  <td>{quote.code}</td>
                  <td>{quote.origin ?? "-"}</td>
                  <td>{quote.destination ?? "-"}</td>
                  <td>{quote.container_type ?? "-"}</td>
                  <td className="number">{formatJPY(quote.total_estimated_cost_jpy)}</td>
                  <td className="number">{formatJPY(quote.total_recommended_revenue_jpy)}</td>
                  <td className="number">{formatJPY(quote.expected_gp_jpy)}</td>
                  <td className="number">{formatRate(quote.expected_gp_rate)}</td>
                  <td>
                    <QuoteDecisionBadge value={quote.decision_hint} />
                  </td>
                  <td>{quote.created_at.slice(0, 10)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {selectedQuote && (
        <section className="panel">
          <h2>견적 상세 #{selectedQuote.id}</h2>
          <p className="comment">{selectedQuote.executive_summary}</p>
          <QuoteItemsTable items={selectedQuote.items} />
        </section>
      )}
    </div>
  );
}

function QuoteResultView({ result }: { result: QuoteResult }) {
  return (
    <>
      <section className="panel">
        <h2>견적 결과</h2>
        <div className="result-grid">
          <div>고객명: {result.customer_name ?? "-"}</div>
          <div>업무코드: {result.code}</div>
          <div>거래구분: {result.trade_type}</div>
          <div>총 예상원가: {formatJPY(result.total_estimated_cost_jpy)}</div>
          <div>권장 청구액: {formatJPY(result.total_recommended_revenue_jpy)}</div>
          <div>예상 GP: {formatJPY(result.expected_gp_jpy)}</div>
          <div>예상 GP율: {formatRate(result.expected_gp_rate)}</div>
          <div>Minimum GP: {formatJPY(result.minimum_gp_jpy)}</div>
          <div>목표 GP율: {formatRate(result.target_gp_rate)}</div>
          <div>
            Decision: <QuoteDecisionBadge value={result.decision_hint} />
          </div>
        </div>
      </section>

      {result.warnings.length > 0 && (
        <section className="panel warning-panel">
          <h2>Warnings</h2>
          <ul className="warning-list">
            {result.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="panel">
        <h2>Executive Summary</h2>
        <p className="comment">{result.executive_summary}</p>
      </section>

      <section className="panel">
        <h2>Quote Items</h2>
        <QuoteItemsTable items={result.items} />
      </section>
    </>
  );
}

function QuoteItemsTable({ items }: { items: QuoteResult["items"] }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Category</th>
            <th>Name</th>
            <th>Basis</th>
            <th className="number">Cost</th>
            <th className="number">Revenue</th>
            <th className="number">GP</th>
            <th>Source</th>
            <th>Note</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => (
            <tr key={`${item.category}-${index}`}>
              <td>{item.category}</td>
              <td>{item.name}</td>
              <td>{item.basis}</td>
              <td className="number">{formatJPY(item.estimated_cost_jpy)}</td>
              <td className="number">{formatJPY(item.recommended_revenue_jpy)}</td>
              <td className="number">{formatJPY(item.gp_jpy)}</td>
              <td>{item.source}</td>
              <td>{item.note ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function QuoteDecisionBadge({ value }: { value: string }) {
  const className =
    value === "QUOTABLE" ? "decision-badge approved" : "decision-badge ceo_review";
  return <span className={className}>{decisionHintLabel(value)}</span>;
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
  step,
  onChange,
}: {
  label: string;
  value: number | null | undefined;
  step?: string;
  onChange: (value: number | null) => void;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        type="number"
        step={step}
        value={value ?? ""}
        onChange={(event) => onChange(numberOrNull(event.target.value))}
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
