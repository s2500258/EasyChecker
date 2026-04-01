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
  const [sort, setSort] = useState({
    key: "created_at",
    direction: "desc",
  });

  const options = useMemo(
    () => ({
      severities: sortUniqueValues(alerts.map((alert) => alert.severity)),
      categories: [],
    }),
    [alerts],
  );

  const filteredAlerts = useMemo(() => {
    const matchingAlerts = alerts.filter((alert) => {
      const matchesHost = filters.host
        ? alert.host?.toLowerCase().includes(filters.host.toLowerCase())
        : true;
      const matchesSeverity = filters.severity
        ? alert.severity === filters.severity
        : true;
      return matchesHost && matchesSeverity;
    });

    return [...matchingAlerts].sort((left, right) =>
      compareValues(left[sort.key], right[sort.key], sort.direction),
    );
  }, [alerts, filters, sort]);

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  function updateSort(key) {
    setSort((current) => ({
      key,
      direction:
        current.key === key && current.direction === "asc" ? "desc" : "asc",
    }));
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
        <AlertsTable alerts={filteredAlerts} sort={sort} onSort={updateSort} />
      ) : null}
    </section>
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
