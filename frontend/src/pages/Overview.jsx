import { BatteryCharging, Cpu, HardDrive, Layers, MemoryStick, ShieldAlert, Wifi } from "lucide-react";
import { useHealthSummary, useInfo, useInventory } from "../api/hooks";
import GlassCard from "../components/GlassCard";
import RingGauge from "../components/RingGauge";
import { renderError, renderLoading, renderStatTile } from "../components/PageElements";
import { formatBytes, formatUptime, levelFor } from "../lib/format";
import "../styles/index.css";

export default function Overview() {
  const info = useInfo();
  const inventory = useInventory();
  const health = useHealthSummary();

  if (info.isLoading || inventory.isLoading) {
    return renderLoading();
  }
  if (info.isError && inventory.isError) {
    return renderError("Could not load data from the server.");
  }

  const system = info.data?.system ?? {};
  const inv = inventory.data?.inventory ?? {};
  const cpu = inv.cpu ?? {};
  const mem = inv.memory ?? {};
  const disks = Array.isArray(inv.disks) ? inv.disks : [];
  const fullest = disks.reduce((best, d) => {
    const pct = d.total ? (d.used / d.total) * 100 : 0;
    return !best || pct > best.pct ? { name: d.mountpoint ?? d.device, pct } : best;
  }, null);
  const net = inv.network?.__stats__ ?? {};

  const cpuPct = typeof cpu.usage_percent === "number" ? cpu.usage_percent : null;
  const ramPct = typeof mem.percent === "number" ? mem.percent : null;

  return (
    <div className="page-stack">
      <GlassCard>
        <div className="host-summary">
          <div>
            <div className="label section-title section-title--compact">Host</div>
            <div className="host-name">{system.hostname ?? "—"}</div>
            <div className="host-platform text-secondary">{system.platform ?? system.os ?? ""}</div>
          </div>
          <div className="host-meta text-muted">
            <div>
              Uptime <span className="host-meta-value">{formatUptime(system.uptime_seconds)}</span>
            </div>
            <div>Architecture {system.architecture ?? "—"}</div>
          </div>
        </div>
      </GlassCard>

      <div className="overview-gauges">
        <GlassCard delay={0.05} className="gauge-card">
          <RingGauge value={cpuPct} label="CPU" sub={cpu.model} level={levelFor("Load", cpuPct)} />
        </GlassCard>
        <GlassCard delay={0.1} className="gauge-card">
          <RingGauge
            value={ramPct}
            label="Memory"
            sub={`${formatBytes(mem.used)} / ${formatBytes(mem.total)}`}
            level={levelFor("Load", ramPct)}
          />
        </GlassCard>
        <GlassCard delay={0.15} className="gauge-card">
          <RingGauge
            value={fullest?.pct ?? null}
            label="Fullest disk"
            sub={fullest?.name}
            level={levelFor("Load", fullest?.pct)}
          />
        </GlassCard>
      </div>

      <div className="overview-metrics">
        {[
          { icon: Layers, label: "Logical cores", value: cpu.logical_cores ?? "—" },
          { icon: Cpu, label: "Frequency", value: typeof cpu.frequency_mhz === "number" ? `${cpu.frequency_mhz.toFixed(0)} MHz` : "—" },
          { icon: MemoryStick, label: "Swap used", value: formatBytes(mem.swap_used) },
          { icon: ShieldAlert, label: "Active alerts", value: health.data?.total_alerts ?? "—" },
        ].map(({ icon: Icon, label, value }) => (
          <GlassCard key={label} className="stat-tile">{renderStatTile(Icon, label, value)}</GlassCard>
        ))}
      </div>
    </div>
  );
}
