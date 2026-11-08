import { motion } from "framer-motion";
import { LEVEL_STROKE } from "../lib/format";

const RADIUS = 52;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export default function RingGauge({ value, label, sub, level = "ok" }) {
  const pct = typeof value === "number" ? Math.max(0, Math.min(100, value)) : 0;
  const stroke = LEVEL_STROKE[level] ?? LEVEL_STROKE.ok;

  return (
    <div className="ring-gauge">
      <div className="ring-gauge-graphic">
        <svg viewBox="0 0 120 120" className="ring-gauge-svg">
          <circle cx="60" cy="60" r={RADIUS} fill="none" stroke="#FFFFFF14" strokeWidth="10" />
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
        <div className="ring-gauge-value">
          {typeof value === "number" ? `${pct.toFixed(0)}%` : "—"}
        </div>
      </div>
      <div className="ring-gauge-caption">
        <div className="label ring-gauge-label">{label}</div>
        {sub && <div className="ring-gauge-subtitle text-subtle">{sub}</div>}
      </div>
    </div>
  );
}
