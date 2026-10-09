import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { useSensorSeries, useSensors } from "../api/hooks";
import GlassCard from "../components/GlassCard";
import TimeSeriesChart from "../components/TimeSeriesChart";
import ErrorState from "../components/ErrorState";
import Spinner from "../components/Spinner";
import { SERIES_COLORS, alignSeries, sensorId } from "../lib/chart";
import { formatNumber, sensorName, sensorType, unitFor } from "../lib/format";

const WINDOWS = [
  { label: "1 h", seconds: 3600 },
  { label: "24 h", seconds: 86400 },
];
const MAX_SELECTED = 8;
const DEFAULT_TYPES = ["Temperature", "Load"];

function flattenSensors(sensors) {
  return Object.entries(sensors).flatMap(([hardware, group]) =>
    Object.entries(group ?? {})
      .filter(([, reading]) => typeof reading?.current === "number")
      .map(([key, reading]) => ({
        id: sensorId(hardware, key),
        hardware,
        type: sensorType(key),
        name: sensorName(key),
        current: reading.current,
      })),
  );
}

export default function SensorCharts() {
  const sensors = useSensors();
  const items = useMemo(() => flattenSensors(sensors.data?.sensors ?? {}), [sensors.data]);
  const byId = useMemo(() => new Map(items.map((i) => [i.id, i])), [items]);

  const [windowSeconds, setWindowSeconds] = useState(3600);
  const [selected, setSelected] = useState(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (selected === null && items.length > 0) {
      const preferred = [...items.filter((i) => DEFAULT_TYPES.includes(i.type)), ...items];
      setSelected([...new Set(preferred.map((i) => i.id))].slice(0, 4));
    }
  }, [items, selected]);

  const ids = selected ?? [];
  const series = useSensorSeries(windowSeconds, ids);

  const chartSeries = ids.map((id, i) => {
    const item = byId.get(id);
    return {
      id,
      label: item ? `${item.name} (${item.hardware})` : id,
      color: SERIES_COLORS[i % SERIES_COLORS.length],
    };
  });

  const chartData = useMemo(
    () => alignSeries(ids.map((id) => series.data?.series?.[id] ?? { t: [], v: [] })),
    [ids.join("|"), series.data], // eslint-disable-line react-hooks/exhaustive-deps
  );

  const hasPoints = chartData[0]?.length > 0;

  function toggle(id) {
    setSelected((prev) => {
      const current = prev ?? [];
      if (current.includes(id)) return current.filter((x) => x !== id);
      if (current.length >= MAX_SELECTED) return current;
      return [...current, id];
    });
  }

  if (sensors.isLoading) return <Spinner />;
  if (sensors.isError) return <ErrorState message={sensors.error.message} />;
  if (items.length === 0) {
    return (
      <GlassCard>
        <p className="text-white/70">No numeric sensor readings yet. Make sure LibreHardwareMonitor is running.</p>
      </GlassCard>
    );
  }

  const q = query.trim().toLowerCase();
  const pickable = items.filter((i) => !q || `${i.hardware} ${i.name} ${i.type}`.toLowerCase().includes(q));
  const grouped = pickable.reduce((acc, item) => {
    (acc[item.type] ??= []).push(item);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex rounded-xl border border-white/10 bg-white/5 p-1 text-sm">
          {WINDOWS.map((w) => (
            <button
              key={w.seconds}
              type="button"
              onClick={() => setWindowSeconds(w.seconds)}
              className={`rounded-lg px-3 py-1.5 transition ${
                windowSeconds === w.seconds ? "bg-white/15 text-white" : "text-white/60 hover:text-white"
              }`}
            >
              {w.label}
            </button>
          ))}
        </div>
        <span className="text-xs text-white/40">Live · refreshes every 1 s · {ids.length}/{MAX_SELECTED} selected</span>
      </div>

      <GlassCard>
        {series.isError && <ErrorState message={series.error.message} />}
        {!series.isError && ids.length === 0 && (
          <p className="py-16 text-center text-white/50">Select sensors below to plot them.</p>
        )}
        {!series.isError && ids.length > 0 && !hasPoints && (
          <p className="py-16 text-center text-white/50">Collecting data... the first points appear within a few seconds.</p>
        )}
        {!series.isError && ids.length > 0 && hasPoints && (
          <TimeSeriesChart data={chartData} series={chartSeries} />
        )}

        {ids.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm">
            {chartSeries.map((s) => {
              const item = byId.get(s.id);
              return (
                <div key={s.id} className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: s.color }} />
                  <span className="text-white/70">{s.label}</span>
                  <span className="font-medium tabular-nums">
                    {formatNumber(item?.current, item?.type === "Fan" || item?.type === "Clock" ? 0 : 1)}
                    {unitFor(item?.type) && <span className="ml-1 text-white/40">{unitFor(item?.type)}</span>}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </GlassCard>

      <GlassCard>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
          <div className="section-title !mb-0">Sensors</div>
          <div className="relative w-full max-w-xs">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter..."
              className="w-full rounded-xl border border-white/10 bg-black/30 py-2 pl-9 pr-3 text-sm outline-none focus:border-cyan-400/60"
            />
          </div>
        </div>
        <div className="flex flex-col gap-4">
          {Object.entries(grouped).map(([type, list]) => (
            <div key={type}>
              <div className="mb-2 text-xs uppercase tracking-wide text-white/40">{type}</div>
              <div className="flex flex-wrap gap-2">
                {list.map((item) => {
                  const active = ids.includes(item.id);
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => toggle(item.id)}
                      title={item.hardware}
                      className={`rounded-full border px-3 py-1 text-xs transition ${
                        active
                          ? "border-cyan-400/60 bg-cyan-400/15 text-white"
                          : "border-white/10 text-white/60 hover:border-white/30 hover:text-white"
                      }`}
                    >
                      {item.name}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}
