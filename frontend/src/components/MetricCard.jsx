// Small summary card used on the dashboard metrics row.
export default function MetricCard({ label, value, accent }) {
  return (
    <article className={`metric-card ${accent || ""}`.trim()}>
      <p>{label}</p>
      <strong>{value}</strong>
    </article>
  );
}
