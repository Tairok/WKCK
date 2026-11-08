import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Loader2, Shield } from "lucide-react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import GlassCard from "../components/GlassCard";

export default function AuthPage() {
  const { status, setUser } = useAuth();
  const navigate = useNavigate();

  const [hasUsers, setHasUsers] = useState(null);
  const [form, setForm] = useState({ username: "", email: "", password: "", password_confirm: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api("/api/users")
      .then((users) => setHasUsers(users.length > 0))
      .catch((err) => {
        setHasUsers(true);
        setError(err.message);
      });
  }, []);

  useEffect(() => {
    if (status === "in") navigate("/", { replace: true });
  }, [status, navigate]);

  const isRegister = hasUsers === false;
  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  async function submitCredentials(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const users = await api("/api/users");
      const username = form.username.trim();
      let user;

      if (isRegister) {
        if (form.password !== form.password_confirm) {
          throw new Error("Passwords do not match");
        }
        user = await api("/api/users", {
          method: "POST",
          body: {
            username,
            email: form.email.trim(),
            last_login: null,
          },
        });
      } else {
        user = users.find((item) => item.username.toLowerCase() === username.toLowerCase());
        if (!user) throw new Error("Unknown mock account. Use a username from the Users list.");
      }

      setUser(user);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-screen">
      <GlassCard className="auth-card">
        <div className="auth-heading">
          <div className="auth-icon">
            <Shield size={22} />
          </div>
          <div>
            <h1 className="auth-title">BMC Console</h1>
            <p className="auth-subtitle text-subtle">
              {hasUsers === null && "Checking..."}
              {isRegister && "Create the administrator account"}
              {hasUsers === true && "Sign in to continue"}
            </p>
          </div>
        </div>

        {hasUsers !== null && (
          <AnimatePresence mode="wait">
            <motion.form
              key="credentials"
              initial={{ opacity: 0, x: 16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -16 }}
              onSubmit={submitCredentials}
              className="auth-form"
            >
              <input className="auth-input" placeholder="Username" value={form.username} onChange={update("username")} required />
              {isRegister && (
                <input className="auth-input" type="email" placeholder="Email" value={form.email} onChange={update("email")} required />
              )}
              <input className="auth-input" type="password" placeholder="Password (mockup only)" value={form.password} onChange={update("password")} required />
              {isRegister && (
                <input
                  className="auth-input"
                  type="password"
                  placeholder="Confirm password"
                  value={form.password_confirm}
                  onChange={update("password_confirm")}
                  required
                />
              )}
              <button className="auth-submit" disabled={busy}>
                {busy && <Loader2 className="spinner-icon" size={16} />}
                {isRegister ? "Create account" : "Continue"}
              </button>
            </motion.form>
          </AnimatePresence>
        )}

        {error && <p className="auth-error">{error}</p>}
      </GlassCard>
    </div>
  );
}
