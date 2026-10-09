import AnimatedNumber from "./AnimatedNumber";
import GlassCard from "./GlassCard";

export default function StatTile({ icon: Icon, label, value, suffix = "", decimals = 0, text, delay = 0 }) {
  return (
    <GlassCard delay={delay} className="flex items-center gap-4 p-4">
      <div className="rounded-xl bg-white/10 p-3 text-cyan-300">
        <Icon size={20} />
      </div>
      <div className="min-w-0">
        <div className="text-xs uppercase tracking-wide text-white/50">{label}</div>
        <div className="truncate text-xl font-semibold">
          {text ?? <AnimatedNumber value={value} decimals={decimals} suffix={suffix} />}
        </div>
      </div>
    </GlassCard>
  );
}
