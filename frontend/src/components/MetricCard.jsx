export default function MetricCard({ label, value, accent }) {
  return (
    <article className={`metric-card ${accent || ""}`.trim()}>
      <p>{label}</p>
      <strong>{value}</strong>
    </article>
  );
}
