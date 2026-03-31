import StatusBadge from "./StatusBadge";
import { formatDateTime, shortenText } from "../utils/formatters";

// Tabular view of normalized backend events.
export default function EventsTable({ events }) {
  return (
    <div className="table-shell">
      <table className="data-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Host</th>
            <th>OS</th>
            <th>Type</th>
            <th>Code</th>
            <th>Category</th>
            <th>Severity</th>
            <th>User</th>
            <th>IP</th>
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
