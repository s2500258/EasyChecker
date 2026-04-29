import { useEffect, useState } from "react";

import {
  fetchAlerts,
  fetchEvents,
  fetchFailedLoginRule,
  fetchHosts,
  fetchSuspiciousProcessRule,
  updateFailedLoginRule,
  updateSuspiciousProcessRule,
} from "./api/client";
import Layout from "./components/Layout";
import { messages } from "./i18n/messages";
import AlertsPage from "./pages/AlertsPage";
import AboutPage from "./pages/AboutPage";
import DashboardPage from "./pages/DashboardPage";
import EventsPage from "./pages/EventsPage";
import HostsPage from "./pages/HostsPage";

// Top-level frontend coordinator for data loading and simple page navigation.
export default function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [language, setLanguage] = useState(() => {
    return window.localStorage.getItem("easychecker-language") || "en";
  });
  const [events, setEvents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [hosts, setHosts] = useState([]);
  const [failedLoginRule, setFailedLoginRule] = useState(null);
  const [suspiciousProcessRule, setSuspiciousProcessRule] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  const t = (key) => messages[language]?.[key] || messages.en[key] || key;
  // Navigation stays local-state based for the MVP to keep the bundle and
  // setup simple while the number of views is still small.
  const navItems = [
    { key: "dashboard", label: t("navDashboard") },
    { key: "events", label: t("navEvents") },
    { key: "alerts", label: t("navAlerts") },
    { key: "hosts", label: t("navHosts") },
  ];

  async function loadData({ silent = false } = {}) {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      // Load events and alerts together so dashboard data stays aligned.
      // Hosts and rule settings are loaded in the same refresh pass so every
      // page sees a consistent snapshot of backend state.
      const [
        eventsData,
        alertsData,
        hostsData,
        failedLoginRuleData,
        suspiciousProcessRuleData,
      ] = await Promise.all([
        fetchEvents(),
        fetchAlerts(),
        fetchHosts(),
        fetchFailedLoginRule(),
        fetchSuspiciousProcessRule(),
      ]);
      setEvents(eventsData);
      setAlerts(alertsData);
      setHosts(hostsData);
      setFailedLoginRule(failedLoginRuleData);
      setSuspiciousProcessRule(suspiciousProcessRuleData);
      setError("");
      setLastUpdated(new Date().toISOString());
    } catch (loadError) {
      setError(loadError.message || t("loadError"));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    window.localStorage.setItem("easychecker-language", language);
  }, [language]);

  const pageProps = {
    events,
    alerts,
    hosts,
    failedLoginRule,
    suspiciousProcessRule,
    onUpdateFailedLoginRule: async (payload) => {
      // Update local state immediately after a successful backend save so the
      // rules panel reflects the active values without an extra full refresh.
      const updatedRule = await updateFailedLoginRule(payload);
      setFailedLoginRule(updatedRule);
      return updatedRule;
    },
    onUpdateSuspiciousProcessRule: async (payload) => {
      const updatedRule = await updateSuspiciousProcessRule(payload);
      setSuspiciousProcessRule(updatedRule);
      return updatedRule;
    },
    loading,
    error,
    onRefresh: () => loadData({ silent: true }),
    refreshing,
    lastUpdated,
    t,
  };

  // Keep routing simple for the MVP by switching pages from local state.
  let content = <DashboardPage {...pageProps} onOpenAbout={() => setActivePage("about")} />;
  if (activePage === "events") {
    content = <EventsPage {...pageProps} />;
  }
  if (activePage === "alerts") {
    content = <AlertsPage {...pageProps} />;
  }
  if (activePage === "hosts") {
    content = <HostsPage {...pageProps} />;
  }
  if (activePage === "about") {
    content = <AboutPage t={t} />;
  }

  return (
    <Layout
      activePage={activePage}
      navItems={navItems}
      onNavigate={setActivePage}
      onRefresh={() => loadData({ silent: true })}
      refreshing={refreshing}
      lastUpdated={lastUpdated}
      language={language}
      onLanguageChange={setLanguage}
      t={t}
    >
      {content}
    </Layout>
  );
}
