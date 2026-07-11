import uuid
from datetime import UTC, datetime

import pytest

from app.models.repository import Repository
from app.models.review import (
    FileAnalysisResult,
    Review,
    ReviewIssue,
    ReviewStatus,
    ReviewType,
)
from app.services.report_service import ReportFormat, ReportService


@pytest.fixture
def sample_repository() -> Repository:
    return Repository(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        url="https://github.com/octocat/Hello-World",
        owner="octocat",
        name="Hello-World",
        status="ready",
    )


@pytest.fixture
def sample_review(sample_repository: Repository) -> Review:
    review_id = uuid.uuid4()
    review = Review(
        id=review_id,
        repository_id=sample_repository.id,
        user_id=sample_repository.user_id,
        status=ReviewStatus.COMPLETED.value,
        review_type=ReviewType.STATIC.value,
        files_analyzed=1,
        issues_count=1,
        overall_score=85.0,
        summary="Found one security issue.",
        created_at=datetime(2026, 7, 12, tzinfo=UTC),
    )
    review.file_results = [
        FileAnalysisResult(
            review_id=review_id,
            file_path="main.py",
            language="python",
            line_count=10,
            issues_count=1,
            file_score=85.0,
        )
    ]
    review.issues = [
        ReviewIssue(
            review_id=review_id,
            file_path="main.py",
            line_start=3,
            line_end=None,
            category="security",
            severity="high",
            confidence=0.9,
            rule_id="python:eval",
            title="Unsafe eval",
            explanation="eval is dangerous",
            suggestion="Use ast.literal_eval",
        )
    ]
    return review


def test_build_markdown(sample_review: Review, sample_repository: Repository) -> None:
    markdown = ReportService.build_markdown(sample_review, sample_repository)
    assert "# Code Review Report" in markdown
    assert "Unsafe eval" in markdown
    assert "main.py" in markdown


def test_build_json(sample_review: Review, sample_repository: Repository) -> None:
    payload = ReportService.build_json(sample_review, sample_repository)
    assert payload["repository"]["owner"] == "octocat"
    assert len(payload["issues"]) == 1
    assert payload["review"]["overall_score"] == 85.0


def test_build_summary(sample_review: Review, sample_repository: Repository) -> None:
    summary = ReportService.build_summary(sample_review, sample_repository)
    assert "security issue" in summary


def test_filename(sample_review: Review, sample_repository: Repository) -> None:
    name = ReportService.filename(
        sample_repository,
        sample_review,
        ReportFormat.MARKDOWN,
    )
    assert name.endswith(".md")
    assert "octocat-Hello-World" in name
