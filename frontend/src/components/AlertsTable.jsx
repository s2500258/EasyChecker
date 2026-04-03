import StatusBadge from "./StatusBadge";
import { formatDateTime, shortenText } from "../utils/formatters";

// Tabular view of generated backend alerts.
export default function AlertsTable({ alerts, sort, onSort, t }) {
  function renderSortableHeader(label, key) {
    const isActive = sort.key === key;
    const direction = isActive ? sort.direction : "";

    return (
      <th>
        <button
          className={isActive ? "table-sort active" : "table-sort"}
          onClick={() => onSort(key)}
          type="button"
        >
          {label}
          <span className="table-sort-indicator">
            {direction === "asc" ? "▲" : direction === "desc" ? "▼" : "↕"}
          </span>
        </button>
      </th>
    );
  }

  return (
    <div className="table-shell">
      <table className="data-table">
        <thead>
          <tr>
            {renderSortableHeader(t("tableTime"), "created_at")}
            {renderSortableHeader(t("tableType"), "type")}
            {renderSortableHeader(t("tableSeverity"), "severity")}
            {renderSortableHeader(t("tableHost"), "host")}
            {renderSortableHeader(t("tableEvents"), "event_count")}
            <th>{t("tableMessage")}</th>
          </tr>
        </thead>
        <tbody>
          {alerts.map((alert) => (
            <tr key={alert.id}>
              <td>{formatDateTime(alert.created_at)}</td>
              <td>{alert.type || t("notAvailable")}</td>
              <td>
                <StatusBadge value={alert.severity} />
              </td>
              <td>{alert.host || t("notAvailable")}</td>
              <td>{alert.event_count}</td>
              <td title={alert.message}>{shortenText(alert.message, 110)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
