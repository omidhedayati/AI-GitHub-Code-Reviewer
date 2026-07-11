import { useQuery } from "@tanstack/react-query";

import { apiClient } from "../api/client";

export function DashboardPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: apiClient.getHealth,
  });

  return (
    <div>
      <h2 className="text-2xl font-bold">Dashboard</h2>
      <p className="mt-2 text-gray-600 dark:text-gray-400">
        Overview of repositories analyzed, reviews performed, and quality metrics.
      </p>
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          "Repositories Analyzed",
          "Reviews Performed",
          "Average Quality Score",
          "Detected Issues",
        ].map((label) => (
          <div
            key={label}
            className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900"
          >
            <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
            <p className="mt-2 text-3xl font-semibold">—</p>
          </div>
        ))}
      </div>
      <div className="mt-6 rounded-lg border border-gray-200 bg-white p-4 text-sm dark:border-gray-800 dark:bg-gray-900">
        <span className="font-medium">API status: </span>
        {isLoading && "Checking..."}
        {isError && "Unavailable"}
        {data && (
          <span className="text-green-600 dark:text-green-400">{data.status}</span>
        )}
      </div>
    </div>
  );
}
