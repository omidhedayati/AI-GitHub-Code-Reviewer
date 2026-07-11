import type { ReviewIssue } from "../../api/types";
import { SeverityBadge } from "./SeverityBadge";

export function IssueList({ issues }: { issues: ReviewIssue[] }) {
  if (issues.length === 0) {
    return (
      <p className="text-sm text-gray-600 dark:text-gray-400">
        No issues detected. Great work!
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {issues.map((issue) => (
        <article
          key={issue.id}
          className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900"
        >
          <div className="flex flex-wrap items-center gap-2">
            <SeverityBadge severity={issue.severity} />
            <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-300">
              {issue.category.replace(/_/g, " ")}
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {Math.round(issue.confidence * 100)}% confidence
            </span>
          </div>
          <h4 className="mt-2 font-medium">{issue.title}</h4>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            {issue.file_path}:{issue.line_start}
            {issue.line_end ? `-${issue.line_end}` : ""}
          </p>
          <p className="mt-2 text-sm">{issue.explanation}</p>
          <p className="mt-2 text-sm text-primary-700 dark:text-primary-300">
            Suggestion: {issue.suggestion}
          </p>
        </article>
      ))}
    </div>
  );
}
