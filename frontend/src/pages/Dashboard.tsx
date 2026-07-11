import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { ApiError, apiClient } from "../api/client";
import { CloneRepositoryForm } from "../components/repositories/CloneRepositoryForm";
import { RepositoryList } from "../components/repositories/RepositoryList";

async function fetchLatestReviewIssues(repositoryId: string): Promise<number> {
  try {
    const review = await apiClient.getLatestReview(repositoryId);
    return review.issues_count;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return 0;
    }
    return 0;
  }
}

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

  const { data: totalIssues = 0 } = useQuery({
    queryKey: ["dashboard-issues", repositories?.items.map((repo) => repo.id)],
    queryFn: async () => {
      if (!repositories?.items.length) {
        return 0;
      }
      const counts = await Promise.all(
        repositories.items
          .filter((repo) => repo.status === "ready")
          .map((repo) => fetchLatestReviewIssues(repo.id)),
      );
      return counts.reduce((sum, count) => sum + count, 0);
    },
    enabled: Boolean(repositories?.items.length),
  });

  const readyCount =
    repositories?.items.filter((repo) => repo.status === "ready").length ?? 0;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Clone GitHub repositories and run static code analysis.
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
            Detected Issues
          </p>
          <p className="mt-2 text-3xl font-semibold">{totalIssues}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <p className="text-sm text-gray-500 dark:text-gray-400">API Status</p>
          <p className="mt-2 text-3xl font-semibold capitalize">
            {health?.status ?? "…"}
          </p>
        </div>
      </div>

      <CloneRepositoryForm />

      <div>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">Your Repositories</h3>
          <Link
            to="/history"
            className="text-sm font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400"
          >
            View review history
          </Link>
        </div>
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
    </div>
  );
}
