import { Fragment, useState } from "react";

import StatusBadge from "./StatusBadge";
import { formatDateTime, shortenText } from "../utils/formatters";

// Tabular view of normalized backend events.
export default function EventsTable({ events, sort, onSort, t }) {
  // Expanded message rows are tracked by event ID so multiple long log entries
  // can stay open at once while the analyst compares them.
  const [expandedMessageIds, setExpandedMessageIds] = useState([]);

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

  function toggleMessage(eventId) {
    // Toggling below the main row keeps the table compact while still allowing
    // full-width inspection of verbose Windows event messages.
    setExpandedMessageIds((current) =>
      current.includes(eventId)
        ? current.filter((id) => id !== eventId)
        : [...current, eventId],
    );
  }

  return (
    <div className="table-shell">
      <table className="data-table">
        <thead>
          <tr>
            {renderSortableHeader(t("tableTime"), "ts")}
            {renderSortableHeader(t("tableHost"), "host")}
            {renderSortableHeader(t("tableHostIP"), "host_ip")}
            {renderSortableHeader(t("tableOS"), "os_type")}
            {renderSortableHeader(t("tableType"), "event_type")}
            {renderSortableHeader(t("tableCode"), "event_code")}
            {renderSortableHeader(t("tableCategory"), "category")}
            {renderSortableHeader(t("tableSeverity"), "severity")}
            {renderSortableHeader(t("tableUser"), "username")}
            {renderSortableHeader(t("tableEventIP"), "ip_address")}
            <th>{t("tableMessage")}</th>
          </tr>
        </thead>
        <tbody>
          {events.map((event) => {
            const isExpanded = expandedMessageIds.includes(event.id);
            const isLongMessage = (event.message || "").length > 96;

            return (
              <Fragment key={event.id}>
                <tr className={isExpanded ? "event-row expanded" : "event-row"}>
                  <td>{formatDateTime(event.ts)}</td>
                  <td>{event.host || t("notAvailable")}</td>
                  <td>{event.host_ip || t("notAvailable")}</td>
                  <td>{event.os_type || t("notAvailable")}</td>
                  <td>{event.event_type || t("notAvailable")}</td>
                  <td>{event.event_code || t("notAvailable")}</td>
                  <td>{event.category || t("notAvailable")}</td>
                  <td>
                    <StatusBadge value={event.severity} />
                  </td>
                  <td>{event.username || t("notAvailable")}</td>
                  <td>{event.ip_address || t("notAvailable")}</td>
                  <td title={event.message}>
                    <div className="event-message-cell">
                      <span>{shortenText(event.message, 96)}</span>
                      {isLongMessage ? (
                        <button
                          className="message-toggle-button"
                          onClick={() => toggleMessage(event.id)}
                          type="button"
                        >
                          {isExpanded ? t("hideMessage") : t("showAll")}
                        </button>
                      ) : null}
                    </div>
                  </td>
                </tr>
                {isExpanded ? (
                  <tr className="event-full-message-row">
                    <td colSpan={11}>
                      <div className="event-full-message-panel">
                        <p className="event-full-message-title">{t("tableMessage")}</p>
                        <p className="event-full-message-text">
                          {event.message || t("notAvailable")}
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
