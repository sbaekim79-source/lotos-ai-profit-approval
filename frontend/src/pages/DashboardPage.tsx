import { useEffect, useMemo, useState } from "react";
import {
  downloadDashboardExcel,
  downloadProductivityExcel,
  getDashboardSummary,
  getLowMarginCases,
  getMonthlyPerformance,
  getProductivityMonthly,
  type DashboardSummary,
  type MonthlyPerformanceItem,
  type ProductivityMonthlyItem,
} from "../api/client";
import { formatJPY, formatRate } from "../format";
import { StatCard } from "../components/StatCard";
import { DecisionBadge } from "../components/DecisionBadge";
import { getErrorMessage } from "../error";
import { saveBlob, todayStamp } from "../download";

type Tab = "summary" | "monthly" | "productivity" | "low-margin";
type Preset = "current" | "previous" | "quarter" | "custom";

type Filters = {
  start_date: string;
  end_date: string;
  work_month: string;
  pic: string;
  trade_type: string;
  code: string;
  partner_name: string;
  customer_name: string;
};

type LowMarginRow = Awaited<ReturnType<typeof getLowMarginCases>>[number];

function toQuery(filters: Filters) {
  return Object.fromEntries(
    Object.entries(filters).filter(([, value]) => value.trim() !== ""),
  );
}

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function monthIso(date: Date) {
  return date.toISOString().slice(0, 7);
}

function applyPreset(preset: Preset): Partial<Filters> {
  const now = new Date();
  if (preset === "current") {
    return { start_date: "", end_date: "", work_month: monthIso(now) };
  }
  if (preset === "previous") {
    const previous = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    return { start_date: "", end_date: "", work_month: monthIso(previous) };
  }
  if (preset === "quarter") {
    const quarterStartMonth = Math.floor(now.getMonth() / 3) * 3;
    const start = new Date(now.getFullYear(), quarterStartMonth, 1);
    return { start_date: start.toISOString().slice(0, 10), end_date: todayIso(), work_month: "" };
  }
  return {};
}

function formatDate(value: string) {
  return value.slice(0, 10);
}

export function DashboardPage() {
  const [tab, setTab] = useState<Tab>("summary");
  const [preset, setPreset] = useState<Preset>("current");
  const [filters, setFilters] = useState<Filters>({
    start_date: "",
    end_date: "",
    work_month: monthIso(new Date()),
    pic: "",
    trade_type: "",
    code: "",
    partner_name: "",
    customer_name: "",
  });
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [monthly, setMonthly] = useState<MonthlyPerformanceItem[]>([]);
  const [productivity, setProductivity] = useState<ProductivityMonthlyItem[]>([]);
  const [lowMargin, setLowMargin] = useState<LowMarginRow[]>([]);
  const [error, setError] = useState("");

  const query = useMemo(() => toQuery(filters), [filters]);

  async function loadDashboard() {
    try {
      setError("");
      const [summaryData, lowMarginData] = await Promise.all([
        getDashboardSummary(query),
        getLowMarginCases(query),
      ]);
      setSummary(summaryData);
      setLowMargin(lowMarginData);

      const startMonth = filters.start_date ? filters.start_date.slice(0, 7) : "";
      const endMonth = filters.end_date ? filters.end_date.slice(0, 7) : "";
      const monthParams = {
        start_month: startMonth || filters.work_month || undefined,
        end_month: endMonth || filters.work_month || undefined,
        pic: filters.pic || undefined,
        trade_type: filters.trade_type || undefined,
        code: filters.code || undefined,
      };
      const [monthlyData, productivityData] = await Promise.all([
        getMonthlyPerformance(monthParams),
        getProductivityMonthly({
          start_month: monthParams.start_month,
          end_month: monthParams.end_month,
          pic: filters.pic || undefined,
        }),
      ]);
      setMonthly(monthlyData);
      setProductivity(productivityData);
    } catch (error) {
      setError(getErrorMessage(error, "Dashboard 조회 실패"));
    }
  }

  function updateFilter(name: keyof Filters, value: string) {
    setFilters((current) => ({ ...current, [name]: value }));
  }

  function changePreset(value: Preset) {
    setPreset(value);
    setFilters((current) => ({ ...current, ...applyPreset(value) }));
  }

  function resetFilters() {
    setPreset("current");
    setFilters({
      start_date: "",
      end_date: "",
      work_month: monthIso(new Date()),
      pic: "",
      trade_type: "",
      code: "",
      partner_name: "",
      customer_name: "",
    });
  }

  async function downloadDashboard() {
    try {
      setError("");
      const blob = await downloadDashboardExcel(query);
      saveBlob(blob, `dashboard_${todayStamp()}.xlsx`);
    } catch (error) {
      const message = getErrorMessage(error, "Dashboard Excel 다운로드 실패");
      setError(message);
      alert(message);
    }
  }

  async function downloadProductivity() {
    try {
      setError("");
      const startMonth = filters.start_date ? filters.start_date.slice(0, 7) : "";
      const endMonth = filters.end_date ? filters.end_date.slice(0, 7) : "";
      const blob = await downloadProductivityExcel({
        start_month: startMonth || filters.work_month || undefined,
        end_month: endMonth || filters.work_month || undefined,
        pic: filters.pic || undefined,
      });
      saveBlob(blob, `productivity_${todayStamp()}.xlsx`);
    } catch (error) {
      const message = getErrorMessage(error, "Productivity Excel 다운로드 실패");
      setError(message);
      alert(message);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  if (!summary && !error) return <div className="loading">Loading dashboard...</div>;

  return (
    <div className="stack">
      {error && <div className="error-box">{error}</div>}

      <section className="panel">
        <div className="section-heading">
          <h2>현재 월 실적</h2>
          <div className="toolbar">
            <button type="button" onClick={downloadDashboard}>
              Dashboard Excel
            </button>
            <button type="button" onClick={downloadProductivity}>
              Productivity Excel
            </button>
            <button type="button" onClick={loadDashboard}>
              조회
            </button>
          </div>
        </div>
        <div className="meta-line">
          기간: {summary?.period_label ?? "-"} ({summary?.start_date ?? "-"} ~ {summary?.end_date ?? "-"})
        </div>
        <div className="form-grid">
          <label className="field">
            <span>기간 선택</span>
            <select value={preset} onChange={(event) => changePreset(event.target.value as Preset)}>
              <option value="current">현재 월</option>
              <option value="previous">전월</option>
              <option value="quarter">이번 분기</option>
              <option value="custom">사용자 지정</option>
            </select>
          </label>
          <label className="field">
            <span>Start Date</span>
            <input type="date" value={filters.start_date} onChange={(event) => updateFilter("start_date", event.target.value)} />
          </label>
          <label className="field">
            <span>End Date</span>
            <input type="date" value={filters.end_date} onChange={(event) => updateFilter("end_date", event.target.value)} />
          </label>
          <label className="field">
            <span>Work Month</span>
            <input type="month" value={filters.work_month} onChange={(event) => updateFilter("work_month", event.target.value)} />
          </label>
          <label className="field">
            <span>담당자</span>
            <input value={filters.pic} onChange={(event) => updateFilter("pic", event.target.value)} />
          </label>
          <label className="field">
            <span>거래구분</span>
            <select value={filters.trade_type} onChange={(event) => updateFilter("trade_type", event.target.value)}>
              <option value="">ALL</option>
              <option value="PARTNER">PARTNER</option>
              <option value="SHIPPER">SHIPPER</option>
              <option value="FORWARDER">FORWARDER</option>
            </select>
          </label>
          <label className="field">
            <span>업무코드</span>
            <input value={filters.code} onChange={(event) => updateFilter("code", event.target.value)} />
          </label>
          <label className="field">
            <span>파트너</span>
            <input value={filters.partner_name} onChange={(event) => updateFilter("partner_name", event.target.value)} />
          </label>
          <label className="field">
            <span>고객명</span>
            <input value={filters.customer_name} onChange={(event) => updateFilter("customer_name", event.target.value)} />
          </label>
        </div>
        <div className="toolbar form-actions">
          <button type="button" onClick={loadDashboard}>조회</button>
          <button type="button" className="secondary-button" onClick={resetFilters}>초기화</button>
        </div>
      </section>

      <div className="toolbar">
        <button type="button" className={tab === "summary" ? "" : "secondary-button"} onClick={() => setTab("summary")}>Summary</button>
        <button type="button" className={tab === "monthly" ? "" : "secondary-button"} onClick={() => setTab("monthly")}>Monthly Performance</button>
        <button type="button" className={tab === "productivity" ? "" : "secondary-button"} onClick={() => setTab("productivity")}>Productivity</button>
        <button type="button" className={tab === "low-margin" ? "" : "secondary-button"} onClick={() => setTab("low-margin")}>Low Margin</button>
      </div>

      {summary && tab === "summary" && (
        <>
          <section className="stat-grid">
            <StatCard label="총 결재건수" value={summary.total_cases} />
            <StatCard label="총매출" value={formatJPY(summary.total_revenue_jpy)} />
            <StatCard label="총원가" value={formatJPY(summary.total_expense_jpy)} />
            <StatCard label="총 GP" value={formatJPY(summary.total_gp_jpy)} />
            <StatCard label="평균 GP율" value={formatRate(summary.average_gp_rate)} />
            <StatCard label="승인" value={summary.decision_counts.APPROVED ?? 0} />
            <StatCard label="조건부승인" value={summary.decision_counts.CONDITIONAL_APPROVED ?? 0} />
            <StatCard label="대표검토" value={summary.decision_counts.CEO_REVIEW ?? 0} />
            <StatCard label="반려" value={summary.decision_counts.REJECTED ?? 0} />
          </section>

          <section className="panel">
            <h2>담당자별 생산성</h2>
            <table>
              <thead><tr><th>담당자</th><th className="number">Point</th><th className="number">건수</th></tr></thead>
              <tbody>
                {summary.productivity_by_pic.map((row) => (
                  <tr key={row.pic}><td>{row.pic}</td><td className="number">{row.total_point}</td><td className="number">{row.case_count}</td></tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="two-column">
            <SummaryTable title="고객별 GP" nameLabel="고객명" rows={summary.gp_by_customer} nameKey="customer_name" />
            <SummaryTable title="Partner Summary" nameLabel="Partner" rows={summary.partner_summary} nameKey="partner_name" />
          </section>
        </>
      )}

      {tab === "monthly" && (
        <section className="panel">
          <h2>Monthly Performance</h2>
          <table>
            <thead>
              <tr><th>월</th><th className="number">건수</th><th className="number">매출</th><th className="number">원가</th><th className="number">GP</th><th className="number">GP율</th><th className="number">승인</th><th className="number">조건부</th><th className="number">대표검토</th><th className="number">반려</th></tr>
            </thead>
            <tbody>
              {monthly.map((row) => (
                <tr key={row.work_month}>
                  <td>{row.work_month}</td>
                  <td className="number">{row.case_count ?? row.total_cases}</td>
                  <td className="number">{formatJPY(row.total_revenue_jpy)}</td>
                  <td className="number">{formatJPY(row.total_expense_jpy)}</td>
                  <td className="number">{formatJPY(row.total_gp_jpy)}</td>
                  <td className="number">{formatRate(row.average_gp_rate)}</td>
                  <td className="number">{row.approved_count}</td>
                  <td className="number">{row.conditional_count ?? row.conditional_approved_count}</td>
                  <td className="number">{row.ceo_review_count}</td>
                  <td className="number">{row.rejected_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === "productivity" && (
        <section className="panel">
          <h2>Productivity</h2>
          <table>
            <thead><tr><th>월</th><th>담당자</th><th className="number">Point</th><th className="number">건수</th><th>등급</th></tr></thead>
            <tbody>
              {productivity.map((row) => (
                <tr key={`${row.work_month}-${row.pic}`}><td>{row.work_month}</td><td>{row.pic}</td><td className="number">{row.total_point}</td><td className="number">{row.case_count}</td><td>{row.grade}</td></tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === "low-margin" && (
        <section className="panel">
          <h2>Low Margin</h2>
          <table>
            <thead><tr><th>ID</th><th>고객명</th><th>파트너</th><th>거래구분</th><th>코드</th><th className="number">GP</th><th className="number">실GP율</th><th>Decision</th><th>대표의견</th><th>생성일</th></tr></thead>
            <tbody>
              {lowMargin.map((row) => (
                <tr key={row.id}>
                  <td>{row.id}</td><td>{row.customer_name}</td><td>{row.partner_name ?? "-"}</td><td>{row.trade_type}</td><td>{row.code}</td>
                  <td className="number">{formatJPY(row.gp_jpy)}</td><td className="number">{formatRate(row.net_gp_rate_ex_tax)}</td>
                  <td><DecisionBadge decision={row.decision} /></td><td>{row.executive_comment}</td><td>{formatDate(row.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}

function SummaryTable({
  title,
  nameLabel,
  rows,
  nameKey,
}: {
  title: string;
  nameLabel: string;
  rows: any[];
  nameKey: "customer_name" | "partner_name";
}) {
  return (
    <div className="panel">
      <h2>{title}</h2>
      <table>
        <thead><tr><th>{nameLabel}</th><th className="number">건수</th><th className="number">매출</th><th className="number">GP</th><th className="number">GP율</th></tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row[nameKey]}>
              <td>{row[nameKey]}</td><td className="number">{row.case_count}</td><td className="number">{formatJPY(row.total_revenue_jpy)}</td><td className="number">{formatJPY(row.total_gp_jpy)}</td><td className="number">{formatRate(row.average_gp_rate)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
