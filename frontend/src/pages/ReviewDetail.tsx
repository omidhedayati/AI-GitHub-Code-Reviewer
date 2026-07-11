import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { apiClient } from "../api/client";
import type { ReportFormat } from "../api/types";
import { IssueList } from "../components/analysis/IssueList";
import { ReviewTypeBadge } from "../components/analysis/ReviewTypeBadge";

function downloadText(content: string, filename: string) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function ReviewDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["review", id],
    queryFn: () => apiClient.getReview(id!),
    enabled: Boolean(id),
  });

  const { data: reportMarkdown } = useQuery({
    queryKey: ["review-report", id, "markdown"],
    queryFn: () => apiClient.fetchReviewReport(id!, "markdown"),
    enabled: Boolean(id) && Boolean(data),
  });

  const downloadMutation = useMutation({
    mutationFn: ({ format, filename }: { format: ReportFormat; filename: string }) =>
      apiClient.fetchReviewReport(id!, format, true).then((content) => {
        downloadText(content, filename);
      }),
  });

  if (!id) {
    return <p className="text-sm text-red-600">Invalid review ID.</p>;
  }

  if (isLoading) {
    return <p className="text-sm text-gray-500">Loading review...</p>;
  }

  if (isError || !data) {
    return (
      <div>
        <p className="text-sm text-red-600">Review not found.</p>
        <Link to="/history" className="mt-4 inline-block text-primary-600">
          Back to history
        </Link>
      </div>
    );
  }

  const baseFilename = `review-${data.review_type}-${data.created_at.slice(0, 10)}`;

  return (
    <div className="space-y-6">
      <div>
        <Link
          to="/history"
          className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
        >
          ← Back to history
        </Link>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <h2 className="text-2xl font-bold">Review details</h2>
          <ReviewTypeBadge reviewType={data.review_type} />
        </div>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          {new Date(data.created_at).toLocaleString()} · Score {data.overall_score} ·{" "}
          {data.issues_count} issues
        </p>
        <Link
          to={`/repositories/${data.repository_id}`}
          className="mt-2 inline-block text-sm text-primary-600 dark:text-primary-400"
        >
          View repository
        </Link>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() =>
            downloadMutation.mutate({
              format: "markdown",
              filename: `${baseFilename}.md`,
            })
          }
          disabled={downloadMutation.isPending}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-900"
        >
          Download Markdown
        </button>
        <button
          type="button"
          onClick={() =>
            downloadMutation.mutate({
              format: "json",
              filename: `${baseFilename}.json`,
            })
          }
          disabled={downloadMutation.isPending}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-900"
        >
          Download JSON
        </button>
        <button
          type="button"
          onClick={() =>
            downloadMutation.mutate({
              format: "summary",
              filename: `${baseFilename}.txt`,
            })
          }
          disabled={downloadMutation.isPending}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-900"
        >
          Download summary
        </button>
      </div>

      <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
        <h3 className="font-semibold">Summary</h3>
        <p className="mt-3 text-sm text-gray-700 dark:text-gray-300">{data.summary}</p>
      </div>

      {reportMarkdown && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <h3 className="font-semibold">Markdown report</h3>
          <pre className="mt-4 max-h-96 overflow-auto whitespace-pre-wrap rounded-lg bg-gray-50 p-4 text-xs dark:bg-gray-950">
            {reportMarkdown}
          </pre>
        </div>
      )}

      <div>
        <h3 className="mb-4 text-lg font-semibold">Issues</h3>
        <IssueList issues={data.issues} />
      </div>
    </div>
  );
}
