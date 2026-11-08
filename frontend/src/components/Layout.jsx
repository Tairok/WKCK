import { NavLink, Outlet, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Cpu, LayoutDashboard, LogOut, ShieldAlert, Thermometer, Users } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { useInfo } from "../api/hooks";

const NAV = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/inventory", label: "Inventory", icon: Cpu },
  { to: "/sensors", label: "Sensors", icon: Thermometer },
  { to: "/health", label: "Health", icon: ShieldAlert },
  { to: "/users", label: "Users", icon: Users },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();
  const info = useInfo();
  const hostname = info.data?.system?.hostname ?? "connecting...";

  return (
    <div className="app-layout">
      <aside className="app-sidebar">
        <div>
          <div className="brand-title">BMC Console</div>
          <div className="brand-host">{hostname}</div>
        </div>

        <nav className="primary-nav">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => `nav-link${isActive ? " nav-link--active" : ""}`}
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="account-panel">
          <div className="account-label">Signed in as {user?.username}</div>
          <button
            onClick={logout}
            className="sign-out-button"
          >
            <LogOut size={16} />
            Sign out
          </button>
        </div>
      </aside>

      <main className="page-main">
        <AnimatePresence mode="wait">
          <motion.div
            className="page-transition"
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
