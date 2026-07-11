import { Link } from "react-router-dom";

import type { Repository } from "../../api/types";
import { RepositoryStatusBadge } from "./RepositoryStatusBadge";

export function RepositoryList({ repositories }: { repositories: Repository[] }) {
  if (repositories.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-gray-300 p-8 text-center dark:border-gray-700">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          No repositories yet. Clone your first GitHub repository above.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 dark:border-gray-800">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800">
        <thead className="bg-gray-50 dark:bg-gray-900">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
              Repository
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
              Branch
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
              Status
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wide text-gray-500">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-800 dark:bg-gray-950">
          {repositories.map((repository) => (
            <tr key={repository.id}>
              <td className="px-4 py-3">
                <div className="font-medium text-gray-900 dark:text-gray-100">
                  {repository.owner}/{repository.name}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {repository.url}
                </div>
              </td>
              <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                {repository.default_branch ?? "—"}
              </td>
              <td className="px-4 py-3">
                <RepositoryStatusBadge status={repository.status} />
              </td>
              <td className="px-4 py-3 text-right">
                <Link
                  to={`/repositories/${repository.id}`}
                  className="text-sm font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400"
                >
                  View
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
