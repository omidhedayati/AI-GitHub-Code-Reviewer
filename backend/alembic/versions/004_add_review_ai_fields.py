"""Add AI review fields to reviews table

Revision ID: 004
Revises: 003
Create Date: 2026-07-12

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "reviews",
        sa.Column(
            "review_type",
            sa.String(length=32),
            nullable=False,
            server_default="static",
        ),
    )
    op.add_column(
        "reviews",
        sa.Column("ai_model", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "reviews",
        sa.Column("report_markdown", sa.Text(), nullable=True),
    )
    op.create_index("ix_reviews_review_type", "reviews", ["review_type"])


def downgrade() -> None:
    op.drop_index("ix_reviews_review_type", table_name="reviews")
    op.drop_column("reviews", "report_markdown")
    op.drop_column("reviews", "ai_model")
    op.drop_column("reviews", "review_type")
