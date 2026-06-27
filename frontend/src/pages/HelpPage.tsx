import { getDocumentationDownloadUrl } from "../api/client";

const roleSteps = [
  {
    role: "담당자 STAFF",
    steps: "Upload -> Map to Case -> 수동수정 -> Analyze -> Analyze & Save -> 결재상신",
  },
  {
    role: "팀장 TEAM_MANAGER",
    steps: "SUBMITTED 확인 -> AI Decision/Findings 확인 -> 승인/보완요청/반려",
  },
  {
    role: "본부장 DIRECTOR",
    steps: "TEAM_APPROVED 확인 -> 저마진/대표검토 우선 확인 -> 승인/보완요청/반려",
  },
  {
    role: "대표 CEO",
    steps: "DIRECTOR_APPROVED 확인 -> Summary PDF 확인 -> Dashboard 확인 -> 최종승인",
  },
  {
    role: "관리자 ADMIN",
    steps: "User/Master 관리 -> Backup -> Audit Log -> Parser Validation -> System Status",
  },
];

const decisions = [
  ["APPROVED", "기준 충족"],
  ["CONDITIONAL_APPROVED", "조건부승인, WARN 확인 필요"],
  ["CEO_REVIEW", "대표검토 필요"],
  ["REJECTED", "반려 권고"],
];

const workflowStatuses = [
  ["DRAFT", "상신 전"],
  ["SUBMITTED", "담당자 상신 완료"],
  ["TEAM_APPROVED", "팀장 승인 완료"],
  ["DIRECTOR_APPROVED", "본부장 승인 완료"],
  ["CEO_APPROVED", "대표 최종 승인"],
  ["REJECTED", "반려"],
  ["RETURNED", "보완요청"],
];

const documents = [
  ["사용자 매뉴얼 다운로드", "/api/docs/user-manual"],
  ["관리자 매뉴얼 다운로드", "/api/docs/admin-manual"],
  ["교육자료 다운로드", "/api/docs/training-guide"],
];

export function HelpPage() {
  return (
    <div className="stack">
      <section className="panel">
        <div className="section-heading">
          <h2>Help</h2>
          <div className="toolbar">
            {documents.map(([label, path]) => (
              <a
                key={path}
                className="button-link"
                href={getDocumentationDownloadUrl(path)}
                target="_blank"
                rel="noreferrer"
              >
                {label}
              </a>
            ))}
          </div>
        </div>
        <p className="comment">
          LOTOS AI Profit Approval System은 Profit Sheet 업로드, AI 결재심사,
          Workflow 승인, Dashboard, PDF/Excel 출력, ERP JSON Export를 하나의
          업무 흐름으로 연결합니다.
        </p>
      </section>

      <section className="panel">
        <h2>Role별 업무 절차</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Role</th>
                <th>업무 절차</th>
              </tr>
            </thead>
            <tbody>
              {roleSteps.map((row) => (
                <tr key={row.role}>
                  <td>{row.role}</td>
                  <td>{row.steps}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="two-column">
        <div className="panel">
          <h2>AI Decision</h2>
          <table>
            <thead>
              <tr>
                <th>Decision</th>
                <th>의미</th>
              </tr>
            </thead>
            <tbody>
              {decisions.map(([decision, description]) => (
                <tr key={decision}>
                  <td>{decision}</td>
                  <td>{description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="panel">
          <h2>Workflow Status</h2>
          <table>
            <thead>
              <tr>
                <th>Status</th>
                <th>의미</th>
              </tr>
            </thead>
            <tbody>
              {workflowStatuses.map(([status, description]) => (
                <tr key={status}>
                  <td>{status}</td>
                  <td>{description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>문의처</h2>
        <p className="comment">
          운영 문의처는 사내 시스템 담당자 또는 관리자에게 확인하십시오.
        </p>
      </section>
    </div>
  );
}
