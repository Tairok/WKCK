import { Activity, AlertTriangle, CheckCircle2, ShieldAlert } from "lucide-react";
import { useAlertHistory, useHealthAnalysis, useHealthSummary } from "../api/hooks";
import GlassCard from "../components/GlassCard";
import StatTile from "../components/StatTile";
import ErrorState from "../components/ErrorState";
import Spinner from "../components/Spinner";
import { LEVEL_TEXT } from "../lib/format";

function LevelBadge({ level }) {
  const cls = level === "critical" ? "bg-rose-500/15 text-rose-300" : "bg-amber-500/15 text-amber-300";
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium uppercase ${cls}`}>{level}</span>;
}

export default function Health() {
  const summary = useHealthSummary();
  const analysis = useHealthAnalysis();
  const history = useAlertHistory();

  if (summary.isLoading || analysis.isLoading) return <Spinner />;
  if (summary.isError) return <ErrorState message={summary.error.message} />;

  const components = Object.entries(analysis.data?.components ?? {});
  const past = history.data?.history ?? [];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <StatTile icon={ShieldAlert} label="Total alerts" value={summary.data?.total_alerts ?? null} />
        <StatTile icon={AlertTriangle} label="Critical" value={summary.data?.critical_count ?? null} delay={0.05} />
        <StatTile icon={Activity} label="Components affected" value={summary.data?.components_with_alerts ?? null} delay={0.1} />
      </div>

      <GlassCard>
        <div className="section-title">Current status</div>
        {components.length === 0 ? (
          <div className="flex items-center gap-3 text-emerald-300">
            <CheckCircle2 size={20} />
            All monitored components are within thresholds.
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {components.map(([name, comp]) => (
              <div key={name} className="rounded-xl bg-black/20 p-4">
                <div className="mb-3 flex items-center justify-between">
                  <span className="font-medium">{name}</span>
                  <span className="text-xs text-white/50">{comp.count} alert(s)</span>
                </div>
                <ul className="flex flex-col gap-2">
                  {(comp.alerts ?? []).map((a, i) => (
                    <li key={`${a.sensor}-${i}`} className="flex items-start justify-between gap-3 text-sm">
                      <span className={LEVEL_TEXT[a.level] ?? "text-white/80"}>{a.message}</span>
                      <LevelBadge level={a.level} />
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      <GlassCard>
        <div className="section-title">Recent alert history</div>
        {past.length === 0 ? (
          <p className="text-sm text-white/50">No alerts recorded in the database yet.</p>
        ) : (
          <ul className="flex flex-col divide-y divide-white/5 text-sm">
            {past.map((h, i) => (
              <li key={h.id ?? i} className="flex flex-wrap items-center justify-between gap-3 py-2">
                <span className="text-white/60">{h.timestamp}</span>
                <span className="flex-1 truncate">{h.message}</span>
                {h.level && <LevelBadge level={h.level} />}
              </li>
            ))}
          </ul>
        )}
      </GlassCard>
    </div>
  );
}
