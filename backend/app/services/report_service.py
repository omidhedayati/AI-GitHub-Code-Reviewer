import json
from datetime import datetime
from enum import StrEnum

from app.models.repository import Repository
from app.models.review import Review, ReviewIssue


class ReportFormat(StrEnum):
    MARKDOWN = "markdown"
    JSON = "json"
    SUMMARY = "summary"


class ReportService:
    """Builds Markdown, JSON, and summary exports from review data."""

    @staticmethod
    def build_summary(review: Review, repository: Repository) -> str:
        if review.summary:
            return review.summary
        return (
            f"Review of {repository.owner}/{repository.name}: "
            f"{review.issues_count} issues, score {review.overall_score}."
        )

    @staticmethod
    def build_markdown(review: Review, repository: Repository) -> str:
        lines: list[str] = [
            f"# Code Review Report: {repository.owner}/{repository.name}",
            "",
            "## Overview",
            "",
            f"- **Repository:** [{repository.url}]({repository.url})",
            f"- **Review type:** {review.review_type}",
            f"- **Status:** {review.status}",
            f"- **Overall score:** {review.overall_score}",
            f"- **Files analyzed:** {review.files_analyzed}",
            f"- **Issues found:** {review.issues_count}",
            f"- **Created:** {review.created_at.isoformat() if review.created_at else '—'}",
        ]
        if review.ai_model:
            lines.append(f"- **AI model:** {review.ai_model}")
        lines.extend(["", "## Summary", "", review.summary or "_No summary provided._", ""])

        if review.file_results:
            lines.extend(["## File scores", "", "| File | Language | Issues | Score |", "| --- | --- | --- | --- |"])
            for file_result in review.file_results:
                lines.append(
                    f"| `{file_result.file_path}` | {file_result.language} | "
                    f"{file_result.issues_count} | {file_result.file_score:.1f} |"
                )
            lines.append("")

        if review.issues:
            lines.extend(["## Issues", ""])
            for severity in ("critical", "high", "medium", "low", "info"):
                grouped = [issue for issue in review.issues if issue.severity == severity]
                if not grouped:
                    continue
                lines.append(f"### {severity.title()} ({len(grouped)})")
                lines.append("")
                for issue in grouped:
                    lines.extend(ReportService._format_issue_markdown(issue))
        else:
            lines.extend(["## Issues", "", "_No issues detected._", ""])

        return "\n".join(lines)

    @staticmethod
    def _format_issue_markdown(issue: ReviewIssue) -> list[str]:
        line_ref = f"{issue.file_path}:{issue.line_start}"
        if issue.line_end:
            line_ref += f"-{issue.line_end}"
        return [
            f"#### {issue.title}",
            "",
            f"- **Location:** `{line_ref}`",
            f"- **Category:** {issue.category.replace('_', ' ')}",
            f"- **Severity:** {issue.severity}",
            f"- **Confidence:** {issue.confidence:.0%}",
            f"- **Rule:** `{issue.rule_id}`",
            "",
            issue.explanation,
            "",
            f"**Suggestion:** {issue.suggestion}",
            "",
        ]

    @staticmethod
    def build_json(review: Review, repository: Repository) -> dict[str, object]:
        return {
            "review": {
                "id": str(review.id),
                "repository_id": str(review.repository_id),
                "review_type": review.review_type,
                "status": review.status,
                "overall_score": review.overall_score,
                "files_analyzed": review.files_analyzed,
                "issues_count": review.issues_count,
                "summary": review.summary,
                "ai_model": review.ai_model,
                "error_message": review.error_message,
                "started_at": _iso(review.started_at),
                "completed_at": _iso(review.completed_at),
                "created_at": _iso(review.created_at),
            },
            "repository": {
                "id": str(repository.id),
                "owner": repository.owner,
                "name": repository.name,
                "url": repository.url,
                "default_branch": repository.default_branch,
            },
            "file_results": [
                {
                    "file_path": result.file_path,
                    "language": result.language,
                    "line_count": result.line_count,
                    "issues_count": result.issues_count,
                    "file_score": result.file_score,
                }
                for result in review.file_results
            ],
            "issues": [
                {
                    "file_path": issue.file_path,
                    "line_start": issue.line_start,
                    "line_end": issue.line_end,
                    "category": issue.category,
                    "severity": issue.severity,
                    "confidence": issue.confidence,
                    "rule_id": issue.rule_id,
                    "title": issue.title,
                    "explanation": issue.explanation,
                    "suggestion": issue.suggestion,
                }
                for issue in review.issues
            ],
        }

    @staticmethod
    def build_json_text(review: Review, repository: Repository) -> str:
        return json.dumps(
            ReportService.build_json(review, repository),
            indent=2,
        )

    @staticmethod
    def filename(repository: Repository, review: Review, fmt: ReportFormat) -> str:
        slug = f"{repository.owner}-{repository.name}"
        date_part = review.created_at.strftime("%Y%m%d") if review.created_at else "report"
        extension = "md" if fmt == ReportFormat.MARKDOWN else fmt.value
        return f"{slug}-{review.review_type}-{date_part}.{extension}"


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None
