import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import AdminPage from "./pages/AdminPage";
import { getCurrentUser } from "./api/auth";

function ProtectedRoute({ children, requiredRole }) {
  const [status, setStatus] = useState("checking");
  const [userRole, setUserRole] = useState(null);

  useEffect(() => {
    let mounted = true;

    async function validateSession() {
      const token = localStorage.getItem("token");
      if (!token) {
        if (mounted) setStatus("unauthenticated");
        return;
      }

      try {
        const { ok, data } = await getCurrentUser();
        if (!mounted) return;

        if (ok && data) {
          localStorage.setItem("user", JSON.stringify(data));
          setUserRole(data.role);
          
          // Verificar si el usuario tiene el rol requerido
          if (requiredRole && data.role !== requiredRole) {
            setStatus("forbidden");
            return;
          }
          
          setStatus("authenticated");
          return;
        }
      } catch {
        // Falls through to session cleanup.
      }

      localStorage.removeItem("token");
      localStorage.removeItem("user");
      if (mounted) setStatus("unauthenticated");
    }

    validateSession();
    return () => {
      mounted = false;
    };
  }, [requiredRole]);

  if (status === "checking") {
    return null;
  }

  if (status === "forbidden") {
    return <Navigate to="/boveda" replace />;
  }

  return status === "authenticated" ? children : <Navigate to="/" replace />;
}

function RoleBasedRoute() {
  const [userRole, setUserRole] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function checkRole() {
      const token = localStorage.getItem("token");
      if (token) {
        try {
          const { ok, data } = await getCurrentUser();
          if (ok && data) {
            setUserRole(data.role);
          }
        } catch {
          // Fall through
        }
      }
      setLoading(false);
    }
    checkRole();
  }, []);

  if (loading) return null;

  return userRole === "admin" ? <AdminPage /> : <DashboardPage />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route
          path="/boveda"
          element={
            <ProtectedRoute>
              <RoleBasedRoute />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute requiredRole="admin">
              <AdminPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
