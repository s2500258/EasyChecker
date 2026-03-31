const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1";

async function request(path) {
  // Keep backend API access in one place so endpoint changes are centralized.
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json();
}

export function fetchEvents() {
  return request("/events");
}

export function fetchAlerts() {
  return request("/alerts");
}
