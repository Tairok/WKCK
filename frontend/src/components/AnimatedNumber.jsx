import { animate } from "framer-motion";
import { useEffect, useRef, useState } from "react";

export default function AnimatedNumber({ value, decimals = 0, suffix = "" }) {
  const [display, setDisplay] = useState(typeof value === "number" ? value : 0);
  const previous = useRef(typeof value === "number" ? value : 0);

  useEffect(() => {
    if (typeof value !== "number") return undefined;
    const controls = animate(previous.current, value, {
      duration: 0.6,
      onUpdate: (v) => setDisplay(v),
    });
    previous.current = value;
    return () => controls.stop();
  }, [value]);

  if (typeof value !== "number") return <span>—</span>;
  return (
    <span>
      {display.toFixed(decimals)}
      {suffix}
    </span>
  );
}
