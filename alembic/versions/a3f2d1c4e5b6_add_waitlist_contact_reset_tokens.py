"""add waitlist, contact, and reset token columns

Revision ID: a3f2d1c4e5b6
Revises: b175bc530c5d
Create Date: 2026-05-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3f2d1c4e5b6'
down_revision: Union[str, Sequence[str], None] = 'b175bc530c5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users: reset-password token columns
    op.add_column('users', sa.Column('reset_token_hash', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('reset_token_expires', sa.DateTime(), nullable=True))

    # waitlist_entries
    op.create_table(
        'waitlist_entries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('marketing_consent', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_waitlist_entries_email', 'waitlist_entries', ['email'], unique=True)

    # contact_messages
    op.create_table(
        'contact_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('contact_messages')
    op.drop_index('ix_waitlist_entries_email', table_name='waitlist_entries')
    op.drop_table('waitlist_entries')
    op.drop_column('users', 'reset_token_expires')
    op.drop_column('users', 'reset_token_hash')
