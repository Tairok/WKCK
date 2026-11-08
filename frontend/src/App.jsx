import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { RequireAuth } from "./auth/AuthContext";
import AuthPage from "./pages/AuthPage";
import Overview from "./pages/Overview";
import Inventory from "./pages/Inventory";
import Sensors from "./pages/Sensors";
import SensorsLayout from "./pages/SensorsLayout";
import Health from "./pages/Health";
import Users from "./pages/Users";

export default function App() {
  return (
    <Routes>
      <Route path="/auth/login" element={<AuthPage />} />
      <Route path="/auth/register" element={<AuthPage />} />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<Overview />} />
        <Route path="inventory" element={<Inventory />} />
        <Route path="sensors" element={<SensorsLayout />}>
          <Route index element={<Sensors />} />
        </Route>
        <Route path="health" element={<Health />} />
        <Route path="users" element={<Users />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
