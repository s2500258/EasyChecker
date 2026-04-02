import { formatDateTime } from "../utils/formatters";

// Shared frame for the dashboard, navigation, and refresh controls.
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
        <div className="hero-main">
          <img
            className="hero-logo"
            src="/logo1.png"
            alt="EasyChecker logo"
          />
          <div className="hero-copy-block">
            <p className="eyebrow">Security Monitoring Console</p>
            <h1>EasyChecker</h1>
            <p className="hero-copy">
              Review host telemetry, detect suspicious behavior, and monitor
              alerts from the backend pipeline in one analyst-focused view.
            </p>
          </div>
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
