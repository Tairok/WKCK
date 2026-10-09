import { orDash } from "../lib/format";

export default function KeyValue({ rows }) {
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
      {rows.map(([key, value]) => (
        <div key={key} className="contents">
          <dt className="text-white/50">{key}</dt>
          <dd className="break-all text-white">{orDash(value)}</dd>
        </div>
      ))}
    </dl>
  );
}
