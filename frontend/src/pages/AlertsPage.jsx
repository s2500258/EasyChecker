import { useMemo, useState } from "react";

import AlertsTable from "../components/AlertsTable";
import FilterBar from "../components/FilterBar";
import { sortUniqueValues } from "../utils/formatters";

// Full alerts page with simple host and severity filters.
export default function AlertsPage({ alerts, loading, error, t }) {
  const PAGE_SIZE_OPTIONS = ["20", "50", "100", "all"];
  const [filters, setFilters] = useState({
    host: "",
    severity: "",
    category: "",
  });
  const [pageSize, setPageSize] = useState("20");
  const [page, setPage] = useState(1);
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

  const resolvedPageSize =
    pageSize === "all" ? filteredAlerts.length || 1 : Number(pageSize);
  const totalPages =
    pageSize === "all" ? 1 : Math.max(1, Math.ceil(filteredAlerts.length / resolvedPageSize));
  const currentPage = Math.min(page, totalPages);
  const pagedAlerts = useMemo(() => {
    if (pageSize === "all") {
      return filteredAlerts;
    }
    const start = (currentPage - 1) * resolvedPageSize;
    return filteredAlerts.slice(start, start + resolvedPageSize);
  }, [filteredAlerts, pageSize, currentPage, resolvedPageSize]);
  const rangeStart = filteredAlerts.length ? (currentPage - 1) * resolvedPageSize + 1 : 0;
  const rangeEnd =
    pageSize === "all"
      ? filteredAlerts.length
      : Math.min(currentPage * resolvedPageSize, filteredAlerts.length);

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
        <h2>{t("alertsTitle")}</h2>
        <p>{t("alertsCopy")}</p>
      </div>

      <FilterBar filters={filters} onChange={updateFilter} options={options} t={t} />

      {loading ? <div className="state-panel">{t("loadingAlerts")}</div> : null}
      {error ? <div className="state-panel error">{error}</div> : null}
      {!loading && !error && !filteredAlerts.length ? (
        <div className="state-panel">{t("noFilteredAlerts")}</div>
      ) : null}
      {!loading && !error && filteredAlerts.length ? (
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
                total: filteredAlerts.length,
              })}
            </p>
          </div>

          <AlertsTable alerts={pagedAlerts} sort={sort} onSort={updateSort} t={t} />

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

function formatMessage(template, values) {
  return Object.entries(values).reduce((result, [key, value]) => {
    return result.replace(`{${key}}`, String(value));
  }, template);
}
