import type { ReviewType } from "../../api/types";

const LABELS: Record<ReviewType, string> = {
  static: "Static",
  ai: "AI",
  hybrid: "Hybrid",
};

const STYLES: Record<ReviewType, string> = {
  static: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
  ai: "bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300",
  hybrid: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
};

export function ReviewTypeBadge({ reviewType }: { reviewType: ReviewType }) {
  return (
    <span
      className={`rounded px-2 py-0.5 text-xs font-medium ${STYLES[reviewType]}`}
    >
      {LABELS[reviewType]}
    </span>
  );
}
