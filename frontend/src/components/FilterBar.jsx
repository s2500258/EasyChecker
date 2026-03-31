// Reusable host/severity/category filters for table pages.
export default function FilterBar({ filters, onChange, options, showCategory = false }) {
  return (
    <section className="filter-bar">
      <label>
        Host
        <input
          type="text"
          value={filters.host}
          onChange={(event) => onChange("host", event.target.value)}
          placeholder="Filter by host"
        />
      </label>

      <label>
        Severity
        <select
          value={filters.severity}
          onChange={(event) => onChange("severity", event.target.value)}
        >
          <option value="">All</option>
          {options.severities.map((severity) => (
            <option key={severity} value={severity}>
              {severity}
            </option>
          ))}
        </select>
      </label>

      {showCategory ? (
        <label>
          Category
          <select
            value={filters.category}
            onChange={(event) => onChange("category", event.target.value)}
          >
            <option value="">All</option>
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
