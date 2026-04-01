import StatusBadge from "./StatusBadge";
import { formatDateTime, shortenText } from "../utils/formatters";

// Tabular view of generated backend alerts.
export default function AlertsTable({ alerts, sort, onSort }) {
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
            {renderSortableHeader("Time", "created_at")}
            {renderSortableHeader("Type", "type")}
            {renderSortableHeader("Severity", "severity")}
            {renderSortableHeader("Host", "host")}
            {renderSortableHeader("Events", "event_count")}
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          {alerts.map((alert) => (
            <tr key={alert.id}>
              <td>{formatDateTime(alert.created_at)}</td>
              <td>{alert.type}</td>
              <td>
                <StatusBadge value={alert.severity} />
              </td>
              <td>{alert.host}</td>
              <td>{alert.event_count}</td>
              <td title={alert.message}>{shortenText(alert.message, 110)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
