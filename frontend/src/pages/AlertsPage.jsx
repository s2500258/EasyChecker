import { useMemo, useState } from "react";

import AlertsTable from "../components/AlertsTable";
import FilterBar from "../components/FilterBar";
import { sortUniqueValues } from "../utils/formatters";

// Full alerts page with simple host and severity filters.
export default function AlertsPage({ alerts, loading, error }) {
  const [filters, setFilters] = useState({
    host: "",
    severity: "",
    category: "",
  });

  const options = useMemo(
    () => ({
      severities: sortUniqueValues(alerts.map((alert) => alert.severity)),
      categories: [],
    }),
    [alerts],
  );

  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      const matchesHost = filters.host
        ? alert.host?.toLowerCase().includes(filters.host.toLowerCase())
        : true;
      const matchesSeverity = filters.severity
        ? alert.severity === filters.severity
        : true;
      return matchesHost && matchesSeverity;
    });
  }, [alerts, filters]);

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Alerts</h2>
        <p>Inspect generated alerts and spot the highest severity activity.</p>
      </div>

      <FilterBar filters={filters} onChange={updateFilter} options={options} />

      {loading ? <div className="state-panel">Loading alerts...</div> : null}
      {error ? <div className="state-panel error">{error}</div> : null}
      {!loading && !error && !filteredAlerts.length ? (
        <div className="state-panel">No alerts match the current filters.</div>
      ) : null}
      {!loading && !error && filteredAlerts.length ? (
        <AlertsTable alerts={filteredAlerts} />
      ) : null}
    </section>
  );
}
