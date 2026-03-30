import { formatDateTime } from "../utils/formatters";

export default function Layout({
  activePage,
  navItems,
  onNavigate,
  onRefresh,
  refreshing,
  lastUpdated,
  children,
}) {
  return (
    <div className="app-shell">
      <div className="app-backdrop" />
      <header className="hero">
        <div>
          <p className="eyebrow">Educational SIEM Console</p>
          <h1>EasyChecker</h1>
          <p className="hero-copy">
            Track real events from the backend, review generated alerts, and
            validate that your Windows agent is feeding the pipeline end to end.
          </p>
        </div>
        <div className="hero-actions">
          <button className="refresh-button" onClick={onRefresh} type="button">
            {refreshing ? "Refreshing..." : "Refresh Data"}
          </button>
          <p className="timestamp">
            Last updated: {lastUpdated ? formatDateTime(lastUpdated) : "Not yet"}
          </p>
        </div>
      </header>

      <nav className="nav-tabs" aria-label="Primary">
        {navItems.map((item) => (
          <button
            key={item.key}
            className={item.key === activePage ? "nav-tab active" : "nav-tab"}
            onClick={() => onNavigate(item.key)}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </nav>

      <main className="page-content">{children}</main>
    </div>
  );
}
