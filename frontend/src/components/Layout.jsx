import { formatDateTime } from "../utils/formatters";

// Shared frame for the dashboard, navigation, and refresh controls.
export default function Layout({
  activePage,
  navItems,
  onNavigate,
  onRefresh,
  refreshing,
  lastUpdated,
  language,
  onLanguageChange,
  t,
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
            <p className="eyebrow">{t("heroEyebrow")}</p>
            <h1>EasyChecker</h1>
            <p className="hero-copy">{t("heroCopy")}</p>
          </div>
        </div>
        <div className="hero-actions">
          <div className="language-switcher" aria-label={t("language")}>
            <button
              className={language === "en" ? "lang-button active" : "lang-button"}
              onClick={() => onLanguageChange("en")}
              type="button"
            >
              EN
            </button>
            <button
              className={language === "fi" ? "lang-button active" : "lang-button"}
              onClick={() => onLanguageChange("fi")}
              type="button"
            >
              FI
            </button>
          </div>
          <button className="refresh-button" onClick={onRefresh} type="button">
            {refreshing ? t("refreshing") : t("refresh")}
          </button>
          <p className="timestamp">
            {t("lastUpdated")}: {lastUpdated ? formatDateTime(lastUpdated) : t("notYet")}
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
