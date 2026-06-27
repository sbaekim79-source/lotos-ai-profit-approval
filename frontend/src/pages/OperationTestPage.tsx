import { useEffect, useState } from "react";
import {
  applyParserImprovementSuggestion,
  deactivateParserValidationCase,
  getOperationTests,
  getParserImprovementSuggestions,
  getParserValidationCases,
  getParserValidationResults,
  holdOperationTest,
  rejectParserImprovementSuggestion,
  runParserValidation,
  saveOperationTest,
  saveParserValidationCase,
  updateOperationTest,
  updateParserValidationCase,
  type OperationTestResult,
  type ParserImprovementSuggestion,
  type ParserValidationCase,
  type ParserValidationResult,
} from "../api/client";
import { formatJPY } from "../format";
import { getErrorMessage } from "../error";

const scenarios = [
  ["TC-001", "Health Check"],
  ["TC-002", "Master Seed"],
  ["TC-003", "Profit Sheet Upload"],
  ["TC-004", "Parse"],
  ["TC-005", "Map to Case"],
  ["TC-006", "Manual Edit"],
  ["TC-007", "Analyze"],
  ["TC-008", "Analyze and Save"],
  ["TC-009", "Workflow Submit"],
  ["TC-010", "Team Approve"],
  ["TC-011", "Director Approve"],
  ["TC-012", "CEO Approve"],
  ["TC-013", "PDF Summary 생성"],
  ["TC-014", "PDF Detail 생성"],
  ["TC-015", "Dashboard 반영"],
  ["TC-016", "기간별 Dashboard 조회"],
  ["TC-017", "Tariff DB 확인"],
  ["TC-018", "Quote Generate"],
  ["TC-019", "권한 오류"],
  ["TC-020", "Backup"],
];

type FormState = Omit<OperationTestResult, "id" | "created_at">;

function defaultForm(): FormState {
  return {
    test_case_id: "TC-001",
    test_name: "Health Check",
    tester: "",
    result: "PASS",
    issue: "",
    action_taken: "",
    tested_at: new Date().toISOString().slice(0, 16),
  };
}

function badgeClass(result: string) {
  if (result === "PASS") return "badge badge-green";
  if (result === "FAIL") return "badge badge-red";
  return "badge badge-orange";
}

export function OperationTestPage() {
  const [items, setItems] = useState<OperationTestResult[]>([]);
  const [form, setForm] = useState<FormState>(defaultForm());
  const [editingId, setEditingId] = useState<number | null>(null);
  const [filterResult, setFilterResult] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [validationCases, setValidationCases] = useState<ParserValidationCase[]>([]);
  const [validationResults, setValidationResults] = useState<ParserValidationResult[]>([]);
  const [improvementSuggestions, setImprovementSuggestions] = useState<ParserImprovementSuggestion[]>([]);
  const [validationUploadId, setValidationUploadId] = useState("");
  const [editingValidationCaseId, setEditingValidationCaseId] = useState<number | null>(null);
  const [validationForm, setValidationForm] = useState<Omit<ParserValidationCase, "id" | "created_at">>({
    case_name: "TOWA_SI_PLUS_PLUS",
    upload_id: null,
    original_filename: null,
    expected_customer_name: "TOWA",
    expected_code: "SI++",
    expected_gp_jpy: 24493,
    expected_decision: "CEO_REVIEW|CONDITIONAL_APPROVED",
    expected_transport_revenue_jpy: 61000,
    expected_transport_expense_jpy: 60000,
    expected_customs_revenue_jpy: 11800,
    expected_customs_duty_jpy: null,
    expected_consumption_tax_jpy: 300300,
    expected_partner_fee_jpy: null,
    expected_partner_fee_usd: null,
    tolerance_jpy: 500,
    is_active: true,
  });

  async function load() {
    try {
      setLoading(true);
      setError("");
      setItems(await getOperationTests({ result: filterResult || undefined }));
    } catch (error) {
      setError(getErrorMessage(error, "Operation test load failed"));
    } finally {
      setLoading(false);
    }
  }

  async function loadParserValidation() {
    try {
      setLoading(true);
      setError("");
      const [cases, results, suggestions] = await Promise.all([
        getParserValidationCases(),
        getParserValidationResults(),
        getParserImprovementSuggestions(),
      ]);
      setValidationCases(cases);
      setValidationResults(results);
      setImprovementSuggestions(suggestions);
    } catch (error) {
      setError(getErrorMessage(error, "Parser validation load failed"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    loadParserValidation();
  }, []);

  const validationCaseById = new Map(
    validationCases.map((validationCase) => [validationCase.id, validationCase]),
  );

  function chooseScenario(testCaseId: string) {
    const match = scenarios.find(([id]) => id === testCaseId);
    setForm((current) => ({
      ...current,
      test_case_id: testCaseId,
      test_name: match?.[1] ?? current.test_name,
    }));
  }

  function edit(item: OperationTestResult) {
    setEditingId(item.id);
    setForm({
      test_case_id: item.test_case_id,
      test_name: item.test_name,
      tester: item.tester ?? "",
      result: item.result,
      issue: item.issue ?? "",
      action_taken: item.action_taken ?? "",
      tested_at: item.tested_at ? item.tested_at.slice(0, 16) : "",
    });
  }

  async function submit() {
    try {
      setLoading(true);
      setError("");
      const payload = {
        ...form,
        tester: form.tester || null,
        issue: form.issue || null,
        action_taken: form.action_taken || null,
        tested_at: form.tested_at ? new Date(form.tested_at).toISOString() : null,
      };
      if (editingId) {
        await updateOperationTest(editingId, payload);
        setMessage(`Updated ${form.test_case_id}`);
      } else {
        await saveOperationTest(payload);
        setMessage(`Saved ${form.test_case_id}`);
      }
      setEditingId(null);
      setForm(defaultForm());
      await load();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "Operation test save failed");
      setError(errorMessage);
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  }

  async function hold(id: number) {
    try {
      setLoading(true);
      setError("");
      await holdOperationTest(id);
      setMessage("Result changed to HOLD");
      await load();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "Operation test hold failed");
      setError(errorMessage);
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  }

  function editValidationCase(item: ParserValidationCase) {
    setEditingValidationCaseId(item.id);
    setValidationForm({
      case_name: item.case_name,
      upload_id: item.upload_id,
      original_filename: item.original_filename,
      expected_customer_name: item.expected_customer_name,
      expected_code: item.expected_code,
      expected_gp_jpy: item.expected_gp_jpy,
      expected_decision: item.expected_decision,
      expected_transport_revenue_jpy: item.expected_transport_revenue_jpy,
      expected_transport_expense_jpy: item.expected_transport_expense_jpy,
      expected_customs_revenue_jpy: item.expected_customs_revenue_jpy,
      expected_customs_duty_jpy: item.expected_customs_duty_jpy,
      expected_consumption_tax_jpy: item.expected_consumption_tax_jpy,
      expected_partner_fee_jpy: item.expected_partner_fee_jpy,
      expected_partner_fee_usd: item.expected_partner_fee_usd,
      tolerance_jpy: item.tolerance_jpy,
      is_active: item.is_active,
    });
    setValidationUploadId(item.upload_id ?? "");
  }

  async function submitValidationCase() {
    try {
      setLoading(true);
      setError("");
      const payload = normalizeValidationPayload(validationForm);
      if (editingValidationCaseId) {
        await updateParserValidationCase(editingValidationCaseId, payload);
        setMessage(`Updated validation case: ${payload.case_name}`);
      } else {
        await saveParserValidationCase(payload);
        setMessage(`Saved validation case: ${payload.case_name}`);
      }
      setEditingValidationCaseId(null);
      await loadParserValidation();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "Parser validation case save failed");
      setError(errorMessage);
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  }

  async function runValidation(caseId: number, uploadId?: string | null) {
    const selectedUploadId = validationUploadId || uploadId || "";
    if (!selectedUploadId) {
      alert("upload_id를 입력하세요.");
      return;
    }
    try {
      setLoading(true);
      setError("");
      const result = await runParserValidation(caseId, selectedUploadId);
      setMessage(`Parser validation ${result.result}: ${result.diff_summary}`);
      await loadParserValidation();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "Parser validation run failed");
      setError(errorMessage);
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  }

  async function deactivateValidationCase(id: number) {
    try {
      setLoading(true);
      setError("");
      await deactivateParserValidationCase(id);
      await loadParserValidation();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "Parser validation case deactivate failed");
      setError(errorMessage);
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  }

  async function applySuggestion(id: number) {
    try {
      setLoading(true);
      setError("");
      await applyParserImprovementSuggestion(id);
      setMessage("Parser improvement suggestion applied");
      await loadParserValidation();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "Parser improvement apply failed");
      setError(errorMessage);
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  }

  async function rejectSuggestion(id: number) {
    try {
      setLoading(true);
      setError("");
      await rejectParserImprovementSuggestion(id);
      setMessage("Parser improvement suggestion rejected");
      await loadParserValidation();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "Parser improvement reject failed");
      setError(errorMessage);
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stack">
      {error && <div className="error-box">{error}</div>}
      {loading && <div className="loading">처리 중...</div>}

      <section className="panel">
        <div className="section-heading">
          <h2>Operation Test</h2>
          <div className="toolbar">
            <select value={filterResult} onChange={(event) => setFilterResult(event.target.value)}>
              <option value="">ALL</option>
              <option value="PASS">PASS</option>
              <option value="FAIL">FAIL</option>
              <option value="HOLD">HOLD</option>
            </select>
            <button type="button" onClick={load}>
              조회
            </button>
          </div>
        </div>
        <p className="meta-line">
          운영 전에는 docs/OPERATION_TEST_SCENARIOS.md 기준으로 전체 흐름을 검증하고 결과를 기록합니다.
        </p>
        <div className="meta-line">{message}</div>
      </section>

      <section className="panel">
        <h2>Test Result Form</h2>
        <div className="form-grid compact">
          <label className="field">
            <span>TC ID</span>
            <select value={form.test_case_id} onChange={(event) => chooseScenario(event.target.value)}>
              {scenarios.map(([id, name]) => (
                <option key={id} value={id}>
                  {id} {name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Test Name</span>
            <input
              value={form.test_name}
              onChange={(event) => setForm((current) => ({ ...current, test_name: event.target.value }))}
            />
          </label>
          <label className="field">
            <span>Tester</span>
            <input
              value={form.tester ?? ""}
              onChange={(event) => setForm((current) => ({ ...current, tester: event.target.value }))}
            />
          </label>
          <label className="field">
            <span>Result</span>
            <select
              value={form.result}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  result: event.target.value as OperationTestResult["result"],
                }))
              }
            >
              <option value="PASS">PASS</option>
              <option value="FAIL">FAIL</option>
              <option value="HOLD">HOLD</option>
            </select>
          </label>
          <label className="field">
            <span>Tested At</span>
            <input
              type="datetime-local"
              value={form.tested_at ?? ""}
              onChange={(event) => setForm((current) => ({ ...current, tested_at: event.target.value }))}
            />
          </label>
          <label className="field wide-field">
            <span>Issue</span>
            <input
              value={form.issue ?? ""}
              onChange={(event) => setForm((current) => ({ ...current, issue: event.target.value }))}
            />
          </label>
          <label className="field wide-field">
            <span>Action Taken</span>
            <input
              value={form.action_taken ?? ""}
              onChange={(event) => setForm((current) => ({ ...current, action_taken: event.target.value }))}
            />
          </label>
        </div>
        <div className="toolbar form-actions">
          <button type="button" onClick={submit}>
            {editingId ? "Update Result" : "Save Result"}
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              setEditingId(null);
              setForm(defaultForm());
            }}
          >
            Reset
          </button>
        </div>
      </section>

      <section className="panel">
        <h2>Test Results</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>TC ID</th>
                <th>테스트명</th>
                <th>담당자</th>
                <th>실행일</th>
                <th>결과</th>
                <th>이슈</th>
                <th>조치</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.test_case_id}</td>
                  <td>{item.test_name}</td>
                  <td>{item.tester ?? "-"}</td>
                  <td>{item.tested_at?.slice(0, 16).replace("T", " ") ?? "-"}</td>
                  <td>
                    <span className={badgeClass(item.result)}>{item.result}</span>
                  </td>
                  <td>{item.issue ?? "-"}</td>
                  <td>{item.action_taken ?? "-"}</td>
                  <td>
                    <div className="toolbar">
                      <button type="button" className="secondary-button" onClick={() => edit(item)}>
                        Edit
                      </button>
                      <button type="button" className="secondary-button" onClick={() => hold(item.id)}>
                        HOLD
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>Parser Validation</h2>
        <p className="meta-line">
          실제 Profit Sheet 업로드 파일의 upload_id를 입력하고 기대값과 파싱 결과를 비교합니다.
        </p>
        <div className="form-grid compact">
          <label className="field">
            <span>Case Name</span>
            <input
              value={validationForm.case_name}
              onChange={(event) =>
                setValidationForm((current) => ({ ...current, case_name: event.target.value }))
              }
            />
          </label>
          <label className="field">
            <span>Upload ID</span>
            <input
              value={validationUploadId}
              onChange={(event) => setValidationUploadId(event.target.value)}
            />
          </label>
          <label className="field">
            <span>Expected Customer</span>
            <input
              value={validationForm.expected_customer_name ?? ""}
              onChange={(event) =>
                setValidationForm((current) => ({ ...current, expected_customer_name: event.target.value }))
              }
            />
          </label>
          <label className="field">
            <span>Expected Code</span>
            <input
              value={validationForm.expected_code ?? ""}
              onChange={(event) =>
                setValidationForm((current) => ({ ...current, expected_code: event.target.value }))
              }
            />
          </label>
          <NumberField label="Expected GP" value={validationForm.expected_gp_jpy} onChange={(value) => setValidationForm((current) => ({ ...current, expected_gp_jpy: value }))} />
          <label className="field">
            <span>Expected Decision</span>
            <input
              value={validationForm.expected_decision ?? ""}
              onChange={(event) =>
                setValidationForm((current) => ({ ...current, expected_decision: event.target.value }))
              }
            />
          </label>
          <NumberField label="Transport Revenue" value={validationForm.expected_transport_revenue_jpy} onChange={(value) => setValidationForm((current) => ({ ...current, expected_transport_revenue_jpy: value }))} />
          <NumberField label="Transport Expense" value={validationForm.expected_transport_expense_jpy} onChange={(value) => setValidationForm((current) => ({ ...current, expected_transport_expense_jpy: value }))} />
          <NumberField label="Customs Revenue" value={validationForm.expected_customs_revenue_jpy} onChange={(value) => setValidationForm((current) => ({ ...current, expected_customs_revenue_jpy: value }))} />
          <NumberField label="Duty" value={validationForm.expected_customs_duty_jpy} onChange={(value) => setValidationForm((current) => ({ ...current, expected_customs_duty_jpy: value }))} />
          <NumberField label="Consumption Tax" value={validationForm.expected_consumption_tax_jpy} onChange={(value) => setValidationForm((current) => ({ ...current, expected_consumption_tax_jpy: value }))} />
          <NumberField label="Partner Fee JPY" value={validationForm.expected_partner_fee_jpy} onChange={(value) => setValidationForm((current) => ({ ...current, expected_partner_fee_jpy: value }))} />
          <NumberField label="Partner Fee USD" value={validationForm.expected_partner_fee_usd} onChange={(value) => setValidationForm((current) => ({ ...current, expected_partner_fee_usd: value }))} />
          <NumberField label="Tolerance JPY" value={validationForm.tolerance_jpy} onChange={(value) => setValidationForm((current) => ({ ...current, tolerance_jpy: value ?? 100 }))} />
        </div>
        <div className="toolbar form-actions">
          <button type="button" onClick={submitValidationCase}>
            {editingValidationCaseId ? "Update Validation Case" : "Add Validation Case"}
          </button>
          <button type="button" className="secondary-button" onClick={loadParserValidation}>
            Refresh
          </button>
        </div>
      </section>

      <section className="panel">
        <h2>Validation Cases</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Case</th>
                <th>Expected Code</th>
                <th className="number">Expected GP</th>
                <th>Decision</th>
                <th className="number">Tolerance</th>
                <th>Active</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {validationCases.map((item) => (
                <tr key={item.id}>
                  <td>{item.case_name}</td>
                  <td>{item.expected_code ?? "-"}</td>
                  <td className="number">{item.expected_gp_jpy == null ? "-" : formatJPY(item.expected_gp_jpy)}</td>
                  <td>{item.expected_decision ?? "-"}</td>
                  <td className="number">{formatJPY(item.tolerance_jpy)}</td>
                  <td>{item.is_active ? "Y" : "N"}</td>
                  <td>
                    <div className="toolbar">
                      <button type="button" className="secondary-button" onClick={() => editValidationCase(item)}>Edit</button>
                      <button type="button" className="secondary-button" onClick={() => runValidation(item.id, item.upload_id)}>Run</button>
                      <button type="button" className="secondary-button" onClick={() => deactivateValidationCase(item.id)} disabled={!item.is_active}>Disable</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>Validation Results</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Case</th>
                <th>Expected Code</th>
                <th>Parsed Code</th>
                <th className="number">Expected GP</th>
                <th className="number">Parsed GP</th>
                <th className="number">Diff</th>
                <th>Expected Decision</th>
                <th>Parsed Decision</th>
                <th>Confidence</th>
                <th>Result</th>
                <th>Diff Summary</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {validationResults.map((item) => {
                const validationCase = validationCaseById.get(item.validation_case_id);
                const gpDiff =
                  item.parsed_gp_jpy != null && validationCase?.expected_gp_jpy != null
                    ? item.parsed_gp_jpy - validationCase.expected_gp_jpy
                    : null;
                return (
                  <tr key={item.id}>
                    <td>{validationCase?.case_name ?? item.validation_case_id}</td>
                    <td>{validationCase?.expected_code ?? "-"}</td>
                    <td>{item.parsed_code ?? "-"}</td>
                    <td className="number">
                      {validationCase?.expected_gp_jpy == null
                        ? "-"
                        : formatJPY(validationCase.expected_gp_jpy)}
                    </td>
                    <td className="number">{item.parsed_gp_jpy == null ? "-" : formatJPY(item.parsed_gp_jpy)}</td>
                    <td className="number">{gpDiff == null ? "-" : formatJPY(gpDiff)}</td>
                    <td>{validationCase?.expected_decision ?? "-"}</td>
                    <td>{item.parsed_decision ?? "-"}</td>
                    <td>{item.confidence == null ? "-" : `${Math.round(item.confidence * 100)}%`}</td>
                    <td><span className={badgeClass(item.result)}>{item.result}</span></td>
                    <td>{item.diff_summary ?? "-"}</td>
                    <td>{item.created_at.slice(0, 19).replace("T", " ")}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>Parser Improvement Suggestions</h2>
        <p className="meta-line">
          Validation 결과가 PARTIAL 또는 FAIL이면 Template 키워드 보완 제안이 자동 생성됩니다.
        </p>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Case</th>
                <th>Issue Type</th>
                <th>Field</th>
                <th>Current</th>
                <th>Expected</th>
                <th>Suggested Keyword</th>
                <th>Suggestion</th>
                <th>Status</th>
                <th>Created</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {improvementSuggestions.map((item) => (
                <tr key={item.id}>
                  <td>{item.case_name}</td>
                  <td>{item.issue_type}</td>
                  <td>{item.field_name}</td>
                  <td>{item.current_value ?? "-"}</td>
                  <td>{item.expected_value ?? "-"}</td>
                  <td>{item.suggested_keyword ?? "-"}</td>
                  <td>{item.suggestion_text}</td>
                  <td><span className={badgeClass(item.status)}>{item.status}</span></td>
                  <td>{item.created_at.slice(0, 19).replace("T", " ")}</td>
                  <td>
                    <div className="toolbar">
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => applySuggestion(item.id)}
                        disabled={item.status !== "OPEN" || !item.suggested_keyword || !item.template_id}
                      >
                        Apply
                      </button>
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => rejectSuggestion(item.id)}
                        disabled={item.status !== "OPEN"}
                      >
                        Reject
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number | null;
  onChange: (value: number | null) => void;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        type="number"
        value={value ?? ""}
        onChange={(event) =>
          onChange(event.target.value === "" ? null : Number(event.target.value))
        }
      />
    </label>
  );
}

function normalizeValidationPayload(
  payload: Omit<ParserValidationCase, "id" | "created_at">,
) {
  return {
    ...payload,
    upload_id: payload.upload_id || null,
    original_filename: payload.original_filename || null,
    expected_customer_name: payload.expected_customer_name || null,
    expected_code: payload.expected_code || null,
    expected_decision: payload.expected_decision || null,
  };
}
