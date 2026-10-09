import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { KeyRound, Loader2, Shield } from "lucide-react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import GlassCard from "../components/GlassCard";

const INPUT =
  "w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-white outline-none transition focus:border-cyan-400/60";
const BUTTON =
  "flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-400/90 px-4 py-2 font-medium text-slate-950 transition hover:bg-cyan-300 disabled:opacity-60";

export default function AuthPage() {
  const { status, setUser } = useAuth();
  const navigate = useNavigate();

  const [hasUsers, setHasUsers] = useState(null);
  const [step, setStep] = useState("credentials");
  const [setup, setSetup] = useState(null);
  const [form, setForm] = useState({ username: "", email: "", password: "", password_confirm: "" });
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api("/api/auth/status")
      .then((data) => setHasUsers(data.has_users))
      .catch(() => setHasUsers(true));
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
      const data = isRegister
        ? await api("/api/auth/register", { method: "POST", body: form })
        : await api("/api/auth/login", {
            method: "POST",
            body: { username: form.username, password: form.password },
          });
      setSetup(data.setup_required ? { qr_svg: data.qr_svg, secret: data.secret } : null);
      setStep("mfa");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function submitCode(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const data = await api("/api/auth/mfa/verify", { method: "POST", body: { code } });
      setUser(data.user);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <GlassCard className="w-full max-w-md">
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-xl bg-white/10 p-3 text-cyan-300">
            <Shield size={22} />
          </div>
          <div>
            <h1 className="text-xl font-semibold">BMC Console</h1>
            <p className="text-sm text-white/50">
              {hasUsers === null && "Checking..."}
              {isRegister && "Create the administrator account"}
              {hasUsers === true && "Sign in to continue"}
            </p>
          </div>
        </div>

        {hasUsers !== null && (
          <AnimatePresence mode="wait">
            {step === "credentials" ? (
              <motion.form
                key="credentials"
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -16 }}
                onSubmit={submitCredentials}
                className="flex flex-col gap-4"
              >
                <input className={INPUT} placeholder="Username" value={form.username} onChange={update("username")} required />
                {isRegister && (
                  <input className={INPUT} type="email" placeholder="Email" value={form.email} onChange={update("email")} required />
                )}
                <input className={INPUT} type="password" placeholder="Password" value={form.password} onChange={update("password")} required />
                {isRegister && (
                  <input
                    className={INPUT}
                    type="password"
                    placeholder="Confirm password"
                    value={form.password_confirm}
                    onChange={update("password_confirm")}
                    required
                  />
                )}
                <button className={BUTTON} disabled={busy}>
                  {busy && <Loader2 className="animate-spin" size={16} />}
                  {isRegister ? "Create account" : "Continue"}
                </button>
              </motion.form>
            ) : (
              <motion.form
                key="mfa"
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -16 }}
                onSubmit={submitCode}
                className="flex flex-col gap-4"
              >
                {setup && (
                  <div className="flex flex-col items-center gap-3 rounded-xl bg-white p-4">
                    <div className="h-44 w-44" dangerouslySetInnerHTML={{ __html: setup.qr_svg }} />
                    <div className="break-all text-center font-mono text-xs text-slate-700">{setup.secret}</div>
                  </div>
                )}
                <p className="flex items-center gap-2 text-sm text-white/60">
                  <KeyRound size={16} />
                  {setup ? "Scan the QR code and enter the 6-digit code." : "Enter the code from your authenticator app."}
                </p>
                <input
                  className={`${INPUT} text-center font-mono text-lg tracking-[0.4em]`}
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  maxLength={6}
                  placeholder="000000"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  required
                />
                <button className={BUTTON} disabled={busy}>
                  {busy && <Loader2 className="animate-spin" size={16} />}
                  Verify
                </button>
                <button type="button" className="text-sm text-white/50 hover:text-white" onClick={() => setStep("credentials")}>
                  Back
                </button>
              </motion.form>
            )}
          </AnimatePresence>
        )}

        {error && <p className="mt-4 rounded-xl bg-rose-500/10 px-3 py-2 text-sm text-rose-300">{error}</p>}
      </GlassCard>
    </div>
  );
}
