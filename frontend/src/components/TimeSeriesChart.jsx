import { useEffect, useRef } from "react";
import uPlot from "uplot";
import "uplot/dist/uPlot.min.css";

const AXIS = {
  stroke: "rgba(248,250,252,0.5)",
  grid: { stroke: "rgba(255,255,255,0.06)" },
  ticks: { stroke: "rgba(255,255,255,0.1)" },
};

export default function TimeSeriesChart({ data, series, height = 340 }) {
  const containerRef = useRef(null);
  const plotRef = useRef(null);
  const seriesKey = series.map((s) => s.label).join("|");

  useEffect(() => {
    const el = containerRef.current;
    const plot = new uPlot(
      {
        width: el.clientWidth,
        height,
        scales: { x: { time: true } },
        cursor: { drag: { x: true, y: false } },
        axes: [AXIS, AXIS],
        series: [
          {},
          ...series.map((s) => ({ label: s.label, stroke: s.color, width: 2, spanGaps: true })),
        ],
      },
      data,
      el,
    );
    plotRef.current = plot;

    const observer = new ResizeObserver(() => plot.setSize({ width: el.clientWidth, height }));
    observer.observe(el);

    return () => {
      observer.disconnect();
      plot.destroy();
      plotRef.current = null;
    };
    // The plot is rebuilt only when the set of series changes; data updates go through setData below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seriesKey, height]);

  useEffect(() => {
    plotRef.current?.setData(data);
  }, [data]);

  return <div ref={containerRef} className="w-full" />;
}
