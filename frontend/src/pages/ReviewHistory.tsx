import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { apiClient } from "../api/client";
import type { ReviewType } from "../api/types";
import { ReviewTypeBadge } from "../components/analysis/ReviewTypeBadge";

const PAGE_SIZE = 20;

export function ReviewHistoryPage() {
  const [query, setQuery] = useState("");
  const [reviewType, setReviewType] = useState<ReviewType | "">("");
  const [severity, setSeverity] = useState("");
  const [offset, setOffset] = useState(0);
  const [searchInput, setSearchInput] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["review-search", query, reviewType, severity, offset],
    queryFn: () =>
      apiClient.searchReviews({
        q: query || undefined,
        review_type: reviewType || undefined,
        severity: severity || undefined,
        offset,
        limit: PAGE_SIZE,
      }),
  });

  const total = data?.total ?? 0;
  const canPrev = offset > 0;
  const canNext = offset + PAGE_SIZE < total;

  function handleSearch(event: React.FormEvent) {
    event.preventDefault();
    setOffset(0);
    setQuery(searchInput.trim());
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Review History</h2>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Search and browse static and AI review runs across your repositories.
        </p>
      </div>

      <form onSubmit={handleSearch} className="flex flex-wrap gap-3">
        <input
          type="search"
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
          placeholder="Search summaries, files, issues..."
          className="min-w-[220px] flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
        />
        <select
          value={reviewType}
          onChange={(event) => {
            setReviewType(event.target.value as ReviewType | "");
            setOffset(0);
          }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
        >
          <option value="">All types</option>
          <option value="static">Static</option>
          <option value="ai">AI</option>
        </select>
        <select
          value={severity}
          onChange={(event) => {
            setSeverity(event.target.value);
            setOffset(0);
          }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
        >
          <option value="">All severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="info">Info</option>
        </select>
        <button
          type="submit"
          className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
        >
          Search
        </button>
      </form>

      {isLoading && <p className="text-sm text-gray-500">Loading reviews...</p>}
      {isError && (
        <p className="text-sm text-red-600">Failed to load review history.</p>
      )}

      {!isLoading && !isError && data?.items.length === 0 && (
        <p className="text-sm text-gray-600 dark:text-gray-400">
          No reviews match your search. Try a different query or run a new review.
        </p>
      )}

      <div className="space-y-3">
        {data?.items.map((review) => (
          <Link
            key={review.id}
            to={`/reviews/${review.id}`}
            className="block rounded-xl border border-gray-200 bg-white p-4 transition hover:border-primary-300 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-primary-700"
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-medium">{review.repository_name}</p>
                  <ReviewTypeBadge reviewType={review.review_type} />
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {new Date(review.created_at).toLocaleString()}
                </p>
                {review.summary && (
                  <p className="mt-2 line-clamp-2 text-sm text-gray-700 dark:text-gray-300">
                    {review.summary}
                  </p>
                )}
              </div>
              <div className="text-right text-sm">
                <p>Score: {review.overall_score}</p>
                <p className="text-gray-500">{review.issues_count} issues</p>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {total > 0 && (
        <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
          <p>
            Showing {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={!canPrev}
              onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))}
              className="rounded border border-gray-300 px-3 py-1 disabled:opacity-50 dark:border-gray-700"
            >
              Previous
            </button>
            <button
              type="button"
              disabled={!canNext}
              onClick={() => setOffset((value) => value + PAGE_SIZE)}
              className="rounded border border-gray-300 px-3 py-1 disabled:opacity-50 dark:border-gray-700"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
