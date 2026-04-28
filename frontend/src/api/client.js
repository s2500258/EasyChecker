const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1";

async function request(path) {
  // Keep backend API access in one place so endpoint changes are centralized.
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json();
}

async function requestWithBody(path, method, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
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

export function fetchHosts() {
  return request("/hosts");
}

export function fetchFailedLoginRule() {
  return request("/rules/failed-login");
}

export function updateFailedLoginRule(payload) {
  return requestWithBody("/rules/failed-login", "PUT", payload);
}

export function fetchSuspiciousProcessRule() {
  return request("/rules/suspicious-process");
}

export function updateSuspiciousProcessRule(payload) {
  return requestWithBody("/rules/suspicious-process", "PUT", payload);
}
