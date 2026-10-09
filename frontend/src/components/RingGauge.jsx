import { motion } from "framer-motion";
import { LEVEL_STROKE } from "../lib/format";

const RADIUS = 52;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export default function RingGauge({ value, label, sub, level = "ok" }) {
  const pct = typeof value === "number" ? Math.max(0, Math.min(100, value)) : 0;
  const stroke = LEVEL_STROKE[level] ?? LEVEL_STROKE.ok;

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative h-36 w-36">
        <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
          <circle cx="60" cy="60" r={RADIUS} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="10" />
          <motion.circle
            cx="60"
            cy="60"
            r={RADIUS}
            fill="none"
            stroke={stroke}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            initial={{ strokeDashoffset: CIRCUMFERENCE }}
            animate={{ strokeDashoffset: CIRCUMFERENCE * (1 - pct / 100) }}
            transition={{ duration: 0.9, ease: "easeOut" }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center text-2xl font-semibold">
          {typeof value === "number" ? `${pct.toFixed(0)}%` : "—"}
        </div>
      </div>
      <div className="text-center">
        <div className="text-sm font-medium text-white/90">{label}</div>
        {sub && <div className="max-w-[12rem] truncate text-xs text-white/50">{sub}</div>}
      </div>
    </div>
  );
}
