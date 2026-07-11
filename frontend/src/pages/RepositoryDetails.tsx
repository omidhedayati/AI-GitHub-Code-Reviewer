import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ApiError, apiClient } from "../api/client";
import { IssueList } from "../components/analysis/IssueList";
import { RepositoryStatusBadge } from "../components/repositories/RepositoryStatusBadge";

export function RepositoryDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["repository", id],
    queryFn: () => apiClient.getRepository(id!),
    enabled: Boolean(id),
  });

  const {
    data: latestReview,
    isLoading: reviewLoading,
    refetch: refetchReview,
  } = useQuery({
    queryKey: ["review", "latest", id],
    queryFn: async () => {
      try {
        return await apiClient.getLatestReview(id!);
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          return null;
        }
        throw error;
      }
    },
    enabled: Boolean(id) && data?.status === "ready",
  });

  const analyzeMutation = useMutation({
    mutationFn: () => apiClient.analyzeRepository(id!),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["review", "latest", id] });
      await refetchReview();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteRepository(id!),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["repositories"] });
      navigate("/dashboard", { replace: true });
    },
  });

  if (!id) {
    return <p className="text-sm text-red-600">Invalid repository ID.</p>;
  }

  if (isLoading) {
    return <p className="text-sm text-gray-500">Loading repository...</p>;
  }

  if (isError || !data) {
    return (
      <div>
        <p className="text-sm text-red-600">Repository not found.</p>
        <Link to="/dashboard" className="mt-4 inline-block text-primary-600">
          Back to dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link
            to="/dashboard"
            className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
          >
            ← Back to dashboard
          </Link>
          <h2 className="mt-2 text-2xl font-bold">
            {data.owner}/{data.name}
          </h2>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{data.url}</p>
        </div>
        <div className="flex items-center gap-3">
          <RepositoryStatusBadge status={data.status} />
          {data.status === "ready" && (
            <button
              type="button"
              onClick={() => analyzeMutation.mutate()}
              disabled={analyzeMutation.isPending}
              className="rounded-lg bg-primary-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
            >
              {analyzeMutation.isPending ? "Analyzing..." : "Run analysis"}
            </button>
          )}
          <button
            type="button"
            onClick={() => deleteMutation.mutate()}
            disabled={deleteMutation.isPending}
            className="rounded-lg border border-red-300 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50 dark:border-red-900 dark:text-red-300 dark:hover:bg-red-950"
          >
            {deleteMutation.isPending ? "Deleting..." : "Delete"}
          </button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <p className="text-sm text-gray-500">Overall score</p>
          <p className="mt-2 text-3xl font-semibold">
            {latestReview?.overall_score ?? "—"}
          </p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <p className="text-sm text-gray-500">Files analyzed</p>
          <p className="mt-2 text-3xl font-semibold">
            {latestReview?.files_analyzed ?? "—"}
          </p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <p className="text-sm text-gray-500">Issues detected</p>
          <p className="mt-2 text-3xl font-semibold">
            {latestReview?.issues_count ?? "—"}
          </p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <h3 className="font-semibold">Clone details</h3>
          <dl className="mt-4 space-y-3 text-sm">
            <div>
              <dt className="text-gray-500 dark:text-gray-400">Default branch</dt>
              <dd className="mt-1">{data.default_branch ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-gray-500 dark:text-gray-400">Cloned at</dt>
              <dd className="mt-1">
                {data.cloned_at
                  ? new Date(data.cloned_at).toLocaleString()
                  : "—"}
              </dd>
            </div>
          </dl>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <h3 className="font-semibold">Analysis summary</h3>
          {reviewLoading && (
            <p className="mt-4 text-sm text-gray-500">Loading analysis...</p>
          )}
          {!reviewLoading && !latestReview && data.status === "ready" && (
            <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
              No analysis yet. Click &quot;Run analysis&quot; to scan the repository.
            </p>
          )}
          {latestReview && (
            <p className="mt-4 text-sm text-gray-700 dark:text-gray-300">
              {latestReview.summary}
            </p>
          )}
          {data.status === "failed" && (
            <p className="mt-4 text-sm text-red-600 dark:text-red-400">
              {data.error_message ?? "Clone failed."}
            </p>
          )}
        </div>
      </div>

      {latestReview && latestReview.file_results.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <h3 className="font-semibold">File scores</h3>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-left dark:border-gray-800">
                  <th className="py-2 pr-4">File</th>
                  <th className="py-2 pr-4">Language</th>
                  <th className="py-2 pr-4">Issues</th>
                  <th className="py-2">Score</th>
                </tr>
              </thead>
              <tbody>
                {latestReview.file_results.map((file) => (
                  <tr
                    key={file.id}
                    className="border-b border-gray-100 dark:border-gray-800"
                  >
                    <td className="py-2 pr-4 font-mono text-xs">{file.file_path}</td>
                    <td className="py-2 pr-4">{file.language}</td>
                    <td className="py-2 pr-4">{file.issues_count}</td>
                    <td className="py-2">{file.file_score.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {latestReview && (
        <div>
          <h3 className="mb-4 text-lg font-semibold">Detected issues</h3>
          <IssueList issues={latestReview.issues} />
        </div>
      )}
    </div>
  );
}
