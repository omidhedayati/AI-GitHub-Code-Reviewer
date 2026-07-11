import uuid
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.repository import Repository
from app.models.review import (
    FileAnalysisResult,
    Review,
    ReviewIssue,
    ReviewStatus,
    ReviewType,
)
from app.schemas.review_search import ReviewSearchParams, ReviewSearchSort
from app.services.analyzers.base import AnalysisIssue


class ReviewRepository:
    """Data access for analysis reviews."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        repository_id: uuid.UUID,
        user_id: uuid.UUID,
        status: ReviewStatus = ReviewStatus.PENDING,
        review_type: ReviewType = ReviewType.STATIC,
    ) -> Review:
        review = Review(
            repository_id=repository_id,
            user_id=user_id,
            status=status.value,
            review_type=review_type.value,
        )
        self._db.add(review)
        self._db.commit()
        self._db.refresh(review)
        return review

    def get_by_id(self, review_id: uuid.UUID) -> Review | None:
        statement = (
            select(Review)
            .options(
                selectinload(Review.issues),
                selectinload(Review.file_results),
            )
            .where(Review.id == review_id)
        )
        return self._db.scalar(statement)

    def get_by_id_for_user(
        self, review_id: uuid.UUID, user_id: uuid.UUID
    ) -> Review | None:
        statement = (
            select(Review)
            .options(
                selectinload(Review.issues),
                selectinload(Review.file_results),
            )
            .where(Review.id == review_id, Review.user_id == user_id)
        )
        return self._db.scalar(statement)

    def get_latest_for_repository(
        self,
        repository_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        review_type: ReviewType | None = None,
    ) -> Review | None:
        statement = (
            select(Review)
            .options(
                selectinload(Review.issues),
                selectinload(Review.file_results),
            )
            .where(
                Review.repository_id == repository_id,
                Review.user_id == user_id,
            )
        )
        if review_type is not None:
            statement = statement.where(Review.review_type == review_type.value)
        statement = statement.order_by(Review.created_at.desc()).limit(1)
        return self._db.scalar(statement)

    def list_for_repository(
        self,
        repository_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[Review]:
        statement = (
            select(Review)
            .where(
                Review.repository_id == repository_id,
                Review.user_id == user_id,
            )
            .order_by(Review.created_at.desc())
        )
        return list(self._db.scalars(statement).all())

    def search_for_user(
        self,
        user_id: uuid.UUID,
        params: ReviewSearchParams,
    ) -> tuple[list[tuple[Review, Repository]], int]:
        id_query = (
            select(Review.id)
            .join(Repository, Review.repository_id == Repository.id)
            .where(Review.user_id == user_id)
        )
        id_query = self._apply_search_filters(id_query, params)
        total = (
            self._db.scalar(
                select(func.count()).select_from(id_query.distinct().subquery())
            )
            or 0
        )

        fetch = (
            select(Review, Repository)
            .join(Repository, Review.repository_id == Repository.id)
            .where(Review.user_id == user_id)
        )
        fetch = self._apply_search_filters(fetch, params)
        fetch = fetch.distinct()
        fetch = self._apply_search_sort(fetch, params.sort)
        fetch = fetch.offset(params.offset).limit(params.limit)
        rows = list(self._db.execute(fetch).all())
        return [(review, repository) for review, repository in rows], total

    def _apply_search_filters(self, statement: Any, params: ReviewSearchParams) -> Any:
        if params.repository_id is not None:
            statement = statement.where(Review.repository_id == params.repository_id)
        if params.review_type is not None:
            statement = statement.where(Review.review_type == params.review_type.value)
        if params.status is not None:
            statement = statement.where(Review.status == params.status.value)
        if params.min_score is not None:
            statement = statement.where(Review.overall_score >= params.min_score)
        if params.max_score is not None:
            statement = statement.where(Review.overall_score <= params.max_score)
        if params.from_date is not None:
            statement = statement.where(Review.created_at >= params.from_date)
        if params.to_date is not None:
            statement = statement.where(Review.created_at <= params.to_date)
        if params.severity is not None:
            statement = statement.where(
                Review.issues.any(ReviewIssue.severity == params.severity)
            )
        if params.q:
            pattern = f"%{params.q.strip()}%"
            statement = statement.where(
                or_(
                    Review.summary.ilike(pattern),
                    Review.report_markdown.ilike(pattern),
                    Repository.owner.ilike(pattern),
                    Repository.name.ilike(pattern),
                    Review.issues.any(
                        or_(
                            ReviewIssue.title.ilike(pattern),
                            ReviewIssue.explanation.ilike(pattern),
                            ReviewIssue.file_path.ilike(pattern),
                        )
                    ),
                )
            )
        return statement

    def _apply_search_sort(self, statement: Any, sort: ReviewSearchSort) -> Any:
        mapping = {
            ReviewSearchSort.CREATED_DESC: Review.created_at.desc(),
            ReviewSearchSort.CREATED_ASC: Review.created_at.asc(),
            ReviewSearchSort.SCORE_DESC: Review.overall_score.desc(),
            ReviewSearchSort.SCORE_ASC: Review.overall_score.asc(),
            ReviewSearchSort.ISSUES_DESC: Review.issues_count.desc(),
            ReviewSearchSort.ISSUES_ASC: Review.issues_count.asc(),
        }
        return statement.order_by(mapping[sort])

    def save_results(
        self,
        review: Review,
        *,
        issues: list[AnalysisIssue],
        file_results: list[FileAnalysisResult],
        files_analyzed: int,
        overall_score: float,
        summary: str,
        status: ReviewStatus,
        error_message: str | None = None,
        ai_model: str | None = None,
        report_markdown: str | None = None,
    ) -> Review:
        review.issues = [
            ReviewIssue(
                file_path=issue.file_path,
                line_start=issue.line_start,
                line_end=issue.line_end,
                category=issue.category.value,
                severity=issue.severity.value,
                confidence=issue.confidence,
                rule_id=issue.rule_id,
                title=issue.title,
                explanation=issue.explanation,
                suggestion=issue.suggestion,
            )
            for issue in issues
        ]
        review.file_results = file_results
        review.files_analyzed = files_analyzed
        review.issues_count = len(issues)
        review.overall_score = overall_score
        review.summary = summary
        review.status = status.value
        review.error_message = error_message
        if ai_model is not None:
            review.ai_model = ai_model
        if report_markdown is not None:
            review.report_markdown = report_markdown
        self._db.add(review)
        self._db.commit()
        reloaded = self.get_by_id(review.id)
        if reloaded is None:
            raise RuntimeError("Failed to reload review after save")
        return reloaded

    def update(self, review: Review) -> Review:
        self._db.add(review)
        self._db.commit()
        self._db.refresh(review)
        return review
