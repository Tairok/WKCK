import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { useSensors } from "../api/hooks";
import GlassCard from "../components/GlassCard";
import { levelTextClass, renderError, renderLoading } from "../components/PageElements";
import { formatNumber, levelFor, sensorName, sensorType, unitFor } from "../lib/format";

function flattenSensors(sensors) {
  return Object.entries(sensors).flatMap(([hardware, group]) =>
    Object.entries(group ?? {}).map(([key, reading]) => ({
      hardware,
      key,
      type: sensorType(key),
      name: sensorName(key),
      current: reading?.current ?? null,
      min: reading?.min ?? null,
      max: reading?.max ?? null,
    })),
  );
}

export default function Sensors() {
  const { data, isLoading, isError, error } = useSensors();
  const [query, setQuery] = useState("");

  const groups = useMemo(() => {
    const q = query.trim().toLowerCase();
    const items = flattenSensors(data?.sensors ?? {}).filter(
      (s) => !q || `${s.hardware} ${s.key}`.toLowerCase().includes(q),
    );
    const byType = {};
    for (const item of items) (byType[item.type] ??= []).push(item);
    return Object.entries(byType);
  }, [data, query]);

  if (isLoading) return renderLoading();
  if (isError) return renderError(error.message);

  const total = Object.keys(data?.sensors ?? {}).length;
  if (total === 0) {
    return (
      <GlassCard>
        <p className="text-secondary">No sensor readings available. Make sure LibreHardwareMonitor is running.</p>
      </GlassCard>
    );
  }

  return (
    <div className="page-stack">
      <div className="sensor-search">
        <Search size={16} className="sensor-search-icon" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Filter sensors..."
          className="text-input"
        />
      </div>

      {groups.map(([type, items], gi) => (
        <GlassCard key={type} delay={gi * 0.05}>
          <div className="label section-title">
            {type} <span className="text-subtle">({items.length})</span>
          </div>
          <div className="sensor-grid">
            {items.map((s) => {
              const level = levelFor(s.type, s.current);
              return (
                <div key={`${s.hardware}-${s.key}`} className="card card--inset sensor-card">
                  <div className="sensor-hardware text-subtle">{s.hardware}</div>
                  <div className="sensor-name">{s.name}</div>
                  <div className={`sensor-reading ${levelTextClass(level)}`}>
                    {formatNumber(s.current, s.type === "Fan" || s.type === "Clock" ? 0 : 1)}
                    <span className="sensor-unit text-subtle">{unitFor(s.type)}</span>
                  </div>
                  {(s.min !== null || s.max !== null) && (
                    <div className="sensor-range text-subtle">
                      min {formatNumber(s.min)} · max {formatNumber(s.max)}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </GlassCard>
      ))}
    </div>
  );
}
