import { Fragment, useMemo, useState } from "react";

import StatusBadge from "./StatusBadge";
import { formatDateTime, shortenText } from "../utils/formatters";

// Tabular view of generated backend alerts.
export default function AlertsTable({ alerts, events = [], sort, onSort, t }) {
  const [expandedAlertId, setExpandedAlertId] = useState(null);
  // Build a lookup once per event refresh so alert rows can quickly resolve
  // their linked event IDs into full event objects for the expandable panel.
  const eventsById = useMemo(() => {
    return new Map(events.map((event) => [event.id, event]));
  }, [events]);

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
            <th>{t("tableLinkedEvents")}</th>
            <th>{t("tableMessage")}</th>
          </tr>
        </thead>
        <tbody>
          {alerts.map((alert) => {
            // Alerts only store event IDs; the frontend joins them back to full
            // event payloads so the analyst can inspect the triggering records.
            const linkedEvents = (alert.event_ids || [])
              .map((eventId) => eventsById.get(eventId))
              .filter(Boolean);
            const isExpanded = expandedAlertId === alert.id;

            return (
              <Fragment key={alert.id}>
                <tr
                  className={isExpanded ? "alert-row expanded" : "alert-row"}
                >
                  <td>{formatDateTime(alert.created_at)}</td>
                  <td>{alert.type || t("notAvailable")}</td>
                  <td>
                    <StatusBadge value={alert.severity} />
                  </td>
                  <td>{alert.host || t("notAvailable")}</td>
                  <td>{alert.event_count}</td>
                  <td>
                    <button
                      className="linked-events-button"
                      onClick={() =>
                        setExpandedAlertId((current) =>
                          current === alert.id ? null : alert.id,
                        )
                      }
                      type="button"
                    >
                      {isExpanded
                        ? t("linkedEventsHide")
                        : formatLinkedEventButtonLabel(
                            t("linkedEventsShow"),
                            alert.event_ids?.length || 0,
                          )}
                    </button>
                  </td>
                  <td title={alert.message}>{shortenText(alert.message, 110)}</td>
                </tr>
                {isExpanded ? (
                  <tr className="alert-events-row">
                    <td colSpan={7}>
                      {linkedEvents.length ? (
                        <div className="alert-events-panel">
                          <p className="alert-events-title">
                            {formatLinkedEventTitle(
                              t("linkedEventsTitle"),
                              linkedEvents.length,
                            )}
                          </p>
                          <div className="alert-event-list">
                            {linkedEvents.map((event) => (
                              <article className="alert-event-card" key={event.id}>
                                <div className="alert-event-meta">
                                  <strong>#{event.id}</strong>
                                  <span>{formatDateTime(event.ts)}</span>
                                  <span>{event.host || t("notAvailable")}</span>
                                  <span>{event.event_code || t("notAvailable")}</span>
                                  <span>{event.category || t("notAvailable")}</span>
                                </div>
                                <div className="alert-event-fields">
                                  <p>
                                    <span>{t("tableType")}:</span> {event.event_type || t("notAvailable")}
                                  </p>
                                  <p>
                                    <span>{t("tableSeverity")}:</span> {event.severity || t("notAvailable")}
                                  </p>
                                  <p>
                                    <span>{t("tableUser")}:</span> {event.username || t("notAvailable")}
                                  </p>
                                  <p>
                                    <span>{t("tableHostIP")}:</span> {event.host_ip || t("notAvailable")}
                                  </p>
                                  <p>
                                    <span>{t("tableEventIP")}:</span> {event.ip_address || t("notAvailable")}
                                  </p>
                                </div>
                                <p className="alert-event-message">
                                  <span>{t("tableMessage")}:</span> {event.message || t("notAvailable")}
                                </p>
                              </article>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="state-panel">{t("linkedEventsEmpty")}</div>
                      )}
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

function formatLinkedEventButtonLabel(template, count) {
  return template.replace("{count}", String(count));
}

function formatLinkedEventTitle(template, count) {
  return template.replace("{count}", String(count));
}
