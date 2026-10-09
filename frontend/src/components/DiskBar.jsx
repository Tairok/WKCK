import { motion } from "framer-motion";
import { LEVEL_STROKE, levelFor } from "../lib/format";

export default function DiskBar({ percent }) {
  const pct = typeof percent === "number" ? Math.max(0, Math.min(100, percent)) : 0;
  const color = LEVEL_STROKE[levelFor("Load", pct)];

  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
      <motion.div
        className="h-full rounded-full"
        style={{ background: color }}
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      />
    </div>
  );
}
