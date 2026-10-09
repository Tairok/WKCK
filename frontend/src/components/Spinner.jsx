import { Loader2 } from "lucide-react";

export default function Spinner() {
  return (
    <div className="flex justify-center p-12 text-white/60">
      <Loader2 className="animate-spin" size={28} />
    </div>
  );
}
