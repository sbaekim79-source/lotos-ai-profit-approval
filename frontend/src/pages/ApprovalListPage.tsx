import { useEffect, useState } from "react";
import { downloadApprovalsExcel, getApprovals, type ApprovalListItem } from "../api/client";
import { DecisionBadge } from "../components/DecisionBadge";
import { formatJPY, formatRate } from "../format";
import { ApprovalDetailPage } from "./ApprovalDetailPage";
import { getErrorMessage } from "../error";
import { saveBlob, todayStamp } from "../download";

export function ApprovalListPage() {
  const [items, setItems] = useState<ApprovalListItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [error, setError] = useState("");

  async function loadApprovals() {
    try {
      setError("");
      setItems(await getApprovals());
    } catch (error) {
      setError(getErrorMessage(error, "결재 이력 조회 실패"));
    }
  }

  async function downloadExcel() {
    try {
      setError("");
      const blob = await downloadApprovalsExcel();
      saveBlob(blob, `approvals_${todayStamp()}.xlsx`);
    } catch (error) {
      const message = getErrorMessage(error, "결재이력 Excel 다운로드 실패");
      setError(message);
      alert(message);
    }
  }

  useEffect(() => {
    loadApprovals();
  }, []);

  return (
    <div className="stack">
      {error && <div className="error-box">{error}</div>}
      <section className="panel">
        <div className="section-heading">
          <h2>Approval Results</h2>
          <div className="toolbar">
            <button type="button" onClick={downloadExcel}>
              Excel 다운로드
            </button>
            <button type="button" onClick={loadApprovals}>
              Refresh
            </button>
          </div>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>고객명</th>
                <th>거래구분</th>
                <th>Partner</th>
                <th>담당자</th>
                <th>코드</th>
                <th className="number">Point</th>
                <th className="number">매출</th>
                <th className="number">GP</th>
                <th className="number">GP율</th>
                <th>Decision</th>
                <th>created_at</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  key={item.id}
                  onClick={() => setSelectedId(item.id)}
                  className="clickable-row"
                >
                  <td>{item.id}</td>
                  <td>{item.customer_name}</td>
                  <td>{item.trade_type}</td>
                  <td>{item.partner_name ?? "-"}</td>
                  <td>{item.pic ?? "-"}</td>
                  <td>{item.code}</td>
                  <td className="number">{item.point}</td>
                  <td className="number">{formatJPY(item.total_revenue_jpy)}</td>
                  <td className="number">{formatJPY(item.gp_jpy)}</td>
                  <td className="number">{formatRate(item.gp_rate)}</td>
                  <td>
                    <DecisionBadge decision={item.decision} />
                  </td>
                  <td>{new Date(item.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {selectedId && <ApprovalDetailPage id={selectedId} />}
    </div>
  );
}
