import { useEffect, useState } from "react";
import {
  deactivateInternalResourceRule,
  deactivateParserTemplate,
  deactivateUser,
  deactivateWorkCodeRule,
  deactivateRequiredChargeRule,
  getGpRateRules,
  getInternalResourceRules,
  getMinimumGpRules,
  getPartnerFees,
  getParserTemplates,
  getRequiredChargeRules,
  getUsers,
  getWorkCodeRules,
  saveInternalResourceRule,
  saveParserTemplate,
  saveRequiredChargeRule,
  saveUser,
  saveWorkCodeRule,
  seedDefaults,
  updateInternalResourceRule,
  updateParserTemplate,
  updateRequiredChargeRule,
  updateUser,
  updateWorkCodeRule,
  type InternalResourceRule,
  type ParserTemplate,
  type RequiredChargeRule,
  type User,
  type UserPayload,
  type WorkCodeRule,
} from "../api/client";
import { formatJPY } from "../format";
import { getErrorMessage } from "../error";

export function MasterPage() {
  const [partnerFees, setPartnerFees] = useState<any[]>([]);
  const [minimumGpRules, setMinimumGpRules] = useState<any[]>([]);
  const [gpRateRules, setGpRateRules] = useState<any[]>([]);
  const [workCodeRules, setWorkCodeRules] = useState<any[]>([]);
  const [internalResourceRules, setInternalResourceRules] = useState<InternalResourceRule[]>([]);
  const [requiredChargeRules, setRequiredChargeRules] = useState<RequiredChargeRule[]>([]);
  const [parserTemplates, setParserTemplates] = useState<ParserTemplate[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [editingWorkCodeId, setEditingWorkCodeId] = useState<number | null>(null);
  const [editingRequiredChargeId, setEditingRequiredChargeId] = useState<number | null>(null);
  const [editingInternalResourceId, setEditingInternalResourceId] = useState<number | null>(null);
  const [editingParserTemplateId, setEditingParserTemplateId] = useState<number | null>(null);
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [workCodeForm, setWorkCodeForm] = useState<Omit<WorkCodeRule, "id">>({
    code: "SE",
    name: "SE",
    mode: "SEA",
    direction: "EXPORT",
    has_customs: false,
    has_transport: false,
    has_work: false,
    point: 1,
    description: "",
    is_active: true,
  });
  const [requiredChargeForm, setRequiredChargeForm] = useState<Omit<RequiredChargeRule, "id">>({
    code: "SE",
    mode: "SEA",
    direction: "EXPORT",
    charge_name: "THC",
    keywords: "THC",
    required_when: "ALWAYS",
    severity: "WARN",
    description: "",
    is_active: true,
  });
  const [internalResourceForm, setInternalResourceForm] = useState<Omit<InternalResourceRule, "id">>({
    resource_type: "CUSTOMS",
    port: "TOKYO",
    location_name: "",
    vendor_name: "",
    priority: 1,
    mandatory: true,
    description: "",
    is_active: true,
  });
  const [parserTemplateForm, setParserTemplateForm] = useState<Omit<ParserTemplate, "id">>({
    template_name: "LOTOS_STANDARD_PDF",
    description: "",
    mode: "ANY",
    direction: "ANY",
    file_type: "PDF",
    customer_keyword: "CUSTOMER,Customer,고객,CONSIGNEE,SHIPPER",
    partner_keyword: "PARTNER,AGENT,파트너",
    revenue_section_keywords: "REVENUE,BILLING,DEBIT,請求,청구,매출",
    expense_section_keywords: "EXPENSE,COST,CREDIT,支払,原価,비용,원가",
    profit_keywords: "PROFIT,GP,GROSS PROFIT,差益,이익",
    duty_keywords: "DUTY,関税,관세",
    consumption_tax_keywords: "CONSUMPTION TAX,VAT,消費税,소비세",
    transport_keywords: "DRAYAGE,TRUCKING,TRANSPORT,DELIVERY,運送,配送,운송,배송",
    customs_keywords: "CUSTOMS,CUSTOM,通関,통관",
    partner_fee_keywords: "PARTNER FEE,AGENT FEE,CREDIT,パートナー,파트너",
    food_keywords: "FOOD,FROZEN,食品,식품,냉동",
    is_default: false,
    is_active: true,
  });
  const [userForm, setUserForm] = useState<UserPayload>({
    username: "staff",
    display_name: "담당자",
    email: "",
    role: "STAFF",
    department: "",
    password: "",
    is_active: true,
  });

  async function load() {
    try {
      setError("");
      const [fees, gpRules, rateRules, codeRules, resourceRules, chargeRules, templates, userRows] = await Promise.all([
        getPartnerFees(),
        getMinimumGpRules(),
        getGpRateRules(),
        getWorkCodeRules(),
        getInternalResourceRules(),
        getRequiredChargeRules(),
        getParserTemplates(),
        getUsers(),
      ]);
      setPartnerFees(fees);
      setMinimumGpRules(gpRules);
      setGpRateRules(rateRules);
      setWorkCodeRules(codeRules);
      setInternalResourceRules(resourceRules);
      setRequiredChargeRules(chargeRules);
      setParserTemplates(templates);
      setUsers(userRows);
    } catch (error) {
      setError(getErrorMessage(error, "Master 조회 실패"));
    }
  }

  async function runSeed() {
    try {
      setError("");
      const result = await seedDefaults();
      setMessage(
        `seed complete: partner ${result.partner_fee_rules_created}, minimum GP ${result.minimum_gp_rules_upserted}, GP rate ${result.gp_rate_rules_upserted}, work code ${result.work_code_rules_upserted}, resource ${result.internal_resource_rules_upserted}, parser ${result.parser_templates_upserted}, users ${result.users_upserted}`,
      );
      await load();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "Master seed 실패");
      setError(errorMessage);
      alert(errorMessage);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function editWorkCode(rule: WorkCodeRule) {
    setEditingWorkCodeId(rule.id);
    setWorkCodeForm({
      code: rule.code,
      name: rule.name,
      mode: rule.mode ?? "PROJECT",
      direction: rule.direction ?? "BOTH",
      has_customs: rule.has_customs,
      has_transport: rule.has_transport,
      has_work: rule.has_work,
      point: rule.point,
      description: rule.description ?? "",
      is_active: rule.is_active,
    });
  }

  function resetWorkCodeForm() {
    setEditingWorkCodeId(null);
    setWorkCodeForm({
      code: "SE",
      name: "SE",
      mode: "SEA",
      direction: "EXPORT",
      has_customs: false,
      has_transport: false,
      has_work: false,
      point: 1,
      description: "",
      is_active: true,
    });
  }

  function workCodePayload() {
    return {
      ...workCodeForm,
      mode: workCodeForm.mode === "PROJECT" ? null : workCodeForm.mode,
      direction: workCodeForm.direction === "BOTH" ? null : workCodeForm.direction,
      description: workCodeForm.description || null,
    };
  }

  async function submitWorkCode() {
    try {
      setError("");
      if (editingWorkCodeId) {
        await updateWorkCodeRule(editingWorkCodeId, workCodePayload());
        setMessage(`work code updated: ${workCodeForm.code}`);
      } else {
        await saveWorkCodeRule(workCodePayload());
        setMessage(`work code saved: ${workCodeForm.code}`);
      }
      resetWorkCodeForm();
      await load();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "Work Code 저장 실패");
      setError(errorMessage);
      alert(errorMessage);
    }
  }

  async function deactivateWorkCode(id: number) {
    try {
      setError("");
      await deactivateWorkCodeRule(id);
      setMessage("work code deactivated");
      await load();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "Work Code 비활성화 실패");
      setError(errorMessage);
      alert(errorMessage);
    }
  }

  function editRequiredCharge(rule: RequiredChargeRule) {
    setEditingRequiredChargeId(rule.id);
    setRequiredChargeForm({
      code: rule.code,
      mode: rule.mode,
      direction: rule.direction,
      charge_name: rule.charge_name,
      keywords: rule.keywords,
      required_when: rule.required_when,
      severity: rule.severity,
      description: rule.description ?? "",
      is_active: rule.is_active,
    });
  }

  function resetRequiredChargeForm() {
    setEditingRequiredChargeId(null);
    setRequiredChargeForm({
      code: "SE",
      mode: "SEA",
      direction: "EXPORT",
      charge_name: "THC",
      keywords: "THC",
      required_when: "ALWAYS",
      severity: "WARN",
      description: "",
      is_active: true,
    });
  }

  function requiredChargePayload() {
    return {
      ...requiredChargeForm,
      description: requiredChargeForm.description || null,
    };
  }

  async function submitRequiredCharge() {
    try {
      setError("");
      if (editingRequiredChargeId) {
        await updateRequiredChargeRule(editingRequiredChargeId, requiredChargePayload());
        setMessage(`required charge updated: ${requiredChargeForm.charge_name}`);
      } else {
        await saveRequiredChargeRule(requiredChargePayload());
        setMessage(`required charge saved: ${requiredChargeForm.charge_name}`);
      }
      resetRequiredChargeForm();
      await load();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "Required Charge 저장 실패");
      setError(errorMessage);
      alert(errorMessage);
    }
  }

  async function deactivateRequiredCharge(id: number) {
    try {
      setError("");
      await deactivateRequiredChargeRule(id);
      setMessage("required charge deactivated");
      await load();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "Required Charge 비활성화 실패");
      setError(errorMessage);
      alert(errorMessage);
    }
  }

  function editInternalResource(rule: InternalResourceRule) {
    setEditingInternalResourceId(rule.id);
    setInternalResourceForm({
      resource_type: rule.resource_type,
      port: rule.port,
      location_name: rule.location_name ?? "",
      vendor_name: rule.vendor_name ?? "",
      priority: rule.priority,
      mandatory: rule.mandatory,
      description: rule.description ?? "",
      is_active: rule.is_active,
    });
  }

  function resetInternalResourceForm() {
    setEditingInternalResourceId(null);
    setInternalResourceForm({
      resource_type: "CUSTOMS",
      port: "TOKYO",
      location_name: "",
      vendor_name: "",
      priority: 1,
      mandatory: true,
      description: "",
      is_active: true,
    });
  }

  function internalResourcePayload() {
    return {
      ...internalResourceForm,
      location_name: internalResourceForm.location_name || null,
      vendor_name: internalResourceForm.vendor_name || null,
      description: internalResourceForm.description || null,
    };
  }

  async function submitInternalResource() {
    try {
      setError("");
      if (editingInternalResourceId) {
        await updateInternalResourceRule(editingInternalResourceId, internalResourcePayload());
        setMessage(`internal resource updated: ${internalResourceForm.resource_type}/${internalResourceForm.port}`);
      } else {
        await saveInternalResourceRule(internalResourcePayload());
        setMessage(`internal resource saved: ${internalResourceForm.resource_type}/${internalResourceForm.port}`);
      }
      resetInternalResourceForm();
      await load();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "Internal Resource 저장 실패");
      setError(errorMessage);
      alert(errorMessage);
    }
  }

  async function deactivateInternalResource(id: number) {
    try {
      setError("");
      await deactivateInternalResourceRule(id);
      setMessage("internal resource deactivated");
      await load();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "Internal Resource 비활성화 실패");
      setError(errorMessage);
      alert(errorMessage);
    }
  }

  function editParserTemplate(rule: ParserTemplate) {
    setEditingParserTemplateId(rule.id);
    setParserTemplateForm({
      template_name: rule.template_name,
      description: rule.description ?? "",
      mode: rule.mode ?? "ANY",
      direction: rule.direction ?? "ANY",
      file_type: rule.file_type,
      customer_keyword: rule.customer_keyword ?? "",
      partner_keyword: rule.partner_keyword ?? "",
      revenue_section_keywords: rule.revenue_section_keywords,
      expense_section_keywords: rule.expense_section_keywords,
      profit_keywords: rule.profit_keywords,
      duty_keywords: rule.duty_keywords,
      consumption_tax_keywords: rule.consumption_tax_keywords,
      transport_keywords: rule.transport_keywords,
      customs_keywords: rule.customs_keywords,
      partner_fee_keywords: rule.partner_fee_keywords,
      food_keywords: rule.food_keywords,
      is_default: rule.is_default,
      is_active: rule.is_active,
    });
  }

  function resetParserTemplateForm() {
    setEditingParserTemplateId(null);
    setParserTemplateForm({
      template_name: "LOTOS_STANDARD_PDF",
      description: "",
      mode: "ANY",
      direction: "ANY",
      file_type: "PDF",
      customer_keyword: "CUSTOMER,Customer,고객,CONSIGNEE,SHIPPER",
      partner_keyword: "PARTNER,AGENT,파트너",
      revenue_section_keywords: "REVENUE,BILLING,DEBIT,請求,청구,매출",
      expense_section_keywords: "EXPENSE,COST,CREDIT,支払,原価,비용,원가",
      profit_keywords: "PROFIT,GP,GROSS PROFIT,差益,이익",
      duty_keywords: "DUTY,関税,관세",
      consumption_tax_keywords: "CONSUMPTION TAX,VAT,消費税,소비세",
      transport_keywords: "DRAYAGE,TRUCKING,TRANSPORT,DELIVERY,運送,配送,운송,배송",
      customs_keywords: "CUSTOMS,CUSTOM,通関,통관",
      partner_fee_keywords: "PARTNER FEE,AGENT FEE,CREDIT,パートナー,파트너",
      food_keywords: "FOOD,FROZEN,食品,식품,냉동",
      is_default: false,
      is_active: true,
    });
  }

  function parserTemplatePayload() {
    return {
      ...parserTemplateForm,
      description: parserTemplateForm.description || null,
      mode: parserTemplateForm.mode || "ANY",
      direction: parserTemplateForm.direction || "ANY",
      customer_keyword: parserTemplateForm.customer_keyword || null,
      partner_keyword: parserTemplateForm.partner_keyword || null,
    };
  }

  async function submitParserTemplate() {
    try {
      setError("");
      if (editingParserTemplateId) {
        await updateParserTemplate(editingParserTemplateId, parserTemplatePayload());
        setMessage(`parser template updated: ${parserTemplateForm.template_name}`);
      } else {
        await saveParserTemplate(parserTemplatePayload());
        setMessage(`parser template saved: ${parserTemplateForm.template_name}`);
      }
      resetParserTemplateForm();
      await load();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "Parser Template 저장 실패");
      setError(errorMessage);
      alert(errorMessage);
    }
  }

  async function deactivateTemplate(id: number) {
    try {
      setError("");
      await deactivateParserTemplate(id);
      setMessage("parser template deactivated");
      await load();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "Parser Template 비활성화 실패");
      setError(errorMessage);
      alert(errorMessage);
    }
  }

  function editUser(user: User) {
    setEditingUserId(user.id);
    setUserForm({
      username: user.username,
      display_name: user.display_name,
      email: user.email ?? "",
      role: user.role,
      department: user.department ?? "",
      password: "",
      is_active: user.is_active,
    });
  }

  function resetUserForm() {
    setEditingUserId(null);
    setUserForm({
      username: "staff",
      display_name: "담당자",
      email: "",
      role: "STAFF",
      department: "",
      password: "",
      is_active: true,
    });
  }

  async function submitUser() {
    try {
      setError("");
      const payload = {
        ...userForm,
        email: userForm.email || null,
        department: userForm.department || null,
        password: userForm.password || null,
      };
      if (editingUserId) {
        await updateUser(editingUserId, payload);
        setMessage(`user updated: ${userForm.username}`);
      } else {
        await saveUser(payload);
        setMessage(`user saved: ${userForm.username}`);
      }
      resetUserForm();
      await load();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "User 저장 실패");
      setError(errorMessage);
      alert(errorMessage);
    }
  }

  async function deactivateUserRow(id: number) {
    try {
      setError("");
      await deactivateUser(id);
      setMessage("user deactivated");
      await load();
    } catch (error) {
      const errorMessage = getErrorMessage(error, "User 비활성화 실패");
      setError(errorMessage);
      alert(errorMessage);
    }
  }

  return (
    <div className="stack">
      {error && <div className="error-box">{error}</div>}
      <section className="panel">
        <h2>Master Data</h2>
        <div className="toolbar">
          <button type="button" onClick={runSeed}>
            Seed Defaults
          </button>
          <button type="button" onClick={load}>
            Refresh
          </button>
        </div>
        <div className="meta-line">{message}</div>
      </section>

      <section className="panel">
        <h2>Partner Fee Master</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Partner</th>
                <th>Mode</th>
                <th>Direction</th>
                <th>Container</th>
                <th>Unit</th>
                <th>Currency</th>
                <th className="number">Amount</th>
                <th>Settlement</th>
              </tr>
            </thead>
            <tbody>
              {partnerFees.map((rule) => (
                <tr key={rule.id}>
                  <td>{rule.partner_name}</td>
                  <td>{rule.mode}</td>
                  <td>{rule.direction}</td>
                  <td>{rule.container_type ?? "-"}</td>
                  <td>{rule.unit_type}</td>
                  <td>{rule.currency}</td>
                  <td className="number">{rule.currency === "JPY" ? formatJPY(rule.amount) : rule.amount}</td>
                  <td>{rule.settlement_direction}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>Minimum GP Master</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th className="number">Minimum GP</th>
                <th>Description</th>
                <th>Active</th>
              </tr>
            </thead>
            <tbody>
              {minimumGpRules.map((rule) => (
                <tr key={rule.id}>
                  <td>{rule.code}</td>
                  <td className="number">{formatJPY(rule.minimum_gp_jpy)}</td>
                  <td>{rule.description ?? "-"}</td>
                  <td>{rule.is_active ? "Y" : "N"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>GP Rate Master</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Trade Type</th>
                <th className="number">Minimum GP Rate</th>
                <th>Description</th>
                <th>Active</th>
              </tr>
            </thead>
            <tbody>
              {gpRateRules.map((rule) => (
                <tr key={rule.id}>
                  <td>{rule.trade_type}</td>
                  <td className="number">{(rule.minimum_gp_rate * 100).toFixed(1)}%</td>
                  <td>{rule.description ?? "-"}</td>
                  <td>{rule.is_active ? "Y" : "N"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>Work Code / Point Master</h2>
        <div className="info-box">
          <strong>생산성 기준:</strong> 1인당 월 80 Point 기준 / 120 이상 우수 / 80~119 정상 / 60~79 관리 / 60 미만 개선
        </div>
        <div className="form-grid">
          <label className="field">
            <span>Code</span>
            <select
              value={workCodeForm.code}
              onChange={(event) =>
                setWorkCodeForm((current) => ({
                  ...current,
                  code: event.target.value,
                  name: current.name || event.target.value,
                }))
              }
            >
              {[
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
                "PJT",
              ].map((code) => (
                <option key={code} value={code}>
                  {code}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Name</span>
            <input
              type="text"
              value={workCodeForm.name}
              onChange={(event) =>
                setWorkCodeForm((current) => ({ ...current, name: event.target.value }))
              }
            />
          </label>
          <label className="field">
            <span>Mode</span>
            <select
              value={workCodeForm.mode ?? "PROJECT"}
              onChange={(event) =>
                setWorkCodeForm((current) => ({ ...current, mode: event.target.value }))
              }
            >
              <option value="SEA">SEA</option>
              <option value="AIR">AIR</option>
              <option value="PROJECT">PROJECT</option>
            </select>
          </label>
          <label className="field">
            <span>Direction</span>
            <select
              value={workCodeForm.direction ?? "BOTH"}
              onChange={(event) =>
                setWorkCodeForm((current) => ({
                  ...current,
                  direction: event.target.value,
                }))
              }
            >
              <option value="EXPORT">EXPORT</option>
              <option value="IMPORT">IMPORT</option>
              <option value="BOTH">BOTH</option>
            </select>
          </label>
          <label className="field">
            <span>Point</span>
            <input
              type="number"
              min="0"
              step="0.1"
              value={workCodeForm.point}
              onChange={(event) =>
                setWorkCodeForm((current) => ({
                  ...current,
                  point: Number(event.target.value),
                }))
              }
            />
          </label>
          <label className="field">
            <span>Description</span>
            <input
              type="text"
              value={workCodeForm.description ?? ""}
              onChange={(event) =>
                setWorkCodeForm((current) => ({
                  ...current,
                  description: event.target.value,
                }))
              }
            />
          </label>
          <label className="check-field">
            <input
              type="checkbox"
              checked={workCodeForm.has_customs}
              onChange={(event) =>
                setWorkCodeForm((current) => ({
                  ...current,
                  has_customs: event.target.checked,
                }))
              }
            />
            <span>Customs</span>
          </label>
          <label className="check-field">
            <input
              type="checkbox"
              checked={workCodeForm.has_transport}
              onChange={(event) =>
                setWorkCodeForm((current) => ({
                  ...current,
                  has_transport: event.target.checked,
                }))
              }
            />
            <span>Transport</span>
          </label>
          <label className="check-field">
            <input
              type="checkbox"
              checked={workCodeForm.has_work}
              onChange={(event) =>
                setWorkCodeForm((current) => ({
                  ...current,
                  has_work: event.target.checked,
                }))
              }
            />
            <span>Work</span>
          </label>
          <label className="check-field">
            <input
              type="checkbox"
              checked={workCodeForm.is_active}
              onChange={(event) =>
                setWorkCodeForm((current) => ({
                  ...current,
                  is_active: event.target.checked,
                }))
              }
            />
            <span>Active</span>
          </label>
        </div>
        <div className="toolbar form-actions">
          <button type="button" onClick={submitWorkCode}>
            {editingWorkCodeId ? "Update Work Code" : "Add Work Code"}
          </button>
          <button type="button" className="secondary-button" onClick={resetWorkCodeForm}>
            Reset
          </button>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Mode</th>
                <th>Direction</th>
                <th>Customs</th>
                <th>Transport</th>
                <th>Work</th>
                <th className="number">Point</th>
                <th>Description</th>
                <th>Active</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {workCodeRules.map((rule) => (
                <tr key={rule.id}>
                  <td>{rule.code}</td>
                  <td>{rule.name}</td>
                  <td>{rule.mode ?? "-"}</td>
                  <td>{rule.direction ?? "-"}</td>
                  <td>{rule.has_customs ? "Y" : "N"}</td>
                  <td>{rule.has_transport ? "Y" : "N"}</td>
                  <td>{rule.has_work ? "Y" : "N"}</td>
                  <td className="number">{rule.point}</td>
                  <td>{rule.description ?? "-"}</td>
                  <td>{rule.is_active ? "Y" : "N"}</td>
                  <td>
                    <div className="toolbar">
                      <button type="button" className="secondary-button" onClick={() => editWorkCode(rule)}>
                        Edit
                      </button>
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => deactivateWorkCode(rule.id)}
                        disabled={!rule.is_active}
                      >
                        Disable
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
        <h2>Required Charge Rules</h2>
        <div className="form-grid">
          <label className="field">
            <span>Code</span>
            <input
              type="text"
              value={requiredChargeForm.code}
              onChange={(event) =>
                setRequiredChargeForm((current) => ({
                  ...current,
                  code: event.target.value,
                }))
              }
            />
          </label>
          <label className="field">
            <span>Mode</span>
            <select
              value={requiredChargeForm.mode}
              onChange={(event) =>
                setRequiredChargeForm((current) => ({
                  ...current,
                  mode: event.target.value,
                }))
              }
            >
              <option value="ANY">ANY</option>
              <option value="SEA">SEA</option>
              <option value="AIR">AIR</option>
            </select>
          </label>
          <label className="field">
            <span>Direction</span>
            <select
              value={requiredChargeForm.direction}
              onChange={(event) =>
                setRequiredChargeForm((current) => ({
                  ...current,
                  direction: event.target.value,
                }))
              }
            >
              <option value="ANY">ANY</option>
              <option value="EXPORT">EXPORT</option>
              <option value="IMPORT">IMPORT</option>
            </select>
          </label>
          <label className="field">
            <span>Charge Name</span>
            <input
              type="text"
              value={requiredChargeForm.charge_name}
              onChange={(event) =>
                setRequiredChargeForm((current) => ({
                  ...current,
                  charge_name: event.target.value,
                }))
              }
            />
          </label>
          <label className="field">
            <span>Keywords</span>
            <input
              type="text"
              value={requiredChargeForm.keywords}
              onChange={(event) =>
                setRequiredChargeForm((current) => ({
                  ...current,
                  keywords: event.target.value,
                }))
              }
            />
          </label>
          <label className="field">
            <span>Required When</span>
            <select
              value={requiredChargeForm.required_when}
              onChange={(event) =>
                setRequiredChargeForm((current) => ({
                  ...current,
                  required_when: event.target.value,
                }))
              }
            >
              <option value="ALWAYS">ALWAYS</option>
              <option value="CUSTOMS">CUSTOMS</option>
              <option value="TRANSPORT">TRANSPORT</option>
              <option value="FOOD">FOOD</option>
              <option value="IMPORT">IMPORT</option>
              <option value="EXPORT">EXPORT</option>
            </select>
          </label>
          <label className="field">
            <span>Severity</span>
            <select
              value={requiredChargeForm.severity}
              onChange={(event) =>
                setRequiredChargeForm((current) => ({
                  ...current,
                  severity: event.target.value,
                }))
              }
            >
              <option value="WARN">WARN</option>
              <option value="NG">NG</option>
            </select>
          </label>
          <label className="field">
            <span>Description</span>
            <input
              type="text"
              value={requiredChargeForm.description ?? ""}
              onChange={(event) =>
                setRequiredChargeForm((current) => ({
                  ...current,
                  description: event.target.value,
                }))
              }
            />
          </label>
          <label className="check-field">
            <input
              type="checkbox"
              checked={requiredChargeForm.is_active}
              onChange={(event) =>
                setRequiredChargeForm((current) => ({
                  ...current,
                  is_active: event.target.checked,
                }))
              }
            />
            <span>Active</span>
          </label>
        </div>
        <div className="toolbar form-actions">
          <button type="button" onClick={submitRequiredCharge}>
            {editingRequiredChargeId ? "Update Required Charge" : "Add Required Charge"}
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={resetRequiredChargeForm}
          >
            Reset
          </button>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Mode</th>
                <th>Direction</th>
                <th>Charge</th>
                <th>Keywords</th>
                <th>Required When</th>
                <th>Severity</th>
                <th>Description</th>
                <th>Active</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {requiredChargeRules.map((rule) => (
                <tr key={rule.id}>
                  <td>{rule.code}</td>
                  <td>{rule.mode}</td>
                  <td>{rule.direction}</td>
                  <td>{rule.charge_name}</td>
                  <td>{rule.keywords}</td>
                  <td>{rule.required_when}</td>
                  <td>{rule.severity}</td>
                  <td>{rule.description ?? "-"}</td>
                  <td>{rule.is_active ? "Y" : "N"}</td>
                  <td>
                    <div className="toolbar">
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => editRequiredCharge(rule)}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => deactivateRequiredCharge(rule.id)}
                        disabled={!rule.is_active}
                      >
                        Disable
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
        <h2>Internal Resource Master</h2>
        <div className="form-grid">
          <label className="field">
            <span>Resource Type</span>
            <select
              value={internalResourceForm.resource_type}
              onChange={(event) =>
                setInternalResourceForm((current) => ({
                  ...current,
                  resource_type: event.target.value,
                }))
              }
            >
              <option value="CUSTOMS">CUSTOMS</option>
              <option value="WAREHOUSE">WAREHOUSE</option>
              <option value="TRANSPORT">TRANSPORT</option>
            </select>
          </label>
          <label className="field">
            <span>Port</span>
            <input
              type="text"
              value={internalResourceForm.port}
              onChange={(event) =>
                setInternalResourceForm((current) => ({
                  ...current,
                  port: event.target.value,
                }))
              }
            />
          </label>
          <label className="field">
            <span>Location Name</span>
            <input
              type="text"
              value={internalResourceForm.location_name ?? ""}
              onChange={(event) =>
                setInternalResourceForm((current) => ({
                  ...current,
                  location_name: event.target.value,
                }))
              }
            />
          </label>
          <label className="field">
            <span>Vendor Name</span>
            <input
              type="text"
              value={internalResourceForm.vendor_name ?? ""}
              onChange={(event) =>
                setInternalResourceForm((current) => ({
                  ...current,
                  vendor_name: event.target.value,
                }))
              }
            />
          </label>
          <label className="field">
            <span>Priority</span>
            <input
              type="number"
              min="1"
              value={internalResourceForm.priority}
              onChange={(event) =>
                setInternalResourceForm((current) => ({
                  ...current,
                  priority: Number(event.target.value),
                }))
              }
            />
          </label>
          <label className="field">
            <span>Description</span>
            <input
              type="text"
              value={internalResourceForm.description ?? ""}
              onChange={(event) =>
                setInternalResourceForm((current) => ({
                  ...current,
                  description: event.target.value,
                }))
              }
            />
          </label>
          <label className="check-field">
            <input
              type="checkbox"
              checked={internalResourceForm.mandatory}
              onChange={(event) =>
                setInternalResourceForm((current) => ({
                  ...current,
                  mandatory: event.target.checked,
                }))
              }
            />
            <span>Mandatory</span>
          </label>
          <label className="check-field">
            <input
              type="checkbox"
              checked={internalResourceForm.is_active}
              onChange={(event) =>
                setInternalResourceForm((current) => ({
                  ...current,
                  is_active: event.target.checked,
                }))
              }
            />
            <span>Active</span>
          </label>
        </div>
        <div className="toolbar form-actions">
          <button type="button" onClick={submitInternalResource}>
            {editingInternalResourceId ? "Update Internal Resource" : "Add Internal Resource"}
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={resetInternalResourceForm}
          >
            Reset
          </button>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Resource Type</th>
                <th>Port</th>
                <th>Location</th>
                <th>Vendor</th>
                <th className="number">Priority</th>
                <th>Mandatory</th>
                <th>Description</th>
                <th>Active</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {internalResourceRules.map((rule) => (
                <tr key={rule.id}>
                  <td>{rule.resource_type}</td>
                  <td>{rule.port}</td>
                  <td>{rule.location_name ?? "-"}</td>
                  <td>{rule.vendor_name ?? "-"}</td>
                  <td className="number">{rule.priority}</td>
                  <td>{rule.mandatory ? "Y" : "N"}</td>
                  <td>{rule.description ?? "-"}</td>
                  <td>{rule.is_active ? "Y" : "N"}</td>
                  <td>
                    <div className="toolbar">
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => editInternalResource(rule)}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => deactivateInternalResource(rule.id)}
                        disabled={!rule.is_active}
                      >
                        Disable
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
        <h2>Parser Templates</h2>
        <div className="info-box">
          Parser Template은 Profit Sheet 양식별 키워드와 추출 기준을 DB로 관리합니다.
        </div>
        <div className="form-grid">
          <label className="field">
            <span>Template Name</span>
            <input
              type="text"
              value={parserTemplateForm.template_name}
              onChange={(event) =>
                setParserTemplateForm((current) => ({
                  ...current,
                  template_name: event.target.value,
                }))
              }
            />
          </label>
          <label className="field">
            <span>File Type</span>
            <select
              value={parserTemplateForm.file_type}
              onChange={(event) =>
                setParserTemplateForm((current) => ({
                  ...current,
                  file_type: event.target.value,
                }))
              }
            >
              <option value="PDF">PDF</option>
              <option value="EXCEL">EXCEL</option>
              <option value="ANY">ANY</option>
            </select>
          </label>
          <label className="field">
            <span>Mode</span>
            <select
              value={parserTemplateForm.mode ?? "ANY"}
              onChange={(event) =>
                setParserTemplateForm((current) => ({
                  ...current,
                  mode: event.target.value,
                }))
              }
            >
              <option value="ANY">ANY</option>
              <option value="SEA">SEA</option>
              <option value="AIR">AIR</option>
            </select>
          </label>
          <label className="field">
            <span>Direction</span>
            <select
              value={parserTemplateForm.direction ?? "ANY"}
              onChange={(event) =>
                setParserTemplateForm((current) => ({
                  ...current,
                  direction: event.target.value,
                }))
              }
            >
              <option value="ANY">ANY</option>
              <option value="EXPORT">EXPORT</option>
              <option value="IMPORT">IMPORT</option>
            </select>
          </label>
          <label className="field">
            <span>Description</span>
            <input
              type="text"
              value={parserTemplateForm.description ?? ""}
              onChange={(event) =>
                setParserTemplateForm((current) => ({
                  ...current,
                  description: event.target.value,
                }))
              }
            />
          </label>
          <label className="field">
            <span>Revenue Keywords</span>
            <input
              type="text"
              value={parserTemplateForm.revenue_section_keywords}
              onChange={(event) =>
                setParserTemplateForm((current) => ({
                  ...current,
                  revenue_section_keywords: event.target.value,
                }))
              }
            />
          </label>
          <label className="field">
            <span>Expense Keywords</span>
            <input
              type="text"
              value={parserTemplateForm.expense_section_keywords}
              onChange={(event) =>
                setParserTemplateForm((current) => ({
                  ...current,
                  expense_section_keywords: event.target.value,
                }))
              }
            />
          </label>
          <label className="field">
            <span>Profit Keywords</span>
            <input
              type="text"
              value={parserTemplateForm.profit_keywords}
              onChange={(event) =>
                setParserTemplateForm((current) => ({
                  ...current,
                  profit_keywords: event.target.value,
                }))
              }
            />
          </label>
          <label className="field">
            <span>Duty Keywords</span>
            <input
              type="text"
              value={parserTemplateForm.duty_keywords}
              onChange={(event) =>
                setParserTemplateForm((current) => ({
                  ...current,
                  duty_keywords: event.target.value,
                }))
              }
            />
          </label>
          <label className="field">
            <span>Consumption Tax Keywords</span>
            <input
              type="text"
              value={parserTemplateForm.consumption_tax_keywords}
              onChange={(event) =>
                setParserTemplateForm((current) => ({
                  ...current,
                  consumption_tax_keywords: event.target.value,
                }))
              }
            />
          </label>
          <label className="field">
            <span>Transport Keywords</span>
            <input
              type="text"
              value={parserTemplateForm.transport_keywords}
              onChange={(event) =>
                setParserTemplateForm((current) => ({
                  ...current,
                  transport_keywords: event.target.value,
                }))
              }
            />
          </label>
          <label className="field">
            <span>Customs Keywords</span>
            <input
              type="text"
              value={parserTemplateForm.customs_keywords}
              onChange={(event) =>
                setParserTemplateForm((current) => ({
                  ...current,
                  customs_keywords: event.target.value,
                }))
              }
            />
          </label>
          <label className="field">
            <span>Partner Fee Keywords</span>
            <input
              type="text"
              value={parserTemplateForm.partner_fee_keywords}
              onChange={(event) =>
                setParserTemplateForm((current) => ({
                  ...current,
                  partner_fee_keywords: event.target.value,
                }))
              }
            />
          </label>
          <label className="field">
            <span>Food Keywords</span>
            <input
              type="text"
              value={parserTemplateForm.food_keywords}
              onChange={(event) =>
                setParserTemplateForm((current) => ({
                  ...current,
                  food_keywords: event.target.value,
                }))
              }
            />
          </label>
          <label className="check-field">
            <input
              type="checkbox"
              checked={parserTemplateForm.is_default}
              onChange={(event) =>
                setParserTemplateForm((current) => ({
                  ...current,
                  is_default: event.target.checked,
                }))
              }
            />
            <span>Default</span>
          </label>
          <label className="check-field">
            <input
              type="checkbox"
              checked={parserTemplateForm.is_active}
              onChange={(event) =>
                setParserTemplateForm((current) => ({
                  ...current,
                  is_active: event.target.checked,
                }))
              }
            />
            <span>Active</span>
          </label>
        </div>
        <div className="toolbar form-actions">
          <button type="button" onClick={submitParserTemplate}>
            {editingParserTemplateId ? "Update Parser Template" : "Add Parser Template"}
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={resetParserTemplateForm}
          >
            Reset
          </button>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Template</th>
                <th>File Type</th>
                <th>Mode</th>
                <th>Direction</th>
                <th>Default</th>
                <th>Active</th>
                <th>Description</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {parserTemplates.map((rule) => (
                <tr key={rule.id}>
                  <td>{rule.template_name}</td>
                  <td>{rule.file_type}</td>
                  <td>{rule.mode ?? "-"}</td>
                  <td>{rule.direction ?? "-"}</td>
                  <td>{rule.is_default ? "Y" : "N"}</td>
                  <td>{rule.is_active ? "Y" : "N"}</td>
                  <td>{rule.description ?? "-"}</td>
                  <td>
                    <div className="toolbar">
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => editParserTemplate(rule)}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => deactivateTemplate(rule.id)}
                        disabled={!rule.is_active}
                      >
                        Disable
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
        <h2>User / Role Master</h2>
        <div className="form-grid compact">
          <label className="field">
            <span>Username</span>
            <input
              value={userForm.username}
              onChange={(event) =>
                setUserForm((current) => ({ ...current, username: event.target.value }))
              }
            />
          </label>
          <label className="field">
            <span>Display Name</span>
            <input
              value={userForm.display_name}
              onChange={(event) =>
                setUserForm((current) => ({ ...current, display_name: event.target.value }))
              }
            />
          </label>
          <label className="field">
            <span>Email</span>
            <input
              value={userForm.email ?? ""}
              onChange={(event) =>
                setUserForm((current) => ({ ...current, email: event.target.value }))
              }
            />
          </label>
          <label className="field">
            <span>Role</span>
            <select
              value={userForm.role}
              onChange={(event) =>
                setUserForm((current) => ({
                  ...current,
                  role: event.target.value as User["role"],
                }))
              }
            >
              <option value="STAFF">STAFF</option>
              <option value="TEAM_MANAGER">TEAM_MANAGER</option>
              <option value="DIRECTOR">DIRECTOR</option>
              <option value="CEO">CEO</option>
              <option value="ADMIN">ADMIN</option>
            </select>
          </label>
          <label className="field">
            <span>Department</span>
            <input
              value={userForm.department ?? ""}
              onChange={(event) =>
                setUserForm((current) => ({ ...current, department: event.target.value }))
              }
            />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              type="password"
              placeholder={editingUserId ? "비우면 기존 비밀번호 유지" : "초기 비밀번호"}
              value={userForm.password ?? ""}
              onChange={(event) =>
                setUserForm((current) => ({ ...current, password: event.target.value }))
              }
            />
          </label>
          <label className="check-field">
            <input
              type="checkbox"
              checked={userForm.is_active}
              onChange={(event) =>
                setUserForm((current) => ({ ...current, is_active: event.target.checked }))
              }
            />
            <span>Active</span>
          </label>
        </div>
        <div className="toolbar form-actions">
          <button type="button" onClick={submitUser}>
            {editingUserId ? "Update User" : "Add User"}
          </button>
          <button type="button" className="secondary-button" onClick={resetUserForm}>
            Reset
          </button>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Username</th>
                <th>Display Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Department</th>
                <th>Active</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.username}</td>
                  <td>{user.display_name}</td>
                  <td>{user.email ?? "-"}</td>
                  <td>{user.role}</td>
                  <td>{user.department ?? "-"}</td>
                  <td>{user.is_active ? "Y" : "N"}</td>
                  <td>
                    <div className="toolbar">
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => editUser(user)}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => deactivateUserRow(user.id)}
                        disabled={!user.is_active}
                      >
                        Disable
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
