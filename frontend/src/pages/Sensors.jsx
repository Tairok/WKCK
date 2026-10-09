import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { useSensors } from "../api/hooks";
import GlassCard from "../components/GlassCard";
import ErrorState from "../components/ErrorState";
import Spinner from "../components/Spinner";
import { LEVEL_TEXT, formatNumber, levelFor, sensorName, sensorType, unitFor } from "../lib/format";

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

  if (isLoading) return <Spinner />;
  if (isError) return <ErrorState message={error.message} />;

  const total = Object.keys(data?.sensors ?? {}).length;
  if (total === 0) {
    return (
      <GlassCard>
        <p className="text-white/70">No sensor readings available. Make sure LibreHardwareMonitor is running.</p>
      </GlassCard>
    );
  }

  return (
    <div className="space-y-6">
      <div className="relative max-w-sm">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Filter sensors..."
          className="w-full rounded-xl border border-white/10 bg-black/30 py-2 pl-9 pr-3 text-sm outline-none focus:border-cyan-400/60"
        />
      </div>

      {groups.map(([type, items], gi) => (
        <GlassCard key={type} delay={gi * 0.05}>
          <div className="section-title">
            {type} <span className="text-white/30">({items.length})</span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {items.map((s) => {
              const level = levelFor(s.type, s.current);
              return (
                <div key={`${s.hardware}-${s.key}`} className="rounded-xl bg-black/20 p-4">
                  <div className="truncate text-xs text-white/50">{s.hardware}</div>
                  <div className="truncate text-sm font-medium">{s.name}</div>
                  <div className={`mt-2 text-2xl font-semibold tabular-nums ${LEVEL_TEXT[level]}`}>
                    {formatNumber(s.current, s.type === "Fan" || s.type === "Clock" ? 0 : 1)}
                    <span className="ml-1 text-sm font-normal text-white/50">{unitFor(s.type)}</span>
                  </div>
                  {(s.min !== null || s.max !== null) && (
                    <div className="mt-1 text-xs text-white/40">
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
