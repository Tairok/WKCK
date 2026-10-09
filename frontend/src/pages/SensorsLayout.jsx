import { NavLink, Outlet } from "react-router-dom";
import { BarChart3, LayoutGrid } from "lucide-react";

const VIEWS = [
  { to: "/sensors", label: "Cards", icon: LayoutGrid, end: true },
  { to: "/sensors/charts", label: "Charts", icon: BarChart3 },
];

export default function SensorsLayout() {
  return (
    <div className="space-y-6">
      <div className="flex rounded-xl border border-white/10 bg-white/5 p-1 text-sm w-fit">
        {VIEWS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-2 rounded-lg px-4 py-2 transition ${
                isActive ? "bg-white/15 text-white" : "text-white/60 hover:text-white"
              }`
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </div>
      <Outlet />
    </div>
  );
}
