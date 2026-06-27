const decisionLabels: Record<string, string> = {
  APPROVED: "승인",
  CONDITIONAL_APPROVED: "조건부승인",
  CEO_REVIEW: "대표검토",
  REJECTED: "반려",
};

export function DecisionBadge({ decision }: { decision: string }) {
  const className = `decision-badge ${decision.toLowerCase()}`;
  return <span className={className}>{decisionLabels[decision] ?? decision}</span>;
}
