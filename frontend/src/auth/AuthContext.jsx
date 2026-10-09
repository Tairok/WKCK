import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../api/client";
import Spinner from "../components/Spinner";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState({ status: "loading", user: null });

  useEffect(() => {
    api("/api/auth/me")
      .then((data) => setAuth({ status: "in", user: data.user }))
      .catch(() => setAuth({ status: "out", user: null }));
  }, []);

  const setUser = useCallback((user) => setAuth({ status: "in", user }), []);

  const logout = useCallback(async () => {
    await api("/api/auth/logout", { method: "POST" }).catch(() => {});
    setAuth({ status: "out", user: null });
  }, []);

  const value = useMemo(() => ({ ...auth, setUser, logout }), [auth, setUser, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}

export function RequireAuth({ children }) {
  const { status } = useAuth();
  if (status === "loading") return <Spinner />;
  if (status === "out") return <Navigate to="/auth/login" replace />;
  return children;
}
