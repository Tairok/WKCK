import { useState } from "react";
import { UserPlus, Loader2 } from "lucide-react";
import { useCreateUser, useUsers } from "../api/hooks";
import GlassCard from "../components/GlassCard";
import ErrorState from "../components/ErrorState";
import Spinner from "../components/Spinner";

const INPUT =
  "w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-white outline-none transition focus:border-cyan-400/60";
const BUTTON =
  "flex items-center justify-center gap-2 rounded-xl bg-cyan-400/90 px-4 py-2 font-medium text-slate-950 transition hover:bg-cyan-300 disabled:opacity-60";
const EMPTY_FORM = { username: "", email: "", password: "", password_confirm: "" };

function MfaBadge({ enabled }) {
  const cls = enabled ? "bg-emerald-500/15 text-emerald-300" : "bg-amber-500/15 text-amber-300";
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {enabled ? "MFA active" : "MFA pending"}
    </span>
  );
}

export default function Users() {
  const users = useUsers();
  const createUser = useCreateUser();
  const [form, setForm] = useState(EMPTY_FORM);
  const [notice, setNotice] = useState("");

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setNotice("");
    try {
      const data = await createUser.mutateAsync(form);
      setNotice(`${data.user.username} added. They will set up MFA at first login.`);
      setForm(EMPTY_FORM);
    } catch {
      // error is shown from createUser.error below
    }
  }

  if (users.isLoading) return <Spinner />;
  if (users.isError) return <ErrorState message={users.error.message} />;

  const list = users.data?.users ?? [];

  return (
    <div className="space-y-6">
      <GlassCard>
        <div className="section-title">Add user</div>
        <form onSubmit={submit} className="grid gap-4 md:grid-cols-2">
          <input className={INPUT} placeholder="Username" value={form.username} onChange={update("username")} required />
          <input className={INPUT} type="email" placeholder="Email" value={form.email} onChange={update("email")} required />
          <input className={INPUT} type="password" placeholder="Password" value={form.password} onChange={update("password")} required />
          <input
            className={INPUT}
            type="password"
            placeholder="Confirm password"
            value={form.password_confirm}
            onChange={update("password_confirm")}
            required
          />
          <div className="flex flex-wrap items-center gap-4 md:col-span-2">
            <button className={BUTTON} disabled={createUser.isPending}>
              {createUser.isPending ? <Loader2 className="animate-spin" size={16} /> : <UserPlus size={16} />}
              Add user
            </button>
            {notice && <span className="text-sm text-emerald-300">{notice}</span>}
            {createUser.isError && <span className="text-sm text-rose-300">{createUser.error.message}</span>}
          </div>
        </form>
      </GlassCard>

      <GlassCard>
        <div className="section-title">Accounts</div>
        <ul className="flex flex-col divide-y divide-white/5 text-sm">
          {list.map((u) => (
            <li key={u.id} className="flex flex-wrap items-center justify-between gap-3 py-2">
              <span className="font-medium">{u.username}</span>
              <span className="flex-1 truncate text-white/60">{u.email}</span>
              <span className="text-xs text-white/50">
                last login: {u.last_login ? new Date(u.last_login).toLocaleString() : "never"}
              </span>
              <MfaBadge enabled={!!u.totp_enabled} />
            </li>
          ))}
        </ul>
      </GlassCard>
    </div>
  );
}
