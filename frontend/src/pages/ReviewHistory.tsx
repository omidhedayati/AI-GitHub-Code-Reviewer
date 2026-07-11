import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { ApiError, apiClient } from "../api/client";
import { ReviewTypeBadge } from "../components/analysis/ReviewTypeBadge";

export function ReviewHistoryPage() {
  const { data: repositories, isLoading } = useQuery({
    queryKey: ["repositories"],
    queryFn: apiClient.listRepositories,
  });

  const { data: historyItems = [], isLoading: historyLoading } = useQuery({
    queryKey: ["review-history", repositories?.items.map((repo) => repo.id)],
    queryFn: async () => {
      if (!repositories?.items.length) {
        return [];
      }
      const results = await Promise.all(
        repositories.items.map(async (repo) => {
          try {
            const reviews = await apiClient.listReviews(repo.id);
            return reviews.items.map((review) => ({
              ...review,
              repositoryName: `${repo.owner}/${repo.name}`,
              repositoryId: repo.id,
            }));
          } catch (error) {
            if (error instanceof ApiError) {
              return [];
            }
            throw error;
          }
        }),
      );
      return results.flat().sort((a, b) => b.created_at.localeCompare(a.created_at));
    },
    enabled: Boolean(repositories?.items.length),
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Review History</h2>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Browse previous static and AI review runs across your repositories.
        </p>
      </div>

      {(isLoading || historyLoading) && (
        <p className="text-sm text-gray-500">Loading review history...</p>
      )}

      {!isLoading && !historyLoading && historyItems.length === 0 && (
        <p className="text-sm text-gray-600 dark:text-gray-400">
          No reviews yet. Clone a repository and run static analysis or an AI review
          from the repository details page.
        </p>
      )}

      <div className="space-y-3">
        {historyItems.map((review) => (
          <Link
            key={review.id}
            to={`/repositories/${review.repositoryId}`}
            className="block rounded-xl border border-gray-200 bg-white p-4 transition hover:border-primary-300 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-primary-700"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-medium">{review.repositoryName}</p>
                  <ReviewTypeBadge reviewType={review.review_type} />
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {new Date(review.created_at).toLocaleString()}
                </p>
              </div>
              <div className="text-right text-sm">
                <p>Score: {review.overall_score}</p>
                <p className="text-gray-500">{review.issues_count} issues</p>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
