import { useEffect, useState } from "react";

import { fetchAlerts, fetchEvents } from "./api/client";
import Layout from "./components/Layout";
import AlertsPage from "./pages/AlertsPage";
import DashboardPage from "./pages/DashboardPage";
import EventsPage from "./pages/EventsPage";

const NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard" },
  { key: "events", label: "Events" },
  { key: "alerts", label: "Alerts" },
];

// Top-level frontend coordinator for data loading and simple page navigation.
export default function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [events, setEvents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  async function loadData({ silent = false } = {}) {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      // Load events and alerts together so dashboard data stays aligned.
      const [eventsData, alertsData] = await Promise.all([
        fetchEvents(),
        fetchAlerts(),
      ]);
      setEvents(eventsData);
      setAlerts(alertsData);
      setError("");
      setLastUpdated(new Date().toISOString());
    } catch (loadError) {
      setError(loadError.message || "Could not load data.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const pageProps = {
    events,
    alerts,
    loading,
    error,
    onRefresh: () => loadData({ silent: true }),
    refreshing,
    lastUpdated,
  };

  // Keep routing simple for the MVP by switching pages from local state.
  let content = <DashboardPage {...pageProps} />;
  if (activePage === "events") {
    content = <EventsPage {...pageProps} />;
  }
  if (activePage === "alerts") {
    content = <AlertsPage {...pageProps} />;
  }

  return (
    <Layout
      activePage={activePage}
      navItems={NAV_ITEMS}
      onNavigate={setActivePage}
      onRefresh={() => loadData({ silent: true })}
      refreshing={refreshing}
      lastUpdated={lastUpdated}
    >
      {content}
    </Layout>
  );
}
