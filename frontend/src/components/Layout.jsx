import { NavLink, Outlet, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Cpu, LayoutDashboard, LogOut, ShieldAlert, Thermometer } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { useInfo } from "../api/hooks";

const NAV = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/inventory", label: "Inventory", icon: Cpu },
  { to: "/sensors", label: "Sensors", icon: Thermometer },
  { to: "/health", label: "Health", icon: ShieldAlert },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();
  const info = useInfo();
  const hostname = info.data?.system?.hostname ?? "connecting...";

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <aside className="flex flex-col gap-6 border-b border-white/10 bg-white/5 p-6 backdrop-blur-xl md:w-64 md:border-b-0 md:border-r">
        <div>
          <div className="text-lg font-semibold">BMC Console</div>
          <div className="truncate text-xs text-white/50">{hostname}</div>
        </div>

        <nav className="flex flex-wrap gap-1 md:flex-col">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition ${
                  isActive ? "bg-white/10 text-white" : "text-white/60 hover:bg-white/5 hover:text-white"
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto hidden flex-col gap-3 md:flex">
          <div className="text-xs text-white/50">Signed in as {user?.username}</div>
          <button
            onClick={logout}
            className="flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-white/70 transition hover:bg-white/10"
          >
            <LogOut size={16} />
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 p-6 md:p-10">
        <AnimatePresence mode="wait">
          <motion.div
            key={pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
