import { useEffect, useState } from "react";
import {
  ceoApproveWorkflow,
  directorApproveWorkflow,
  generateApprovalPdfReport,
  getCurrentRole,
  getCurrentUsername,
  getReportDownloadUrl,
  getWorkflowDetail,
  getWorkflows,
  rejectWorkflow,
  returnWorkflow,
  submitWorkflow,
  teamApproveWorkflow,
  type ApprovalReportFile,
  type WorkflowDetail,
  type WorkflowListItem,
} from "../api/client";
import { DecisionBadge } from "../components/DecisionBadge";
import { FindingsTable } from "../components/FindingsTable";
import { getErrorMessage } from "../error";
import { formatJPY, formatRate } from "../format";

const statuses = [
  "",
  "DRAFT",
  "SUBMITTED",
  "TEAM_APPROVED",
  "DIRECTOR_APPROVED",
  "CEO_APPROVED",
  "REJECTED",
  "RETURNED",
];

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    DRAFT: "상신 전",
    SUBMITTED: "팀장 승인 대기",
    TEAM_APPROVED: "본부장 승인 대기",
    DIRECTOR_APPROVED: "대표 승인 대기",
    CEO_APPROVED: "최종 승인",
    REJECTED: "반려",
    RETURNED: "보완요청",
  };
  return labels[status] ?? status;
}

function errorMessage(error: unknown, fallback: string) {
  const status = (error as { response?: { status?: number } }).response?.status;
  if (status === 403) return "권한이 없습니다.";
  return getErrorMessage(error, fallback);
}

export function WorkflowPage() {
  const [items, setItems] = useState<WorkflowListItem[]>([]);
  const [detail, setDetail] = useState<WorkflowDetail | null>(null);
  const [status, setStatus] = useState("");
  const [pic, setPic] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [comment, setComment] = useState("결재 요청드립니다.");
  const [username, setUsername] = useState(getCurrentUsername());
  const [latestPdf, setLatestPdf] = useState<ApprovalReportFile | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const role = getCurrentRole();

  function canAction(action: string, workflowStatus: string) {
    if (action === "submit") {
      return ["STAFF", "ADMIN"].includes(role) && ["DRAFT", "RETURNED"].includes(workflowStatus);
    }
    if (action === "team") {
      return ["TEAM_MANAGER", "ADMIN"].includes(role) && workflowStatus === "SUBMITTED";
    }
    if (action === "director") {
      return ["DIRECTOR", "ADMIN"].includes(role) && workflowStatus === "TEAM_APPROVED";
    }
    if (action === "ceo") {
      return ["CEO", "ADMIN"].includes(role) && workflowStatus === "DIRECTOR_APPROVED";
    }
    if (action === "reject") {
      return ["TEAM_MANAGER", "DIRECTOR", "CEO", "ADMIN"].includes(role) && workflowStatus !== "CEO_APPROVED";
    }
    if (action === "return") {
      return (
        ["TEAM_MANAGER", "DIRECTOR", "CEO", "ADMIN"].includes(role) &&
        ["SUBMITTED", "TEAM_APPROVED", "DIRECTOR_APPROVED"].includes(workflowStatus)
      );
    }
    return false;
  }

  async function loadWorkflows() {
    try {
      setError("");
      setItems(
        await getWorkflows({
          status: status || undefined,
          pic: pic || undefined,
          start_date: startDate || undefined,
          end_date: endDate || undefined,
        }),
      );
    } catch (error) {
      setError(errorMessage(error, "Workflow 목록 조회 실패"));
    }
  }

  useEffect(() => {
    loadWorkflows();
  }, []);

  useEffect(() => {
    function handleUserChange() {
      setUsername(getCurrentUsername());
    }
    window.addEventListener("lotos-user-change", handleUserChange);
    return () => window.removeEventListener("lotos-user-change", handleUserChange);
  }, []);

  async function selectWorkflow(id: number) {
    try {
      setError("");
      setDetail(await getWorkflowDetail(id));
    } catch (error) {
      const message = errorMessage(error, "Workflow 상세 조회 실패");
      setError(message);
      alert(message);
    }
  }

  async function runAction(action: string) {
    if (!detail) return;
    const workflowId = detail.workflow.workflow_id;
    try {
      setError("");
      if (action === "submit") {
        await submitWorkflow(workflowId, { request_comment: comment });
      }
      if (action === "team") {
        await teamApproveWorkflow(workflowId, { comment });
      }
      if (action === "director") {
        await directorApproveWorkflow(workflowId, { comment });
      }
      if (action === "ceo") {
        await ceoApproveWorkflow(workflowId, { comment });
      }
      if (action === "reject") {
        await rejectWorkflow(workflowId, { reject_reason: comment || "반려" });
      }
      if (action === "return") {
        await returnWorkflow(workflowId, { return_reason: comment || "보완요청" });
      }
      setMessage("Workflow 상태가 변경되었습니다.");
      await loadWorkflows();
      await selectWorkflow(workflowId);
    } catch (error) {
      const message = errorMessage(error, "Workflow 처리 실패");
      setError(message);
      alert(message);
    }
  }

  async function createPdf(reportType: "SUMMARY" | "DETAIL") {
    if (!detail) return;
    try {
      setError("");
      const created = await generateApprovalPdfReport(
        detail.approval_case.id,
        reportType,
      );
      setLatestPdf(created);
      downloadPdf(created);
    } catch (error) {
      const message = errorMessage(error, "PDF 생성 실패");
      setError(message);
      alert(message);
    }
  }

  function downloadPdf(file: ApprovalReportFile) {
    const anchor = document.createElement("a");
    anchor.href = getReportDownloadUrl(file.download_url);
    anchor.download = file.file_name;
    anchor.click();
  }

  return (
    <div className="stack">
      {error && <div className="error-box">{error}</div>}
      <section className="panel">
        <div className="section-heading">
          <h2>Approval Workflows</h2>
          <button type="button" onClick={loadWorkflows}>
            조회
          </button>
        </div>
        <div className="form-grid compact">
          <label className="field">
            <span>Status</span>
            <select value={status} onChange={(event) => setStatus(event.target.value)}>
              {statuses.map((item) => (
                <option key={item || "ALL"} value={item}>
                  {item ? statusLabel(item) : "ALL"}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>PIC</span>
            <input value={pic} onChange={(event) => setPic(event.target.value)} />
          </label>
          <label className="field">
            <span>Start Date</span>
            <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
          </label>
          <label className="field">
            <span>End Date</span>
            <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
          </label>
        </div>
        <div className="meta-line">Current user: {username} / Role: {role}</div>
        <div className="meta-line">{message}</div>
      </section>

      <section className="panel">
        <h2>Workflow 목록</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Workflow</th>
                <th>Approval</th>
                <th>Customer</th>
                <th>Code</th>
                <th className="number">GP</th>
                <th>AI Decision</th>
                <th>Workflow Status</th>
                <th>Requested By</th>
                <th>Created</th>
                <th>Submitted</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  key={item.workflow_id}
                  className="clickable-row"
                  onClick={() => selectWorkflow(item.workflow_id)}
                >
                  <td>{item.workflow_id}</td>
                  <td>{item.approval_case_id}</td>
                  <td>{item.customer_name}</td>
                  <td>{item.code}</td>
                  <td className="number">{formatJPY(item.gp_jpy)}</td>
                  <td>
                    <DecisionBadge decision={item.decision} />
                  </td>
                  <td>{statusLabel(item.current_status)}</td>
                  <td>{item.requested_by ?? "-"}</td>
                  <td>{item.created_at.slice(0, 10)}</td>
                  <td>{item.submitted_at?.slice(0, 10) ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {detail && (
        <section className="panel">
          <div className="section-heading">
            <h2>Workflow 상세 #{detail.workflow.workflow_id}</h2>
            <div className="toolbar">
              <button
                type="button"
                disabled={!canAction("submit", detail.workflow.current_status)}
                onClick={() => runAction("submit")}
              >
                결재상신
              </button>
              <button
                type="button"
                disabled={!canAction("team", detail.workflow.current_status)}
                onClick={() => runAction("team")}
              >
                팀장 승인
              </button>
              <button
                type="button"
                disabled={!canAction("director", detail.workflow.current_status)}
                onClick={() => runAction("director")}
              >
                본부장 승인
              </button>
              <button
                type="button"
                disabled={!canAction("ceo", detail.workflow.current_status)}
                onClick={() => runAction("ceo")}
              >
                대표 승인
              </button>
              <button
                type="button"
                className="secondary-button"
                disabled={!canAction("reject", detail.workflow.current_status)}
                onClick={() => runAction("reject")}
              >
                반려
              </button>
              <button
                type="button"
                className="secondary-button"
                disabled={!canAction("return", detail.workflow.current_status)}
                onClick={() => runAction("return")}
              >
                보완요청
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={() => createPdf("SUMMARY")}
              >
                Summary PDF
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={() => createPdf("DETAIL")}
              >
                Detail PDF
              </button>
            </div>
          </div>

          <div className="form-grid compact">
            <label className="field">
              <span>처리자</span>
              <input value={`${username} (${role})`} readOnly />
            </label>
            <label className="field">
              <span>Comment / Reason</span>
              <input value={comment} onChange={(event) => setComment(event.target.value)} />
            </label>
          </div>

          <div className="detail-grid">
            <div>AI 판정: <DecisionBadge decision={detail.approval_case.decision} /></div>
            <div>결재상태: {statusLabel(detail.workflow.current_status)}</div>
            <div>고객명: {detail.approval_case.customer_name}</div>
            <div>업무코드: {detail.approval_case.code}</div>
            <div>거래구분: {detail.approval_case.trade_type}</div>
            <div>담당자: {detail.approval_case.pic ?? "-"}</div>
            <div>GP: {formatJPY(detail.approval_case.gp_jpy)}</div>
            <div>GP율: {formatRate(detail.approval_case.gp_rate)}</div>
          </div>

          <p className="comment">{detail.approval_case.executive_comment}</p>
          {latestPdf && (
            <p className="meta-line">
              PDF: {latestPdf.file_name}{" "}
              <button
                type="button"
                className="secondary-button"
                onClick={() => downloadPdf(latestPdf)}
              >
                Download
              </button>
            </p>
          )}
          <FindingsTable findings={detail.findings} />
        </section>
      )}
    </div>
  );
}
