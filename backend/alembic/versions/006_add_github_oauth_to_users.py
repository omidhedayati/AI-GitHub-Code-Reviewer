"""Add GitHub OAuth fields to users

Revision ID: 006
Revises: 005
Create Date: 2026-07-12

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("users", "hashed_password", existing_type=sa.String(255), nullable=True)
    op.add_column("users", sa.Column("github_id", sa.BigInteger(), nullable=True))
    op.add_column("users", sa.Column("github_username", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(length=512), nullable=True))
    op.add_column(
        "users",
        sa.Column("auth_provider", sa.String(length=32), nullable=False, server_default="local"),
    )
    op.create_index("ix_users_github_id", "users", ["github_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_github_id", table_name="users")
    op.drop_column("users", "auth_provider")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "github_username")
    op.drop_column("users", "github_id")
    op.alter_column("users", "hashed_password", existing_type=sa.String(255), nullable=False)
