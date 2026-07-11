import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";

import { apiClient } from "../api/client";
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

      <div className="grid gap-4 md:grid-cols-2">
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
            <div>
              <dt className="text-gray-500 dark:text-gray-400">Created</dt>
              <dd className="mt-1">
                {new Date(data.created_at).toLocaleString()}
              </dd>
            </div>
          </dl>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <h3 className="font-semibold">Analysis</h3>
          {data.status === "ready" ? (
            <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
              Repository cloned successfully. Static analysis and AI review will
              be available in the next step.
            </p>
          ) : data.status === "failed" ? (
            <p className="mt-4 text-sm text-red-600 dark:text-red-400">
              {data.error_message ?? "Clone failed."}
            </p>
          ) : (
            <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
              Repository clone in progress or pending.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
