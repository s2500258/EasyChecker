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
  const highAlerts = alerts.filter((alert) => alert.severity === "HIGH").length;
  const latestEvents = events.slice(0, 5);
  const latestAlerts = alerts.slice(0, 5);

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
            sort={DEFAULT_EVENT_SORT}
            onSort={() => {}}
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
            sort={DEFAULT_ALERT_SORT}
            onSort={() => {}}
            t={t}
          />
        ) : (
          <div className="state-panel">{t("noAlertsYet")}</div>
        )}
      </section>
    </div>
  );
}
