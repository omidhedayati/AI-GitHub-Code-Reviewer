import uuid
from dataclasses import dataclass

from app.models.repository import Repository
from app.models.review import Review, ReviewStatus, ReviewType
from app.models.user import User
from app.repositories.repository_repository import RepositoryRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.analysis import ReviewResponse
from app.schemas.review_search import (
    ReviewHistoryItem,
    ReviewSearchParams,
    ReviewSearchResponse,
)
from app.services.report_service import ReportFormat, ReportService


class ReviewServiceError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ReviewNotFoundError(ReviewServiceError):
    pass


@dataclass(frozen=True)
class ReportContent:
    body: str
    media_type: str
    filename: str


class ReviewService:
    """Search reviews and export reports."""

    def __init__(
        self,
        review_repository: ReviewRepository,
        repository_repository: RepositoryRepository,
    ) -> None:
        self._reviews = review_repository
        self._repositories = repository_repository

    def search_reviews(
        self,
        user: User,
        params: ReviewSearchParams,
    ) -> ReviewSearchResponse:
        rows, total = self._reviews.search_for_user(user.id, params)
        items = [
            ReviewHistoryItem(
                id=review.id,
                repository_id=review.repository_id,
                repository_name=f"{repository.owner}/{repository.name}",
                review_type=ReviewType(review.review_type),
                status=ReviewStatus(review.status),
                overall_score=review.overall_score,
                issues_count=review.issues_count,
                files_analyzed=review.files_analyzed,
                summary=review.summary,
                ai_model=review.ai_model,
                created_at=review.created_at,
            )
            for review, repository in rows
        ]
        return ReviewSearchResponse(
            items=items,
            total=total,
            offset=params.offset,
            limit=params.limit,
        )

    def get_review(self, user: User, review_id: uuid.UUID) -> ReviewResponse:
        review = self._reviews.get_by_id_for_user(review_id, user.id)
        if review is None:
            raise ReviewNotFoundError("Review not found")
        return ReviewResponse.model_validate(review)

    def get_report(
        self,
        user: User,
        review_id: uuid.UUID,
        fmt: ReportFormat,
    ) -> ReportContent:
        review = self._reviews.get_by_id_for_user(review_id, user.id)
        if review is None:
            raise ReviewNotFoundError("Review not found")

        repository = self._repositories.get_by_id(review.repository_id)
        if repository is None:
            raise ReviewNotFoundError("Repository not found")

        if fmt == ReportFormat.SUMMARY:
            body = ReportService.build_summary(review, repository)
            media_type = "text/plain; charset=utf-8"
        elif fmt == ReportFormat.JSON:
            body = ReportService.build_json_text(review, repository)
            media_type = "application/json; charset=utf-8"
        else:
            body = review.report_markdown or ReportService.build_markdown(
                review, repository
            )
            media_type = "text/markdown; charset=utf-8"

        filename = ReportService.filename(repository, review, fmt)
        return ReportContent(body=body, media_type=media_type, filename=filename)

    def persist_report_markdown(
        self,
        review: Review,
        repository: Repository,
    ) -> Review:
        review.report_markdown = ReportService.build_markdown(review, repository)
        return self._reviews.update(review)
