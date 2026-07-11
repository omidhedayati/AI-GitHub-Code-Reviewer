import { useQuery } from "@tanstack/react-query";

import { apiClient } from "../api/client";
import { CloneRepositoryForm } from "../components/repositories/CloneRepositoryForm";
import { RepositoryList } from "../components/repositories/RepositoryList";

export function DashboardPage() {
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: apiClient.getHealth,
  });

  const {
    data: repositories,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["repositories"],
    queryFn: apiClient.listRepositories,
  });

  const readyCount =
    repositories?.items.filter((repo) => repo.status === "ready").length ?? 0;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Clone GitHub repositories and track their review status.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Repositories Added
          </p>
          <p className="mt-2 text-3xl font-semibold">
            {repositories?.total ?? (isLoading ? "…" : 0)}
          </p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Ready for Review
          </p>
          <p className="mt-2 text-3xl font-semibold">{readyCount}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Reviews Performed
          </p>
          <p className="mt-2 text-3xl font-semibold">—</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Detected Issues
          </p>
          <p className="mt-2 text-3xl font-semibold">—</p>
        </div>
      </div>

      <CloneRepositoryForm />

      <div>
        <h3 className="mb-4 text-lg font-semibold">Your Repositories</h3>
        {isLoading && (
          <p className="text-sm text-gray-500 dark:text-gray-400">Loading...</p>
        )}
        {isError && (
          <p className="text-sm text-red-600 dark:text-red-400">
            Failed to load repositories.
          </p>
        )}
        {repositories && <RepositoryList repositories={repositories.items} />}
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-4 text-sm dark:border-gray-800 dark:bg-gray-900">
        <span className="font-medium">API status: </span>
        <span className="text-green-600 dark:text-green-400">
          {health?.status ?? "checking..."}
        </span>
      </div>
    </div>
  );
}
