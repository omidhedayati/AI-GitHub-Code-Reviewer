import { Navigate, Outlet } from "react-router-dom";

export function ProtectedRoute() {
  // Auth guard will be implemented in Step 2
  return <Outlet />;
}

export function PublicOnlyRoute() {
  // Redirect authenticated users once auth is implemented
  return <Outlet />;
}

export function RootRedirect() {
  return <Navigate to="/dashboard" replace />;
}
