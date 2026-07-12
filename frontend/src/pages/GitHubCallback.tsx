import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../hooks/useAuth";

export function GitHubCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { completeGitHubLogin } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const oauthError = searchParams.get("error");
    if (oauthError) {
      setError(oauthError.replace(/_/g, " "));
      return;
    }

    const exchangeCode = searchParams.get("code");
    if (!exchangeCode) {
      setError("Missing GitHub login code");
      return;
    }

    const code = exchangeCode;
    let cancelled = false;

    async function finishLogin() {
      try {
        await completeGitHubLogin(code);
        if (!cancelled) {
          navigate("/dashboard", { replace: true });
        }
      } catch (err) {
        if (!cancelled) {
          if (err instanceof ApiError) {
            setError(err.message);
          } else {
            setError("Unable to complete GitHub sign-in.");
          }
        }
      }
    }

    void finishLogin();

    return () => {
      cancelled = true;
    };
  }, [completeGitHubLogin, navigate, searchParams]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 dark:bg-gray-950">
        <div className="w-full max-w-md rounded-xl border border-gray-200 bg-white p-8 shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <h2 className="text-2xl font-bold">GitHub sign-in failed</h2>
          <p className="mt-4 text-sm text-red-600 dark:text-red-400">{error}</p>
          <Link
            to="/login"
            className="mt-6 inline-block text-sm font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400"
          >
            Back to login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-950">
      <p className="text-sm text-gray-500 dark:text-gray-400">
        Completing GitHub sign-in...
      </p>
    </div>
  );
}
