import { AlertTriangle, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { LEVEL_STROKE, LEVEL_TEXT, levelFor, orDash } from "../lib/format";

export function renderLoading() {
  return <div className="loading-indicator"><Loader2 className="spinner-icon" size={28} /></div>;
}

export function renderError(message) {
  return <div className="error-state"><AlertTriangle size={18} /><span>{message}</span></div>;
}

export function renderStatTile(Icon, label, value) {
  return (
    <>
      <div className="stat-tile-icon"><Icon size={20} /></div>
      <div className="stat-tile-content">
        <div className="label stat-tile-label">{label}</div>
        <div className="stat-tile-value">{value ?? "—"}</div>
      </div>
    </>
  );
}

export function renderKeyValueList(rows) {
  return (
    <dl className="key-value-list">
      {rows.map(([key, value]) => (
        <div key={key} className="key-value-row">
          <dt className="label key-value-label">{key}</dt>
          <dd className="key-value-value">{orDash(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

export function renderDiskBar(percent) {
  const value = typeof percent === "number" ? Math.max(0, Math.min(100, percent)) : 0;
  const style = {
    "--disk-fill": LEVEL_STROKE[levelFor("Load", value)],
  };

  return (
    <div className="disk-bar">
      <motion.div
        className="disk-bar-fill"
        style={style}
        initial={{ width: 0 }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      />
    </div>
  );
}

export function renderAlertBadge(level) {
  return (
    <span className={`alert-badge ${level === "critical" ? "alert-badge--critical" : "alert-badge--warning"}`}>
      {level}
    </span>
  );
}

export function levelTextClass(level) {
  return LEVEL_TEXT[level] ?? "level-text--default";
}
