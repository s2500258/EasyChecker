import { useMemo, useState } from "react";

import EventsTable from "../components/EventsTable";
import FilterBar from "../components/FilterBar";
import { sortUniqueValues } from "../utils/formatters";

// Full events page with lightweight client-side filtering.
export default function EventsPage({ events, loading, error }) {
  const [filters, setFilters] = useState({
    host: "",
    severity: "",
    category: "",
  });

  const options = useMemo(
    () => ({
      severities: sortUniqueValues(events.map((event) => event.severity)),
      categories: sortUniqueValues(events.map((event) => event.category)),
    }),
    [events],
  );

  const filteredEvents = useMemo(() => {
    // Filtering stays client-side for the MVP while the dataset remains small.
    return events.filter((event) => {
      const matchesHost = filters.host
        ? event.host?.toLowerCase().includes(filters.host.toLowerCase())
        : true;
      const matchesSeverity = filters.severity
        ? event.severity === filters.severity
        : true;
      const matchesCategory = filters.category
        ? event.category === filters.category
        : true;
      return matchesHost && matchesSeverity && matchesCategory;
    });
  }, [events, filters]);

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Events</h2>
        <p>Review normalized telemetry coming from the backend.</p>
      </div>

      <FilterBar
        filters={filters}
        onChange={updateFilter}
        options={options}
        showCategory
      />

      {loading ? <div className="state-panel">Loading events...</div> : null}
      {error ? <div className="state-panel error">{error}</div> : null}
      {!loading && !error && !filteredEvents.length ? (
        <div className="state-panel">No events match the current filters.</div>
      ) : null}
      {!loading && !error && filteredEvents.length ? (
        <EventsTable events={filteredEvents} />
      ) : null}
    </section>
  );
}
