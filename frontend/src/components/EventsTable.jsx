import StatusBadge from "./StatusBadge";
import { formatDateTime, shortenText } from "../utils/formatters";

// Tabular view of normalized backend events.
export default function EventsTable({ events, sort, onSort }) {
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
            {renderSortableHeader("Time", "ts")}
            {renderSortableHeader("Host", "host")}
            {renderSortableHeader("OS", "os_type")}
            {renderSortableHeader("Type", "event_type")}
            {renderSortableHeader("Code", "event_code")}
            {renderSortableHeader("Category", "category")}
            {renderSortableHeader("Severity", "severity")}
            {renderSortableHeader("User", "username")}
            {renderSortableHeader("IP", "ip_address")}
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          {events.map((event) => (
            <tr key={event.id}>
              <td>{formatDateTime(event.ts)}</td>
              <td>{event.host || "N/A"}</td>
              <td>{event.os_type || "N/A"}</td>
              <td>{event.event_type || "N/A"}</td>
              <td>{event.event_code || "N/A"}</td>
              <td>{event.category || "N/A"}</td>
              <td>
                <StatusBadge value={event.severity} />
              </td>
              <td>{event.username || "N/A"}</td>
              <td>{event.ip_address || "N/A"}</td>
              <td title={event.message}>{shortenText(event.message, 96)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
