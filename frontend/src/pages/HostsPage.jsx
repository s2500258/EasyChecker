import { useMemo, useState } from "react";

import HostsTable from "../components/HostsTable";
import { sortUniqueValues } from "../utils/formatters";

// Aggregated host overview page built from the backend /hosts endpoint.
export default function HostsPage({ hosts, loading, error, t }) {
  const PAGE_SIZE_OPTIONS = ["20", "50", "100", "all"];
  const [filters, setFilters] = useState({
    host: "",
    severity: "",
    os: "",
  });
  const [pageSize, setPageSize] = useState("20");
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState({
    key: "last_seen",
    direction: "desc",
  });

  const options = useMemo(
    () => ({
      severities: sortUniqueValues(hosts.map((host) => host.highest_severity)),
      osTypes: sortUniqueValues(hosts.map((host) => host.os_type)),
    }),
    [hosts],
  );

  const filteredHosts = useMemo(() => {
    const matchingHosts = hosts.filter((host) => {
      const matchesHost = filters.host
        ? host.host?.toLowerCase().includes(filters.host.toLowerCase())
        : true;
      const matchesSeverity = filters.severity
        ? host.highest_severity === filters.severity
        : true;
      const matchesOs = filters.os ? host.os_type === filters.os : true;
      return matchesHost && matchesSeverity && matchesOs;
    });

    return [...matchingHosts].sort((left, right) =>
      compareValues(left[sort.key], right[sort.key], sort.direction),
    );
  }, [hosts, filters, sort]);

  const resolvedPageSize =
    pageSize === "all" ? filteredHosts.length || 1 : Number(pageSize);
  const totalPages =
    pageSize === "all" ? 1 : Math.max(1, Math.ceil(filteredHosts.length / resolvedPageSize));
  const currentPage = Math.min(page, totalPages);
  const pagedHosts = useMemo(() => {
    if (pageSize === "all") {
      return filteredHosts;
    }
    const start = (currentPage - 1) * resolvedPageSize;
    return filteredHosts.slice(start, start + resolvedPageSize);
  }, [filteredHosts, pageSize, currentPage, resolvedPageSize]);
  const rangeStart = filteredHosts.length ? (currentPage - 1) * resolvedPageSize + 1 : 0;
  const rangeEnd =
    pageSize === "all"
      ? filteredHosts.length
      : Math.min(currentPage * resolvedPageSize, filteredHosts.length);

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
          <span className="page-title-icon" aria-hidden="true">🖥️</span>
          {t("hostsTitle")}
        </h2>
        <p>{t("hostsCopy")}</p>
      </div>

      <section className="filter-bar hosts-filter-bar">
        <label>
          {t("filterHost")}
          <input
            type="text"
            value={filters.host}
            onChange={(event) => updateFilter("host", event.target.value)}
            placeholder={t("filterHostPlaceholder")}
          />
        </label>

        <label>
          {t("filterSeverity")}
          <select
            value={filters.severity}
            onChange={(event) => updateFilter("severity", event.target.value)}
          >
            <option value="">{t("filterAll")}</option>
            {options.severities.map((severity) => (
              <option key={severity} value={severity}>
                {severity}
              </option>
            ))}
          </select>
        </label>

        <label>
          {t("hostsFilterOs")}
          <select value={filters.os} onChange={(event) => updateFilter("os", event.target.value)}>
            <option value="">{t("filterAll")}</option>
            {options.osTypes.map((osType) => (
              <option key={osType} value={osType}>
                {osType}
              </option>
            ))}
          </select>
        </label>
      </section>

      {loading ? <div className="state-panel">{t("hostsLoading")}</div> : null}
      {error ? <div className="state-panel error">{error}</div> : null}
      {!loading && !error && !filteredHosts.length ? (
        <div className="state-panel">{t("hostsEmpty")}</div>
      ) : null}
      {!loading && !error && filteredHosts.length ? (
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
                total: filteredHosts.length,
              })}
            </p>
          </div>

          <HostsTable hosts={pagedHosts} sort={sort} onSort={updateSort} t={t} />

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
