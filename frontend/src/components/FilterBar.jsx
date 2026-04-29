// Reusable host/severity/category filters for table pages.
export default function FilterBar({
  filters,
  onChange,
  options,
  showCategory = false,
  showHostIp = false,
  showTimeRange = false,
  t,
}) {
  return (
    <section className="filter-bar">
      <label>
        {t("filterHost")}
        <input
          type="text"
          value={filters.host}
          onChange={(event) => onChange("host", event.target.value)}
          placeholder={t("filterHostPlaceholder")}
        />
      </label>

      <label>
        {t("filterSeverity")}
        <select
          value={filters.severity}
          onChange={(event) => onChange("severity", event.target.value)}
        >
          <option value="">{t("filterAll")}</option>
          {options.severities.map((severity) => (
            <option key={severity} value={severity}>
              {severity}
            </option>
          ))}
        </select>
      </label>

      {showTimeRange ? (
        <label>
          {t("filterTimeFrom")}
          <input
            type="datetime-local"
            value={filters.timeFrom}
            onChange={(event) => onChange("timeFrom", event.target.value)}
          />
        </label>
      ) : null}

      {showTimeRange ? (
        <label>
          {t("filterTimeTo")}
          <input
            type="datetime-local"
            value={filters.timeTo}
            onChange={(event) => onChange("timeTo", event.target.value)}
          />
        </label>
      ) : null}

      {showHostIp ? (
        <label>
          {t("filterHostIp")}
          <input
            type="text"
            value={filters.hostIp}
            onChange={(event) => onChange("hostIp", event.target.value)}
            placeholder={t("filterHostIpPlaceholder")}
          />
        </label>
      ) : null}

      {showCategory ? (
        <label>
          {t("filterCategory")}
          <select
            value={filters.category}
            onChange={(event) => onChange("category", event.target.value)}
          >
            <option value="">{t("filterAll")}</option>
            {options.categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </label>
      ) : null}
    </section>
  );
}
