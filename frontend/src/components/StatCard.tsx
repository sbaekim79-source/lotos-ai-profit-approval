type StatCardProps = {
  label: string;
  value: string | number;
};

export function StatCard({ label, value }: StatCardProps) {
  return (
    <section className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </section>
  );
}
