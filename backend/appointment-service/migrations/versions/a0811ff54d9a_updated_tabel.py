"""recreate appointment table with correct schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-03-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'appointment',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.UUID(), nullable=False),
        sa.Column('doctor_id', sa.UUID(), nullable=False),
        sa.Column('appointment_date', sa.Date(), nullable=False),
        sa.Column(
            'time_preference',
            sa.Enum('AM', 'PM', name='timepreference'),
            nullable=False,
        ),
        sa.Column('assigned_time', sa.Time(), nullable=True),
        sa.Column(
            'status',
            sa.Enum(
                'scheduled',
                'handed_off',
                'completed',
                'cancelled',
                name='appointmentstatus',
            ),
            nullable=False,
            server_default='scheduled',
        ),
        sa.Column('notes', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('appointment')
    op.execute('DROP TYPE IF EXISTS appointmentstatus')
    op.execute('DROP TYPE IF EXISTS timepreference')