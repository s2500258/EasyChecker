import StatusBadge from "./StatusBadge";
import { formatDateTime } from "../utils/formatters";

// Tabular host inventory view built from aggregated backend host summaries.
export default function HostsTable({ hosts, sort, onSort, t }) {
  function renderSortableHeader(label, key, className = "") {
    const isActive = sort.key === key;
    const direction = isActive ? sort.direction : "";

    return (
      <th className={className}>
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
            {renderSortableHeader(t("hostsStatus"), "activity_status", "host-status-column")}
            {renderSortableHeader(t("tableHost"), "host")}
            {renderSortableHeader(t("tableOS"), "os_type")}
            {renderSortableHeader(t("hostsLastSeen"), "last_seen")}
            {renderSortableHeader(t("hostsTotalEvents"), "total_events")}
            {renderSortableHeader(t("hostsTotalAlerts"), "total_alerts")}
            {renderSortableHeader(t("hostsHighestSeverity"), "highest_severity")}
            {renderSortableHeader(t("hostsLastEventType"), "last_event_type")}
          </tr>
        </thead>
        <tbody>
          {hosts.map((host) => (
            <tr key={host.host}>
              <td className="host-status-cell">
                <span
                  className={
                    host.activity_status === "ONLINE"
                      ? "host-status-dot online"
                      : "host-status-dot offline"
                  }
                  title={
                    host.activity_status === "ONLINE"
                      ? t("hostsStatusOnline")
                      : t("hostsStatusOffline")
                  }
                  aria-label={
                    host.activity_status === "ONLINE"
                      ? t("hostsStatusOnline")
                      : t("hostsStatusOffline")
                  }
                />
              </td>
              <td>{host.host || t("notAvailable")}</td>
              <td>{host.os_type || t("notAvailable")}</td>
              <td>{host.last_seen ? formatDateTime(host.last_seen) : t("notAvailable")}</td>
              <td>{host.total_events}</td>
              <td>{host.total_alerts}</td>
              <td>
                {host.highest_severity ? (
                  <StatusBadge value={host.highest_severity} />
                ) : (
                  t("notAvailable")
                )}
              </td>
              <td>{host.last_event_type || t("notAvailable")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
