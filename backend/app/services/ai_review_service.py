import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from app.config.settings import Settings
from app.models.repository import Repository, RepositoryStatus
from app.models.review import FileAnalysisResult, Review, ReviewStatus, ReviewType
from app.models.user import User
from app.repositories.repository_repository import RepositoryRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.ai_review import AIReviewOutput
from app.schemas.analysis import ReviewResponse
from app.services.ai_review_prompt import (
    AI_REVIEW_SYSTEM_PROMPT,
    build_ai_review_prompt,
)
from app.services.analyzers.base import AnalysisIssue, IssueCategory, IssueSeverity
from app.services.ollama_service import (
    OllamaModelNotFoundError,
    OllamaResponseError,
    OllamaService,
    OllamaUnavailableError,
)
from app.services.report_service import ReportService
from app.utils.file_walker import detect_language, iter_analyzable_files
from app.utils.scoring import calculate_file_score, calculate_overall_score


class AIReviewServiceError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class RepositoryNotReadyError(AIReviewServiceError):
    pass


class ReviewNotFoundError(AIReviewServiceError):
    pass


class OllamaNotReadyError(AIReviewServiceError):
    pass


_CATEGORY_MAP: dict[str, IssueCategory] = {
    "bug": IssueCategory.BUG,
    "security": IssueCategory.SECURITY,
    "code_smell": IssueCategory.CODE_SMELL,
    "complexity": IssueCategory.COMPLEXITY,
    "long_method": IssueCategory.LONG_METHOD,
    "bad_naming": IssueCategory.BAD_NAMING,
    "dead_code": IssueCategory.DEAD_CODE,
    "missing_documentation": IssueCategory.MISSING_DOCUMENTATION,
    "duplicated_code": IssueCategory.DUPLICATED_CODE,
    "unused_import": IssueCategory.UNUSED_IMPORT,
}

_SEVERITY_MAP: dict[str, IssueSeverity] = {
    "critical": IssueSeverity.CRITICAL,
    "high": IssueSeverity.HIGH,
    "medium": IssueSeverity.MEDIUM,
    "low": IssueSeverity.LOW,
    "info": IssueSeverity.INFO,
}


class AIReviewService:
    """Runs Ollama-powered structured code reviews."""

    def __init__(
        self,
        repository_repository: RepositoryRepository,
        review_repository: ReviewRepository,
        ollama_service: OllamaService,
        settings: Settings,
    ) -> None:
        self._repositories = repository_repository
        self._reviews = review_repository
        self._ollama = ollama_service
        self._settings = settings

    def run_ai_review(
        self,
        user: User,
        repository_id: uuid.UUID,
    ) -> ReviewResponse:
        repository = self._repositories.get_by_id_for_user(repository_id, user.id)
        if repository is None:
            raise ReviewNotFoundError("Repository not found")
        if (
            repository.status != RepositoryStatus.READY.value
            or not repository.local_path
        ):
            raise RepositoryNotReadyError("Repository must be cloned before AI review")

        root = Path(repository.local_path)
        if not root.exists():
            raise RepositoryNotReadyError("Repository files are unavailable on disk")

        health = self._ollama.check_health()
        if not health.available:
            raise OllamaNotReadyError(health.message)

        review = self._reviews.create(
            repository_id=repository.id,
            user_id=user.id,
            status=ReviewStatus.RUNNING,
            review_type=ReviewType.AI,
        )
        review.started_at = datetime.now(UTC)
        review.ai_model = self._settings.ollama_model
        self._reviews.update(review)

        try:
            return self._run_ai_review(repository, root, review.id, user.id)
        except (OllamaUnavailableError, OllamaModelNotFoundError) as exc:
            self._fail_review(review, str(exc))
            raise OllamaNotReadyError(exc.message) from exc
        except OllamaResponseError as exc:
            self._fail_review(review, exc.message)
            raise AIReviewServiceError(exc.message) from exc
        except Exception as exc:
            self._fail_review(review, "AI review failed unexpectedly")
            raise AIReviewServiceError("AI review failed") from exc

    def get_review(self, user: User, review_id: uuid.UUID) -> ReviewResponse:
        review = self._reviews.get_by_id_for_user(review_id, user.id)
        if review is None:
            raise ReviewNotFoundError("Review not found")
        return ReviewResponse.model_validate(review)

    def get_latest_review(
        self,
        user: User,
        repository_id: uuid.UUID,
        *,
        review_type: ReviewType | None = None,
    ) -> ReviewResponse | None:
        repository = self._repositories.get_by_id_for_user(repository_id, user.id)
        if repository is None:
            raise ReviewNotFoundError("Repository not found")
        review = self._reviews.get_latest_for_repository(
            repository_id,
            user.id,
            review_type=review_type,
        )
        if review is None:
            return None
        return ReviewResponse.model_validate(review)

    def list_reviews(
        self, user: User, repository_id: uuid.UUID
    ) -> list[ReviewResponse]:
        repository = self._repositories.get_by_id_for_user(repository_id, user.id)
        if repository is None:
            raise ReviewNotFoundError("Repository not found")
        reviews = self._reviews.list_for_repository(repository_id, user.id)
        return [ReviewResponse.model_validate(review) for review in reviews]

    def _fail_review(self, review: Review, message: str) -> None:
        review.status = ReviewStatus.FAILED.value
        review.error_message = message
        review.completed_at = datetime.now(UTC)
        self._reviews.update(review)

    def _run_ai_review(
        self,
        repository: Repository,
        root: Path,
        review_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ReviewResponse:
        files = iter_analyzable_files(root, self._settings)[
            : self._settings.ai_max_files
        ]
        if not files:
            raise AIReviewServiceError("No analyzable source files found")

        file_snippets: list[tuple[str, str]] = []
        file_results: list[FileAnalysisResult] = []

        for file_path in files:
            relative_path = str(file_path.relative_to(root)).replace("\\", "/")
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = file_path.read_text(encoding="utf-8", errors="replace")

            snippet = self._truncate_with_line_numbers(content)
            file_snippets.append((relative_path, snippet))

            language = detect_language(file_path) or "unknown"
            file_results.append(
                FileAnalysisResult(
                    review_id=review_id,
                    file_path=relative_path,
                    language=language,
                    line_count=len(content.splitlines()),
                    issues_count=0,
                    file_score=100.0,
                )
            )

        prompt = build_ai_review_prompt(
            f"{repository.owner}/{repository.name}",
            file_snippets,
        )
        raw_json = self._ollama.generate_json(
            system_prompt=AI_REVIEW_SYSTEM_PROMPT,
            user_prompt=prompt,
        )
        parsed = self._parse_ai_response(raw_json)
        issues = self._to_analysis_issues(parsed)

        for file_result in file_results:
            file_issues = [
                issue for issue in issues if issue.file_path == file_result.file_path
            ]
            file_result.issues_count = len(file_issues)
            file_result.file_score = calculate_file_score(file_issues)

        file_scores = [result.file_score for result in file_results]
        overall_score = calculate_overall_score(file_scores)
        summary = parsed.summary.strip() or (
            f"AI review of {len(file_results)} files in "
            f"{repository.owner}/{repository.name}. "
            f"Found {len(issues)} issues with an overall score of {overall_score}."
        )

        review = self._reviews.get_by_id_for_user(review_id, user_id)
        if review is None:
            raise ReviewNotFoundError("Review not found")

        review.completed_at = datetime.now(UTC)
        updated = self._reviews.save_results(
            review,
            issues=issues,
            file_results=file_results,
            files_analyzed=len(file_results),
            overall_score=overall_score,
            summary=summary,
            status=ReviewStatus.COMPLETED,
            ai_model=self._settings.ollama_model,
        )
        updated.report_markdown = ReportService.build_markdown(updated, repository)
        updated = self._reviews.update(updated)
        return ReviewResponse.model_validate(updated)

    def _truncate_with_line_numbers(self, content: str) -> str:
        max_chars = self._settings.ai_max_chars_per_file
        lines = content.splitlines()
        numbered: list[str] = []
        total_chars = 0
        for index, line in enumerate(lines, start=1):
            entry = f"{index:4d}| {line}"
            if total_chars + len(entry) + 1 > max_chars:
                numbered.append("... (truncated)")
                break
            numbered.append(entry)
            total_chars += len(entry) + 1
        return "\n".join(numbered)

    def _parse_ai_response(self, raw_json: str) -> AIReviewOutput:
        try:
            payload = json.loads(raw_json)
            return AIReviewOutput.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise OllamaResponseError(
                "Failed to parse structured AI review response"
            ) from exc

    def _to_analysis_issues(self, parsed: AIReviewOutput) -> list[AnalysisIssue]:
        issues: list[AnalysisIssue] = []
        for index, item in enumerate(parsed.issues):
            category = _CATEGORY_MAP.get(
                item.category.lower(),
                IssueCategory.CODE_SMELL,
            )
            severity = _SEVERITY_MAP.get(
                item.severity.lower(),
                IssueSeverity.MEDIUM,
            )
            issues.append(
                AnalysisIssue(
                    file_path=item.file_path,
                    line_start=item.line_start,
                    line_end=item.line_end,
                    category=category,
                    severity=severity,
                    confidence=item.confidence,
                    rule_id=f"ai:{category.value}:{index + 1}",
                    title=item.title[:255],
                    explanation=item.explanation,
                    suggestion=item.suggestion,
                )
            )
        return issues
