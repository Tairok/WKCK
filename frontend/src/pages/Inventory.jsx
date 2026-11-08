import { useInventory } from "../api/hooks";
import GlassCard from "../components/GlassCard";
import { renderDiskBar, renderError, renderKeyValueList, renderLoading } from "../components/PageElements";
import { formatBytes, mhzText, percentText } from "../lib/format";

const OPTIONAL_SECTIONS = [
  ["Motherboard", "motherboard"],
  ["BIOS", "bios"],
  ["System hardware", "system_hw"],
];

const HIDDEN_KEYS = { system_hw: ["model"] };

function renderOptionalSection(title, data, hiddenKeys = []) {
  if (data?.error) {
    return (
      <GlassCard>
        <div className="label section-title">{title}</div>
        {renderError(data.error)}
      </GlassCard>
    );
  }

  const rows = Array.isArray(data)
    ? data.slice(0, 50).map((item, i) => [item?.name ?? item?.Name ?? `Item ${i + 1}`, item?.value ?? item?.Value ?? ""])
    : Object.entries(data ?? {}).filter(([k, v]) => !hiddenKeys.includes(k) && (v === null || typeof v !== "object"));

  return (
    <GlassCard>
      <div className="label section-title">{title}</div>
      {renderKeyValueList(rows)}
    </GlassCard>
  );
}

export default function Inventory() {
  const { data, isLoading, isError, error } = useInventory();

  if (isLoading) return renderLoading();
  if (isError) return renderError(error.message);

  const inv = data?.inventory ?? {};
  const cpu = inv.cpu ?? {};
  const mem = inv.memory ?? {};
  const disks = Array.isArray(inv.disks) ? inv.disks : [];
  const interfaces = Object.entries(inv.network ?? {}).filter(([name]) => name !== "__stats__");
  const optional = OPTIONAL_SECTIONS.filter(([, key]) => inv[key] != null);
  return (
    <div className="inventory-grid">
      <GlassCard>
        <div className="label section-title">CPU</div>
        {renderKeyValueList([
            ["Model", cpu.model],
            ["Physical cores", cpu.physical_cores],
            ["Logical cores", cpu.logical_cores],
            ["Frequency", mhzText(cpu.frequency_mhz)],
            ["Max frequency", mhzText(cpu.frequency_max_mhz)],
            ["Usage", percentText(cpu.usage_percent)],
          ])}
      </GlassCard>

      <GlassCard>
        <div className="label section-title">Memory</div>
        {renderKeyValueList([
            ["Total", formatBytes(mem.total)],
            ["Used", `${formatBytes(mem.used)} (${percentText(mem.percent)})`],
            ["Available", formatBytes(mem.available)],
            ["Swap total", formatBytes(mem.swap_total)],
            ["Swap used", formatBytes(mem.swap_used)],
          ])}
      </GlassCard>

      <GlassCard className="inventory-wide">
        <div className="label section-title">Disks</div>
        <div className="disk-list">
          {disks.map((d) => {
            const pct = d.total ? (d.used / d.total) * 100 : 0;
            return (
              <div key={d.device ?? d.mountpoint} className="disk-item">
                <div className="disk-item-heading">
                  <span>
                    {d.mountpoint} <span className="text-secondary">{d.filesystem}</span>
                  </span>
                  <span className="text-muted">
                    {formatBytes(d.used)} / {formatBytes(d.total)}
                  </span>
                </div>
                {renderDiskBar(pct)}
              </div>
            );
          })}
          {disks.length === 0 && <p className="text-muted">No disks reported.</p>}
        </div>
      </GlassCard>

      <GlassCard className="inventory-wide">
        <div className="label section-title">Network</div>
        <div className="network-list">
          {interfaces.map(([name, iface]) => (
            <div key={name} className="card card--inset network-interface">
              <div className="label network-interface-name">{name}</div>
              <div className="network-addresses text-subtle">
                {(iface?.addresses ?? []).map((a, i) => (
                  <span key={`${a.address}-${i}`}>{a.address}</span>
                ))}
              </div>
            </div>
          ))}
          {interfaces.length === 0 && <p className="text-muted">No interfaces reported.</p>}
        </div>
      </GlassCard>

      {optional.map(([title, key]) => (
        <div key={key} className="inventory-wide">
          {renderOptionalSection(title, inv[key], HIDDEN_KEYS[key])}
        </div>
      ))}
    </div>
  );
}
