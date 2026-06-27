import { useEffect, useState } from "react";
import {
  downloadIntegrationFile,
  exportApprovalIntegration,
  generateApprovalPdfReport,
  getApprovalDetail,
  getApprovalIntegrationPayload,
  getApprovalReport,
  getApprovalReportFiles,
  getCurrentRole,
  getReportDownloadUrl,
  getWorkflowDetail,
  getWorkflows,
  submitWorkflow,
  type ApprovalDetail,
  type ApprovalReportFile,
  type WorkflowDetail,
} from "../api/client";
import { DecisionBadge } from "../components/DecisionBadge";
import { FindingsTable } from "../components/FindingsTable";
import { getErrorMessage } from "../error";
import { formatJPY, formatRate } from "../format";
import { saveBlob } from "../download";

function workflowStatusLabel(status: string) {
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

export function ApprovalDetailPage({ id }: { id: number }) {
  const [detail, setDetail] = useState<ApprovalDetail | null>(null);
  const [workflow, setWorkflow] = useState<WorkflowDetail | null>(null);
  const [report, setReport] = useState("");
  const [integrationPayload, setIntegrationPayload] = useState("");
  const [pdfFiles, setPdfFiles] = useState<ApprovalReportFile[]>([]);
  const [error, setError] = useState("");
  const canUseIntegration = ["DIRECTOR", "CEO", "ADMIN"].includes(getCurrentRole());

  async function loadWorkflow() {
    const workflows = await getWorkflows();
    const item = workflows.find((workflow) => workflow.approval_case_id === id);
    setWorkflow(item ? await getWorkflowDetail(item.workflow_id) : null);
  }

  async function loadPdfFiles() {
    setPdfFiles(await getApprovalReportFiles(id));
  }

  useEffect(() => {
    getApprovalDetail(id)
      .then((data) => {
        setDetail(data);
        setError("");
      })
      .catch((error) => setError(getErrorMessage(error, "결재 상세 조회 실패")));
    loadWorkflow().catch(() => setWorkflow(null));
    loadPdfFiles().catch(() => setPdfFiles([]));
    setReport("");
    setIntegrationPayload("");
  }, [id]);

  if (error) return <div className="error-box">{error}</div>;
  if (!detail) return <div className="loading">Loading approval detail...</div>;

  async function showReport() {
    try {
      setError("");
      const reportText = await getApprovalReport(id);
      setReport(reportText);
    } catch (error) {
      const message = getErrorMessage(error, "결재심사서 조회 실패");
      setError(message);
      alert(message);
    }
  }

  async function downloadReport() {
    try {
      setError("");
      const reportText = report || (await getApprovalReport(id));
      const blob = new Blob([reportText], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `approval_report_${id}.md`;
      anchor.click();
      URL.revokeObjectURL(url);
      setReport(reportText);
    } catch (error) {
      const message = getErrorMessage(error, "Markdown 다운로드 실패");
      setError(message);
      alert(message);
    }
  }

  async function submitApprovalWorkflow() {
    if (!workflow || !detail) return;
    try {
      setError("");
      await submitWorkflow(workflow.workflow.workflow_id, {
        request_comment: "결재 요청드립니다.",
      });
      await loadWorkflow();
    } catch (error) {
      const message = getErrorMessage(error, "결재상신 실패");
      setError(message);
      alert(message);
    }
  }

  async function createPdf(reportType: "SUMMARY" | "DETAIL") {
    try {
      setError("");
      const created = await generateApprovalPdfReport(id, reportType);
      await loadPdfFiles();
      downloadPdf(created);
    } catch (error) {
      const status = (error as { response?: { status?: number } }).response?.status;
      const message = status === 403 ? "권한이 없습니다." : getErrorMessage(error, "PDF 생성 실패");
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

  async function showErpPayload() {
    try {
      setError("");
      const payload = await getApprovalIntegrationPayload(id);
      setIntegrationPayload(JSON.stringify(payload, null, 2));
    } catch (error) {
      const status = (error as { response?: { status?: number } }).response?.status;
      const message = status === 403 ? "권한이 없습니다." : getErrorMessage(error, "ERP Payload 조회 실패");
      setError(message);
      alert(message);
    }
  }

  async function exportErpJson() {
    try {
      setError("");
      const result = await exportApprovalIntegration(id, {
        integration_name: "ERP",
        export_format: "JSON",
      });
      if (result.download_url) {
        const blob = await downloadIntegrationFile(result.download_url);
        saveBlob(blob, result.file_name ?? `approval_${id}.json`);
      } else {
        alert(`Integration export status: ${result.status}`);
      }
    } catch (error) {
      const status = (error as { response?: { status?: number } }).response?.status;
      const message = status === 403 ? "권한이 없습니다." : getErrorMessage(error, "ERP JSON Export 실패");
      setError(message);
      alert(message);
    }
  }

  return (
    <div className="stack">
      <section className="panel">
        <div className="section-heading">
          <h2>Approval Detail #{detail.id}</h2>
          <div className="toolbar">
            <button type="button" onClick={showReport}>
              결재심사서 보기
            </button>
            <button type="button" onClick={downloadReport}>
              Markdown 다운로드
            </button>
            <button type="button" onClick={() => createPdf("SUMMARY")}>
              Summary PDF
            </button>
            <button type="button" onClick={() => createPdf("DETAIL")}>
              Detail PDF
            </button>
            {canUseIntegration && (
              <>
                <button type="button" onClick={showErpPayload}>
                  ERP Payload 보기
                </button>
                <button type="button" onClick={exportErpJson}>
                  ERP JSON Export
                </button>
              </>
            )}
            <button
              type="button"
              disabled={!workflow || !["DRAFT", "RETURNED"].includes(workflow.workflow.current_status)}
              onClick={submitApprovalWorkflow}
            >
              결재상신
            </button>
          </div>
        </div>
        <div className="detail-grid">
          <div>고객명: {detail.customer_name}</div>
          <div>거래구분: {detail.trade_type}</div>
          <div>Partner: {detail.partner_name ?? "-"}</div>
          <div>담당자: {detail.pic ?? "-"}</div>
          <div>Mode: {detail.mode}</div>
          <div>Direction: {detail.direction}</div>
          <div>POL: {detail.pol ?? "-"}</div>
          <div>POD: {detail.pod ?? "-"}</div>
          <div>Code: {detail.code}</div>
          <div>
            AI 판정: <DecisionBadge decision={detail.decision} />
          </div>
          <div>
            결재상태:{" "}
            {workflow ? workflowStatusLabel(workflow.workflow.current_status) : "-"}
          </div>
        </div>
        <div className="result-grid">
          <div>매출: {formatJPY(detail.total_revenue_jpy)}</div>
          <div>원가: {formatJPY(detail.total_expense_jpy)}</div>
          <div>GP: {formatJPY(detail.gp_jpy)}</div>
          <div>GP율: {formatRate(detail.gp_rate)}</div>
          <div>실GP율: {formatRate(detail.net_gp_rate_ex_tax)}</div>
          <div>Minimum GP: {formatJPY(detail.minimum_gp_jpy)}</div>
        </div>
        <p className="comment">{detail.executive_comment}</p>
        <FindingsTable findings={detail.findings} />
      </section>

      {pdfFiles.length > 0 && (
        <section className="panel">
          <h2>PDF Reports</h2>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>File</th>
                  <th>Created By</th>
                  <th>Created At</th>
                  <th>Download</th>
                </tr>
              </thead>
              <tbody>
                {pdfFiles.map((file) => (
                  <tr key={file.report_file_id}>
                    <td>{file.report_type}</td>
                    <td>{file.file_name}</td>
                    <td>{file.created_by ?? "-"}</td>
                    <td>{file.created_at?.slice(0, 19).replace("T", " ") ?? "-"}</td>
                    <td>
                      <button
                        type="button"
                        className="secondary-button"
                        onClick={() => downloadPdf(file)}
                      >
                        PDF Download
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {report && (
        <section className="panel">
          <h2>대표이사 결재심사서</h2>
          <pre className="report-preview">{report}</pre>
        </section>
      )}

      {integrationPayload && (
        <section className="panel">
          <h2>ERP Payload</h2>
          <pre className="report-preview">{integrationPayload}</pre>
        </section>
      )}
    </div>
  );
}
