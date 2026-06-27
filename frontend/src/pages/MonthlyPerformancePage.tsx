import { useEffect, useMemo, useState } from "react";
import {
  getDashboardProductivity,
  getDashboardSummary,
  getMonthlyPerformance,
  type DashboardSummary,
  type MonthlyPerformanceItem,
  type ProductivityMonthlyItem,
} from "../api/client";
import { formatJPY, formatRate } from "../format";
import { getErrorMessage } from "../error";
import { StatCard } from "../components/StatCard";

function currentMonth() {
  return new Date().toISOString().slice(0, 7);
}

function monthStart(month: string) {
  return `${month}-01`;
}

function monthEnd(month: string) {
  const [year, monthValue] = month.split("-").map(Number);
  const end = new Date(year, monthValue, 0);
  return end.toISOString().slice(0, 10);
}

export function MonthlyPerformancePage() {
  const [startMonth, setStartMonth] = useState(currentMonth());
  const [endMonth, setEndMonth] = useState(currentMonth());
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [monthlyRows, setMonthlyRows] = useState<MonthlyPerformanceItem[]>([]);
  const [productivityRows, setProductivityRows] = useState<ProductivityMonthlyItem[]>([]);
  const [error, setError] = useState("");

  const dateRange = useMemo(
    () => ({
      start_date: monthStart(startMonth),
      end_date: monthEnd(endMonth),
    }),
    [startMonth, endMonth],
  );

  async function load() {
    try {
      setError("");
      const [summaryData, monthlyData, productivityData] = await Promise.all([
        getDashboardSummary(dateRange),
        getMonthlyPerformance({ start_month: startMonth, end_month: endMonth }),
        getDashboardProductivity({ start_month: startMonth, end_month: endMonth }),
      ]);
      setSummary(summaryData);
      setMonthlyRows(monthlyData);
      setProductivityRows(productivityData);
    } catch (error) {
      setError(getErrorMessage(error, "월별 실적 조회 실패"));
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="stack">
      {error && <div className="error-box">{error}</div>}
      <section className="panel">
        <div className="section-heading">
          <h2>월별 실적</h2>
          <button type="button" onClick={load}>
            조회
          </button>
        </div>
        <div className="form-grid compact">
          <label className="field">
            <span>시작 월</span>
            <input
              type="month"
              value={startMonth}
              onChange={(event) => setStartMonth(event.target.value)}
            />
          </label>
          <label className="field">
            <span>종료 월</span>
            <input
              type="month"
              value={endMonth}
              onChange={(event) => setEndMonth(event.target.value)}
            />
          </label>
        </div>
      </section>

      {summary && (
        <section className="stat-grid">
          <StatCard label="기간 결재건수" value={summary.total_cases} />
          <StatCard label="기간 매출" value={formatJPY(summary.total_revenue_jpy)} />
          <StatCard label="기간 원가" value={formatJPY(summary.total_expense_jpy)} />
          <StatCard label="기간 GP" value={formatJPY(summary.total_gp_jpy)} />
          <StatCard label="평균 GP율" value={formatRate(summary.average_gp_rate)} />
          <StatCard label="승인" value={summary.decision_counts.APPROVED ?? 0} />
          <StatCard
            label="조건부승인"
            value={summary.decision_counts.CONDITIONAL_APPROVED ?? 0}
          />
          <StatCard label="대표검토" value={summary.decision_counts.CEO_REVIEW ?? 0} />
          <StatCard label="반려" value={summary.decision_counts.REJECTED ?? 0} />
        </section>
      )}

      <section className="panel">
        <h2>월별 수익성</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>월</th>
                <th className="number">건수</th>
                <th className="number">매출</th>
                <th className="number">원가</th>
                <th className="number">GP</th>
                <th className="number">GP율</th>
                <th className="number">승인</th>
                <th className="number">조건부</th>
                <th className="number">대표검토</th>
                <th className="number">반려</th>
              </tr>
            </thead>
            <tbody>
              {monthlyRows.map((row) => (
                <tr key={row.work_month}>
                  <td>{row.work_month}</td>
                  <td className="number">{row.total_cases}</td>
                  <td className="number">{formatJPY(row.total_revenue_jpy)}</td>
                  <td className="number">{formatJPY(row.total_expense_jpy)}</td>
                  <td className="number">{formatJPY(row.total_gp_jpy)}</td>
                  <td className="number">{formatRate(row.average_gp_rate)}</td>
                  <td className="number">{row.approved_count}</td>
                  <td className="number">{row.conditional_approved_count}</td>
                  <td className="number">{row.ceo_review_count}</td>
                  <td className="number">{row.rejected_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>월별 담당자 생산성</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>월</th>
                <th>담당자</th>
                <th className="number">Point</th>
                <th className="number">건수</th>
                <th>등급</th>
              </tr>
            </thead>
            <tbody>
              {productivityRows.map((row) => (
                <tr key={`${row.work_month}-${row.pic}`}>
                  <td>{row.work_month}</td>
                  <td>{row.pic}</td>
                  <td className="number">{row.total_point}</td>
                  <td className="number">{row.case_count}</td>
                  <td>{row.grade}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
