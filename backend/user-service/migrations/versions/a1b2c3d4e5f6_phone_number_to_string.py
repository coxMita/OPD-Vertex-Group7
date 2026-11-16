"""phone_number to string

Revision ID: a1b2c3d4e5f6
Revises: cbfedb7c9bf4
Create Date: 2026-11-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "cbfedb7c9bf4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Store phone numbers as text (+45..., leading zeros, >10 digits)."""
    op.alter_column(
        "patient",
        "phone_number",
        existing_type=sa.Integer(),
        type_=sa.String(),
        existing_nullable=False,
        postgresql_using="phone_number::text",
    )


def downgrade() -> None:
    """Revert to integer (fails if any value is not numeric)."""
    op.alter_column(
        "patient",
        "phone_number",
        existing_type=sa.String(),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using="phone_number::integer",
    )