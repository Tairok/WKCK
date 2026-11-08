import { useState } from "react";
import { Loader2, UserPlus } from "lucide-react";
import { useCreateUser, useUsers } from "../api/hooks";
import GlassCard from "../components/GlassCard";
import { renderError, renderLoading } from "../components/PageElements";

const EMPTY_FORM = { username: "", email: "", password: "", password_confirm: "" };

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
      setNotice(`${data.user.username} added.`);
      setForm(EMPTY_FORM);
    } catch {
      // error is shown from createUser.error below
    }
  }

  if (users.isLoading) return renderLoading();
  if (users.isError) return renderError(users.error.message);

  const list = users.data?.users ?? [];

  return (
    <div className="page-stack">
      <GlassCard>
        <div className="label section-title">Add user</div>
        <form onSubmit={submit} className="user-form">
          <input className="text-input" placeholder="Username" value={form.username} onChange={update("username")} required />
          <input className="text-input" type="email" placeholder="Email" value={form.email} onChange={update("email")} required />
          <input className="text-input" type="password" placeholder="Password" value={form.password} onChange={update("password")} required />
          <input
            className="text-input"
            type="password"
            placeholder="Confirm password"
            value={form.password_confirm}
            onChange={update("password_confirm")}
            required
          />
          <div className="user-form-actions">
            <button className="primary-button" disabled={createUser.isPending}>
              {createUser.isPending ? <Loader2 className="spinner-icon" size={16} /> : <UserPlus size={16} />}
              Add user
            </button>
            {notice && <span className="success-message">{notice}</span>}
            {createUser.isError && <span className="error-message">{createUser.error.message}</span>}
          </div>
        </form>
      </GlassCard>

      <GlassCard>
        <div className="label section-title">Accounts</div>
        <ul className="user-list">
          {list.map((u) => (
            <li key={u.id} className="user-row">
              <span className="user-name">{u.username}</span>
              <span className="user-email">{u.email}</span>
              <span className="user-last-login text-subtle">
                last login: {u.last_login ? new Date(u.last_login).toLocaleString() : "never"}
              </span>
            </li>
          ))}
        </ul>
      </GlassCard>
    </div>
  );
}
