import type { IssueSeverity } from "../../api/types";

const STYLES: Record<IssueSeverity, string> = {
  critical: "bg-red-200 text-red-900 dark:bg-red-950 dark:text-red-200",
  high: "bg-orange-200 text-orange-900 dark:bg-orange-950 dark:text-orange-200",
  medium: "bg-yellow-200 text-yellow-900 dark:bg-yellow-950 dark:text-yellow-200",
  low: "bg-blue-100 text-blue-900 dark:bg-blue-950 dark:text-blue-200",
  info: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
};

export function SeverityBadge({ severity }: { severity: IssueSeverity }) {
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium capitalize ${STYLES[severity]}`}
    >
      {severity}
    </span>
  );
}
