import StatusBadge from "./StatusBadge";
import { formatDateTime, shortenText } from "../utils/formatters";

// Tabular view of generated backend alerts.
export default function AlertsTable({ alerts }) {
  return (
    <div className="table-shell">
      <table className="data-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Type</th>
            <th>Severity</th>
            <th>Host</th>
            <th>Events</th>
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
