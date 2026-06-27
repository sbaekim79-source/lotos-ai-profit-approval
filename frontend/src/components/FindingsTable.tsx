import type { Finding } from "../api/client";
import { formatJPY } from "../format";

export function FindingsTable({ findings }: { findings: Finding[] }) {
  if (!findings?.length) {
    return <div className="empty-state">Findings 없음</div>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>구분</th>
          <th>상태</th>
          <th>내용</th>
          <th className="number">금액</th>
        </tr>
      </thead>
      <tbody>
        {findings.map((finding, index) => (
          <tr key={`${finding.category}-${index}`}>
            <td>{finding.category}</td>
            <td>{finding.status}</td>
            <td>{finding.message}</td>
            <td className="number">
              {finding.amount_jpy === null ? "-" : formatJPY(finding.amount_jpy)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
