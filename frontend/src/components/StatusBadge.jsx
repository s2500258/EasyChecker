// Color-coded severity badge used across event and alert views.
export default function StatusBadge({ value }) {
  const tone = String(value || "").toLowerCase();
  return <span className={`status-badge ${tone}`.trim()}>{value || "N/A"}</span>;
}
