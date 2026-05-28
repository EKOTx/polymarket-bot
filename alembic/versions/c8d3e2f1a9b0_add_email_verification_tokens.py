"""Add email verification token columns to users

Revision ID: c8d3e2f1a9b0
Revises: a3f2d1c4e5b6
Create Date: 2026-05-28

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "c8d3e2f1a9b0"
down_revision = "a3f2d1c4e5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("verification_token_hash", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("verification_token_expires", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "verification_token_expires")
    op.drop_column("users", "verification_token_hash")
