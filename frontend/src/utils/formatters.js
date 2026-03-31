// Small UI formatting helpers shared across the dashboard and table views.
export function formatDateTime(value) {
  if (!value) {
    return "N/A";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

export function shortenText(value, limit = 80) {
  if (!value) {
    return "N/A";
  }
  if (value.length <= limit) {
    return value;
  }
  return `${value.slice(0, limit - 3)}...`;
}

export function sortUniqueValues(values) {
  return [...new Set(values.filter(Boolean))].sort((left, right) =>
    String(left).localeCompare(String(right)),
  );
}
