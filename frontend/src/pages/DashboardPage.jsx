import { useMemo, useState } from "react";

import AlertsTable from "../components/AlertsTable";
import EventsTable from "../components/EventsTable";
import MetricCard from "../components/MetricCard";

const DEFAULT_EVENT_SORT = {
  key: "ts",
  direction: "desc",
};

const DEFAULT_ALERT_SORT = {
  key: "created_at",
  direction: "desc",
};

// Overview page with summary cards plus the latest events and alerts.
export default function DashboardPage({
  events,
  alerts,
  loading,
  error,
  t,
}) {
  const [eventSort, setEventSort] = useState(DEFAULT_EVENT_SORT);
  const [alertSort, setAlertSort] = useState(DEFAULT_ALERT_SORT);
  const highAlerts = alerts.filter((alert) => alert.severity === "HIGH").length;
  const latestEvents = useMemo(() => {
    return [...events]
      .sort((left, right) =>
        compareValues(left[eventSort.key], right[eventSort.key], eventSort.direction),
      )
      .slice(0, 5);
  }, [events, eventSort]);
  const latestAlerts = useMemo(() => {
    return [...alerts]
      .sort((left, right) =>
        compareValues(left[alertSort.key], right[alertSort.key], alertSort.direction),
      )
      .slice(0, 5);
  }, [alerts, alertSort]);

  function updateEventSort(key) {
    setEventSort((current) => ({
      key,
      direction:
        current.key === key && current.direction === "asc" ? "desc" : "asc",
    }));
  }

  function updateAlertSort(key) {
    setAlertSort((current) => ({
      key,
      direction:
        current.key === key && current.direction === "asc" ? "desc" : "asc",
    }));
  }

  if (loading) {
    return <section className="state-panel">{t("loadingDashboard")}</section>;
  }

  if (error) {
    return <section className="state-panel error">{error}</section>;
  }

  return (
    <div className="stack">
      <section className="metrics-grid">
        <MetricCard label={t("totalEvents")} value={events.length} accent="amber" />
        <MetricCard label={t("totalAlerts")} value={alerts.length} accent="red" />
        <MetricCard label={t("highAlerts")} value={highAlerts} accent="charcoal" />
        <MetricCard
          label={t("uniqueHosts")}
          value={new Set(events.map((event) => event.host)).size}
          accent="teal"
        />
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>{t("latestEvents")}</h2>
          <p>{t("latestEventsCopy")}</p>
        </div>
        {latestEvents.length ? (
          <EventsTable
            events={latestEvents}
            sort={eventSort}
            onSort={updateEventSort}
            t={t}
          />
        ) : (
          <div className="state-panel">{t("noEventsYet")}</div>
        )}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>{t("latestAlerts")}</h2>
          <p>{t("latestAlertsCopy")}</p>
        </div>
        {latestAlerts.length ? (
          <AlertsTable
            alerts={latestAlerts}
            sort={alertSort}
            onSort={updateAlertSort}
            t={t}
          />
        ) : (
          <div className="state-panel">{t("noAlertsYet")}</div>
        )}
      </section>
    </div>
  );
}

function compareValues(left, right, direction) {
  const normalizedLeft = normalizeValue(left);
  const normalizedRight = normalizeValue(right);

  if (normalizedLeft < normalizedRight) {
    return direction === "asc" ? -1 : 1;
  }
  if (normalizedLeft > normalizedRight) {
    return direction === "asc" ? 1 : -1;
  }
  return 0;
}

function normalizeValue(value) {
  if (value === null || value === undefined || value === "") {
    return "";
  }

  if (typeof value === "number") {
    return value;
  }

  const date = new Date(value);
  if (!Number.isNaN(date.getTime()) && typeof value === "string") {
    return date.getTime();
  }

  return String(value).toLowerCase();
}
