import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.config.settings import Settings
from app.models.repository import Repository, RepositoryStatus
from app.models.review import FileAnalysisResult, ReviewStatus, ReviewType
from app.models.user import User
from app.repositories.repository_repository import RepositoryRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.analysis import ReviewResponse
from app.services.analyzers.base import AnalysisIssue
from app.services.analyzers.common import detect_duplicated_blocks
from app.services.analyzers.registry import analyze_file
from app.services.report_service import ReportService
from app.utils.file_walker import detect_language, iter_analyzable_files
from app.utils.scoring import calculate_file_score, calculate_overall_score


class AnalysisServiceError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class RepositoryNotReadyError(AnalysisServiceError):
    pass


class ReviewNotFoundError(AnalysisServiceError):
    pass


class AnalysisService:
    """Runs static analysis over cloned repository files."""

    def __init__(
        self,
        repository_repository: RepositoryRepository,
        review_repository: ReviewRepository,
        settings: Settings,
    ) -> None:
        self._repositories = repository_repository
        self._reviews = review_repository
        self._settings = settings

    def analyze_repository(
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
            raise RepositoryNotReadyError("Repository must be cloned before analysis")

        root = Path(repository.local_path)
        if not root.exists():
            raise RepositoryNotReadyError("Repository files are unavailable on disk")

        review = self._reviews.create(
            repository_id=repository.id,
            user_id=user.id,
            status=ReviewStatus.RUNNING,
            review_type=ReviewType.STATIC,
        )
        review.started_at = datetime.now(UTC)
        self._reviews.update(review)

        try:
            return self._run_analysis(repository, root, review.id, user.id)
        except Exception as exc:
            review.status = ReviewStatus.FAILED.value
            review.error_message = "Analysis failed unexpectedly"
            review.completed_at = datetime.now(UTC)
            self._reviews.update(review)
            raise AnalysisServiceError("Analysis failed") from exc

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

    def _run_analysis(
        self,
        repository: Repository,
        root: Path,
        review_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ReviewResponse:
        files = iter_analyzable_files(root, self._settings)
        all_issues: list[AnalysisIssue] = []
        file_contents: dict[str, str] = {}
        file_results: list[FileAnalysisResult] = []

        for file_path in files:
            relative_path = str(file_path.relative_to(root)).replace("\\", "/")
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = file_path.read_text(encoding="utf-8", errors="replace")

            file_contents[relative_path] = content
            file_issues = analyze_file(file_path, content, relative_path)
            all_issues.extend(file_issues)

            language = detect_language(file_path) or "unknown"
            file_score = calculate_file_score(file_issues)
            file_results.append(
                FileAnalysisResult(
                    review_id=review_id,
                    file_path=relative_path,
                    language=language,
                    line_count=len(content.splitlines()),
                    issues_count=len(file_issues),
                    file_score=file_score,
                )
            )

        duplicate_issues = detect_duplicated_blocks(file_contents)
        all_issues.extend(duplicate_issues)

        for file_result in file_results:
            extra = sum(
                1
                for issue in duplicate_issues
                if issue.file_path == file_result.file_path
            )
            if extra:
                file_result.issues_count += extra
                file_result.file_score = calculate_file_score(
                    [
                        issue
                        for issue in all_issues
                        if issue.file_path == file_result.file_path
                    ]
                )

        file_scores = [result.file_score for result in file_results]
        overall_score = calculate_overall_score(file_scores)
        summary = (
            f"Analyzed {len(file_results)} files in "
            f"{repository.owner}/{repository.name}. "
            f"Found {len(all_issues)} issues with an overall score of {overall_score}."
        )

        review = self._reviews.get_by_id_for_user(review_id, user_id)
        if review is None:
            raise ReviewNotFoundError("Review not found")

        review.completed_at = datetime.now(UTC)
        updated = self._reviews.save_results(
            review,
            issues=all_issues,
            file_results=file_results,
            files_analyzed=len(file_results),
            overall_score=overall_score,
            summary=summary,
            status=ReviewStatus.COMPLETED,
        )
        updated.report_markdown = ReportService.build_markdown(updated, repository)
        updated = self._reviews.update(updated)
        return ReviewResponse.model_validate(updated)
