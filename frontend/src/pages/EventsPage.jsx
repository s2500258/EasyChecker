import { useMemo, useState } from "react";

import EventsTable from "../components/EventsTable";
import FilterBar from "../components/FilterBar";
import { sortUniqueValues } from "../utils/formatters";

// Full events page with lightweight client-side filtering.
export default function EventsPage({ events, loading, error, t }) {
  const PAGE_SIZE_OPTIONS = ["20", "50", "100", "all"];
  const [filters, setFilters] = useState({
    host: "",
    severity: "",
    timeFrom: "",
    timeTo: "",
    hostIp: "",
    category: "",
  });
  const [pageSize, setPageSize] = useState("20");
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState({
    key: "ts",
    direction: "desc",
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
    const matchingEvents = events.filter((event) => {
      const matchesHost = filters.host
        ? event.host?.toLowerCase().includes(filters.host.toLowerCase())
        : true;
      const matchesSeverity = filters.severity
        ? event.severity === filters.severity
        : true;
      const matchesTimeFrom = filters.timeFrom
        ? eventFallsAfter(event.ts, filters.timeFrom)
        : true;
      const matchesTimeTo = filters.timeTo
        ? eventFallsBefore(event.ts, filters.timeTo)
        : true;
      const matchesHostIp = filters.hostIp
        ? event.host_ip?.toLowerCase().includes(filters.hostIp.toLowerCase())
        : true;
      const matchesCategory = filters.category
        ? event.category === filters.category
        : true;
      return (
        matchesHost &&
        matchesSeverity &&
        matchesTimeFrom &&
        matchesTimeTo &&
        matchesHostIp &&
        matchesCategory
      );
    });

    return [...matchingEvents].sort((left, right) =>
      compareValues(left[sort.key], right[sort.key], sort.direction),
    );
  }, [events, filters, sort]);

  const resolvedPageSize =
    pageSize === "all" ? filteredEvents.length || 1 : Number(pageSize);
  // Keep pagination derived from the filtered result so page controls stay
  // consistent after sorting, filtering, or switching page size.
  const totalPages =
    pageSize === "all" ? 1 : Math.max(1, Math.ceil(filteredEvents.length / resolvedPageSize));
  const currentPage = Math.min(page, totalPages);
  const pagedEvents = useMemo(() => {
    if (pageSize === "all") {
      return filteredEvents;
    }
    const start = (currentPage - 1) * resolvedPageSize;
    return filteredEvents.slice(start, start + resolvedPageSize);
  }, [filteredEvents, pageSize, currentPage, resolvedPageSize]);
  const rangeStart = filteredEvents.length ? (currentPage - 1) * resolvedPageSize + 1 : 0;
  const rangeEnd =
    pageSize === "all"
      ? filteredEvents.length
      : Math.min(currentPage * resolvedPageSize, filteredEvents.length);

  function updateFilter(key, value) {
    setPage(1);
    setFilters((current) => ({ ...current, [key]: value }));
  }

  function updateSort(key) {
    setPage(1);
    setSort((current) => ({
      key,
      direction:
        current.key === key && current.direction === "asc" ? "desc" : "asc",
    }));
  }

  function updatePageSize(value) {
    setPageSize(value);
    setPage(1);
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>
          <span className="page-title-icon" aria-hidden="true">📄</span>
          {t("eventsTitle")}
        </h2>
        <p>{t("eventsCopy")}</p>
      </div>

      <FilterBar
        filters={filters}
        onChange={updateFilter}
        options={options}
        showCategory
        showHostIp
        showTimeRange
        t={t}
      />

      {loading ? <div className="state-panel">{t("loadingEvents")}</div> : null}
      {error ? <div className="state-panel error">{error}</div> : null}
      {!loading && !error && !filteredEvents.length ? (
        <div className="state-panel">{t("noFilteredEvents")}</div>
      ) : null}
      {!loading && !error && filteredEvents.length ? (
        <>
          <div className="pagination-bar">
            <label className="page-size-control">
              <span>{t("pageSize")}</span>
              <select
                value={pageSize}
                onChange={(event) => updatePageSize(event.target.value)}
              >
                {PAGE_SIZE_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option === "all" ? t("pageSizeAll") : option}
                  </option>
                ))}
              </select>
            </label>
            <p className="pagination-summary">
              {formatMessage(t("pageSummary"), {
                from: rangeStart,
                to: rangeEnd,
                total: filteredEvents.length,
              })}
            </p>
          </div>

          <EventsTable events={pagedEvents} sort={sort} onSort={updateSort} t={t} />

          <div className="pagination-footer">
            <p className="pagination-summary">
              {formatMessage(t("pageNumber"), {
                current: currentPage,
                total: totalPages,
              })}
            </p>
            <div className="pagination-actions">
              <button
                className="pagination-button"
                disabled={currentPage === 1}
                onClick={() => setPage((value) => Math.max(1, value - 1))}
                type="button"
              >
                {t("pagePrevious")}
              </button>
              <button
                className="pagination-button"
                disabled={currentPage === totalPages}
                onClick={() => setPage((value) => Math.min(totalPages, value + 1))}
                type="button"
              >
                {t("pageNext")}
              </button>
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}

function compareValues(left, right, direction) {
  // Normalize timestamps, empty values, and strings into one comparable shape
  // so the same sorter can be reused across all table columns.
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

  const date = new Date(value);
  if (!Number.isNaN(date.getTime()) && typeof value === "string") {
    return date.getTime();
  }

  return String(value).toLowerCase();
}

function formatMessage(template, values) {
  return Object.entries(values).reduce((result, [key, value]) => {
    return result.replace(`{${key}}`, String(value));
  }, template);
}

function eventFallsAfter(eventTimestamp, fromValue) {
  // Invalid dates should not silently hide events from the analyst, so failed
  // parsing falls back to "keep the row visible" instead of filtering it out.
  const eventDate = new Date(eventTimestamp);
  const fromDate = new Date(fromValue);
  if (Number.isNaN(eventDate.getTime()) || Number.isNaN(fromDate.getTime())) {
    return true;
  }
  return eventDate.getTime() >= fromDate.getTime();
}

function eventFallsBefore(eventTimestamp, toValue) {
  const eventDate = new Date(eventTimestamp);
  const toDate = new Date(toValue);
  if (Number.isNaN(eventDate.getTime()) || Number.isNaN(toDate.getTime())) {
    return true;
  }
  return eventDate.getTime() <= toDate.getTime();
}
