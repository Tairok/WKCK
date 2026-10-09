export const LEVEL_STROKE = { ok: "#34d399", warning: "#fbbf24", critical: "#fb7185" };
export const LEVEL_TEXT = { ok: "text-emerald-300", warning: "text-amber-300", critical: "text-rose-400" };

const UNITS = {
  Temperature: "°C",
  Fan: "RPM",
  Load: "%",
  Control: "%",
  Level: "%",
  Voltage: "V",
  Power: "W",
  Clock: "MHz",
  Data: "GB",
  Throughput: "KB/s",
};

export function sensorType(key) {
  const i = key.indexOf(":");
  return i > 0 ? key.slice(0, i).trim() : "Other";
}

export function sensorName(key) {
  const i = key.indexOf(":");
  return i > 0 ? key.slice(i + 1).trim() : key;
}

export function unitFor(type) {
  return UNITS[type] ?? "";
}

export function levelFor(type, value) {
  if (typeof value !== "number" || Number.isNaN(value)) return "ok";
  if (type === "Temperature" || ["Load", "Control", "Level"].includes(type)) {
    if (value >= 95) return "critical";
    if (value >= 80) return "warning";
  }
  return "ok";
}

export function formatBytes(bytes) {
  if (typeof bytes !== "number") return "—";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let i = 0;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i += 1;
  }
  return `${value.toFixed(value >= 100 || i === 0 ? 0 : 1)} ${units[i]}`;
}

export function formatUptime(seconds) {
  if (typeof seconds !== "number") return "—";
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d) return `${d} d ${h} h`;
  if (h) return `${h} h ${m} min`;
  return `${m} min`;
}

export function formatNumber(value, digits = 1) {
  return typeof value === "number" ? value.toFixed(digits) : "—";
}

export function orDash(value) {
  return value === null || value === undefined || value === "" ? "—" : value;
}

export function percentText(value) {
  return typeof value === "number" ? `${value.toFixed(1)}%` : null;
}

export function mhzText(value) {
  return typeof value === "number" ? `${value.toFixed(0)} MHz` : null;
}
