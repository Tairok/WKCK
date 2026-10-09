import { BatteryCharging, Cpu, HardDrive, Layers, MemoryStick, ShieldAlert, Wifi } from "lucide-react";
import { useHealthSummary, useInfo, useInventory } from "../api/hooks";
import GlassCard from "../components/GlassCard";
import RingGauge from "../components/RingGauge";
import StatTile from "../components/StatTile";
import ErrorState from "../components/ErrorState";
import Spinner from "../components/Spinner";
import { formatBytes, formatUptime, levelFor } from "../lib/format";

export default function Overview() {
  const info = useInfo();
  const inventory = useInventory();
  const health = useHealthSummary();

  if (info.isLoading || inventory.isLoading) return <Spinner />;
  if (info.isError && inventory.isError) return <ErrorState message="Could not load data from the server." />;

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
    <div className="space-y-6">
      <GlassCard>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="section-title !mb-1">Host</div>
            <div className="text-3xl font-semibold">{system.hostname ?? "—"}</div>
            <div className="text-sm text-white/60">{system.platform ?? system.os ?? ""}</div>
          </div>
          <div className="text-right text-sm text-white/60">
            <div>
              Uptime <span className="text-white">{formatUptime(system.uptime_seconds)}</span>
            </div>
            <div>Architecture {system.architecture ?? "—"}</div>
          </div>
        </div>
      </GlassCard>

      <div className="grid gap-6 md:grid-cols-3">
        <GlassCard delay={0.05} className="flex justify-center">
          <RingGauge value={cpuPct} label="CPU" sub={cpu.model} level={levelFor("Load", cpuPct)} />
        </GlassCard>
        <GlassCard delay={0.1} className="flex justify-center">
          <RingGauge
            value={ramPct}
            label="Memory"
            sub={`${formatBytes(mem.used)} / ${formatBytes(mem.total)}`}
            level={levelFor("Load", ramPct)}
          />
        </GlassCard>
        <GlassCard delay={0.15} className="flex justify-center">
          <RingGauge
            value={fullest?.pct ?? null}
            label="Fullest disk"
            sub={fullest?.name}
            level={levelFor("Load", fullest?.pct)}
          />
        </GlassCard>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatTile icon={Layers} label="Logical cores" value={cpu.logical_cores ?? null} delay={0.2} />
        <StatTile icon={Cpu} label="Frequency" text={typeof cpu.frequency_mhz === "number" ? `${cpu.frequency_mhz.toFixed(0)} MHz` : "—"} delay={0.25} />
        <StatTile icon={Wifi} label="Received" text={formatBytes(net.bytes_recv)} delay={0.3} />
        <StatTile icon={Wifi} label="Sent" text={formatBytes(net.bytes_sent)} delay={0.35} />
        {typeof inv.battery?.percent === "number" && (
          <StatTile icon={BatteryCharging} label="Battery" value={inv.battery.percent} suffix="%" delay={0.4} />
        )}
        <StatTile icon={MemoryStick} label="Swap used" text={formatBytes(mem.swap_used)} delay={0.45} />
        <StatTile icon={HardDrive} label="Disks" value={disks.length} delay={0.5} />
        <StatTile icon={ShieldAlert} label="Active alerts" value={health.data?.total_alerts ?? null} delay={0.55} />
      </div>
    </div>
  );
}
