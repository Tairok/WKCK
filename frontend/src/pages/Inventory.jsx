import { useInventory } from "../api/hooks";
import GlassCard from "../components/GlassCard";
import DiskBar from "../components/DiskBar";
import KeyValue from "../components/KeyValue";
import ErrorState from "../components/ErrorState";
import Spinner from "../components/Spinner";
import { formatBytes, mhzText, percentText } from "../lib/format";

const OPTIONAL_SECTIONS = [
  ["Motherboard", "motherboard"],
  ["BIOS", "bios"],
  ["System hardware", "system_hw"],
];

const HIDDEN_KEYS = { system_hw: ["model"] };

function OptionalSection({ title, data, hiddenKeys = [] }) {
  if (data?.error) {
    return (
      <GlassCard>
        <div className="section-title">{title}</div>
        <ErrorState message={data.error} />
      </GlassCard>
    );
  }

  const rows = Array.isArray(data)
    ? data.slice(0, 50).map((item, i) => [item?.name ?? item?.Name ?? `Item ${i + 1}`, item?.value ?? item?.Value ?? ""])
    : Object.entries(data ?? {}).filter(([k, v]) => !hiddenKeys.includes(k) && (v === null || typeof v !== "object"));

  return (
    <GlassCard>
      <div className="section-title">{title}</div>
      <KeyValue rows={rows} />
    </GlassCard>
  );
}

export default function Inventory() {
  const { data, isLoading, isError, error } = useInventory();

  if (isLoading) return <Spinner />;
  if (isError) return <ErrorState message={error.message} />;

  const inv = data?.inventory ?? {};
  const cpu = inv.cpu ?? {};
  const mem = inv.memory ?? {};
  const disks = Array.isArray(inv.disks) ? inv.disks : [];
  const interfaces = Object.entries(inv.network ?? {}).filter(([name]) => name !== "__stats__");
  const optional = OPTIONAL_SECTIONS.filter(([, key]) => inv[key] != null);

  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <GlassCard>
        <div className="section-title">CPU</div>
        <KeyValue
          rows={[
            ["Model", cpu.model],
            ["Physical cores", cpu.physical_cores],
            ["Logical cores", cpu.logical_cores],
            ["Frequency", mhzText(cpu.frequency_mhz)],
            ["Max frequency", mhzText(cpu.frequency_max_mhz)],
            ["Usage", percentText(cpu.usage_percent)],
          ]}
        />
      </GlassCard>

      <GlassCard>
        <div className="section-title">Memory</div>
        <KeyValue
          rows={[
            ["Total", formatBytes(mem.total)],
            ["Used", `${formatBytes(mem.used)} (${percentText(mem.percent)})`],
            ["Available", formatBytes(mem.available)],
            ["Swap total", formatBytes(mem.swap_total)],
            ["Swap used", formatBytes(mem.swap_used)],
          ]}
        />
      </GlassCard>

      <GlassCard className="xl:col-span-2">
        <div className="section-title">Disks</div>
        <div className="grid gap-5 md:grid-cols-2">
          {disks.map((d) => {
            const pct = d.total ? (d.used / d.total) * 100 : 0;
            return (
              <div key={d.device ?? d.mountpoint} className="flex flex-col gap-2">
                <div className="flex justify-between text-sm">
                  <span>
                    {d.mountpoint} <span className="text-white/40">{d.filesystem}</span>
                  </span>
                  <span className="text-white/60">
                    {formatBytes(d.used)} / {formatBytes(d.total)}
                  </span>
                </div>
                <DiskBar percent={pct} />
              </div>
            );
          })}
          {disks.length === 0 && <p className="text-sm text-white/50">No disks reported.</p>}
        </div>
      </GlassCard>

      <GlassCard className="xl:col-span-2">
        <div className="section-title">Network</div>
        <div className="grid gap-4 md:grid-cols-2">
          {interfaces.map(([name, iface]) => (
            <div key={name} className="rounded-xl bg-black/20 p-4">
              <div className="mb-2 text-sm font-medium">{name}</div>
              <div className="flex flex-col gap-1 font-mono text-xs text-white/60">
                {(iface?.addresses ?? []).map((a, i) => (
                  <span key={`${a.address}-${i}`}>{a.address}</span>
                ))}
              </div>
            </div>
          ))}
          {interfaces.length === 0 && <p className="text-sm text-white/50">No interfaces reported.</p>}
        </div>
      </GlassCard>

      {optional.map(([title, key]) => (
        <div key={key} className="xl:col-span-2">
          <OptionalSection title={title} data={inv[key]} hiddenKeys={HIDDEN_KEYS[key]} />
        </div>
      ))}
    </div>
  );
}
