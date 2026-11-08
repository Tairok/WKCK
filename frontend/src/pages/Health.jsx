import { Activity, AlertTriangle, CheckCircle2, ShieldAlert } from "lucide-react";
import { useAlertHistory, useHealthAnalysis, useHealthSummary } from "../api/hooks";
import GlassCard from "../components/GlassCard";
import { renderAlertBadge, renderError, renderLoading, renderStatTile, levelTextClass } from "../components/PageElements";

export default function Health() {
  const summary = useHealthSummary();
  const analysis = useHealthAnalysis();
  const history = useAlertHistory();

  if (summary.isLoading || analysis.isLoading) {
    return renderLoading();
  }
  if (summary.isError) {
    return renderError(summary.error.message);
  }

  const components = Object.entries(analysis.data?.components ?? {});
  const past = history.data?.history ?? [];

  return (
    <div className="page-stack">
      <div className="health-summary-grid">
        {[
          { icon: ShieldAlert, label: "Total alerts", value: summary.data?.total_alerts },
          { icon: AlertTriangle, label: "Critical", value: summary.data?.critical_count },
          { icon: Activity, label: "Components affected", value: summary.data?.components_with_alerts },
        ].map(({ icon: Icon, label, value }) => (
          <GlassCard key={label} className="stat-tile">{renderStatTile(Icon, label, value)}</GlassCard>
        ))}
      </div>

      <GlassCard>
        <div className="label section-title">Current status</div>
        {components.length === 0 ? (
          <div className="healthy-state">
            <CheckCircle2 size={20} />
            All monitored components are within thresholds.
          </div>
        ) : (
          <div className="health-component-grid">
            {components.map(([name, comp]) => (
              <div key={name} className="card card--inset health-component-card">
                <div className="health-component-header">
                  <span className="label health-component-name">{name}</span>
                  <span className="text-muted">{comp.count} alert(s)</span>
                </div>
                <ul className="health-alert-list">
                  {(comp.alerts ?? []).map((a, i) => (
                    <li key={`${a.sensor}-${i}`} className="health-alert-item">
                      <span className={levelTextClass(a.level)}>{a.message}</span>
                      {renderAlertBadge(a.level)}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      <GlassCard>
        <div className="label section-title">Recent alert history</div>
        {past.length === 0 ? (
          <p className="text-muted">No alerts recorded in the database yet.</p>
        ) : (
          <ul className="alert-history-list">
            {past.map((h, i) => (
              <li key={h.id ?? i} className="alert-history-row">
                <span className="text-muted">{h.timestamp}</span>
                <span className="alert-history-message">{h.message}</span>
                {h.level && renderAlertBadge(h.level)}
              </li>
            ))}
          </ul>
        )}
      </GlassCard>
    </div>
  );
}
