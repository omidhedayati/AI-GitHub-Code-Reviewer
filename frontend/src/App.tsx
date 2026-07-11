import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, createBrowserRouter } from "react-router-dom";

import { AppShell } from "./components/layout/AppShell";
import { AuthProvider } from "./context/AuthContext";
import { DashboardPage } from "./pages/Dashboard";
import { LoginPage } from "./pages/Login";
import { ProfilePage } from "./pages/Profile";
import { RegisterPage } from "./pages/Register";
import { RepositoryDetailsPage } from "./pages/RepositoryDetails";
import { ReviewHistoryPage } from "./pages/ReviewHistory";
import { SettingsPage } from "./pages/Settings";
import {
  ProtectedRoute,
  PublicOnlyRoute,
  RootRedirect,
} from "./routes/index";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
});

const router = createBrowserRouter([
  {
    path: "/",
    element: <RootRedirect />,
  },
  {
    element: <PublicOnlyRoute />,
    children: [
      {
        path: "/login",
        element: <LoginPage />,
      },
      {
        path: "/register",
        element: <RegisterPage />,
      },
    ],
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          { path: "/dashboard", element: <DashboardPage /> },
          { path: "/history", element: <ReviewHistoryPage /> },
          { path: "/repositories/:id", element: <RepositoryDetailsPage /> },
          { path: "/settings", element: <SettingsPage /> },
          { path: "/profile", element: <ProfilePage /> },
        ],
      },
    ],
  },
]);

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>
  );
}
