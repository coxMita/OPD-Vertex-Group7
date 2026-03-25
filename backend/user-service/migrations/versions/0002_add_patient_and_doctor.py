"""Add patient and doctor tables

Revision ID: 0002_add_patient_and_doctor
Revises: 0001_initial
Create Date: 2026-03-25 22:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_add_patient_and_doctor'
down_revision: Union[str, Sequence[str], None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Patient table
    op.create_table('patient',
    sa.Column('patient_id', sa.Uuid(), nullable=False),
    sa.Column('first_name', sa.String(), nullable=False),
    sa.Column('last_name', sa.String(), nullable=False),
    sa.Column('date_of_birth', sa.Date(), nullable=False),
    sa.Column('gender', sa.String(), nullable=False),
    sa.Column('phone_number', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('patient_id'),
    sa.UniqueConstraint('patient_id')
    )
    op.create_index(op.f('ix_patient_patient_id'), 'patient', ['patient_id'], unique=False)

    # Doctor table
    op.create_table('doctor',
    sa.Column('doctor_id', sa.Uuid(), nullable=False),
    sa.Column('full_name', sa.String(), nullable=False),
    sa.Column('department_name', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('keycloak_id', sa.Uuid(), nullable=False),
    sa.PrimaryKeyConstraint('doctor_id'),
    sa.UniqueConstraint('doctor_id'),
    sa.UniqueConstraint('keycloak_id')
    )
    op.create_index(op.f('ix_doctor_doctor_id'), 'doctor', ['doctor_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_doctor_doctor_id'), table_name='doctor')
    op.drop_table('doctor')
    op.drop_index(op.f('ix_patient_patient_id'), table_name='patient')
    op.drop_table('patient')
