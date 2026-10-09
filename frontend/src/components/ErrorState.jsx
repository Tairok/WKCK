import { AlertTriangle } from "lucide-react";

export default function ErrorState({ message }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-rose-400/30 bg-rose-500/10 p-4 text-sm text-rose-200">
      <AlertTriangle size={18} />
      <span>{message}</span>
    </div>
  );
}
