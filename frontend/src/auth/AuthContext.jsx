import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { Navigate } from "react-router-dom";
import { renderLoading } from "../components/PageElements";

const AuthContext = createContext(null);
const AUTH_STORAGE_KEY = "bmc-mock-user";

function getStoredUser() {
  const savedUser = window.localStorage.getItem(AUTH_STORAGE_KEY);
  if (!savedUser) return null;

  try {
    const user = JSON.parse(savedUser);
    return typeof user?.username === "string" ? user : null;
  } catch {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
}

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(() => {
    const user = getStoredUser();
    return user ? { status: "in", user } : { status: "out", user: null };
  });

  const setUser = useCallback((user) => {
    window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
    setAuth({ status: "in", user });
  }, []);

  const logout = useCallback(() => {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
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
  if (status === "loading") return renderLoading();
  if (status === "out") return <Navigate to="/auth/login" replace />;
  return children;
}
