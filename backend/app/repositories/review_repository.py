import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.review import FileAnalysisResult, Review, ReviewIssue, ReviewStatus
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
    ) -> Review:
        review = Review(
            repository_id=repository_id,
            user_id=user_id,
            status=status.value,
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
            .order_by(Review.created_at.desc())
            .limit(1)
        )
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
