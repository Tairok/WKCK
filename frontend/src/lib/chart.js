export const SERIES_COLORS = ["#22d3ee", "#a78bfa", "#34d399", "#fbbf24", "#fb7185", "#60a5fa", "#f472b6", "#a3e635"];

export function sensorId(hardware, key) {
  return `${hardware} / ${key}`;
}

// Merge per-sensor (t, v) pairs onto one shared time axis for uPlot; missing points become null.
export function alignSeries(entries) {
  const xs = [...new Set(entries.flatMap((e) => e.t))].sort((a, b) => a - b);
  const index = new Map(xs.map((x, i) => [x, i]));
  const columns = entries.map((e) => {
    const col = new Array(xs.length).fill(null);
    e.t.forEach((t, i) => {
      col[index.get(t)] = e.v[i];
    });
    return col;
  });
  return [xs, ...columns];
}
