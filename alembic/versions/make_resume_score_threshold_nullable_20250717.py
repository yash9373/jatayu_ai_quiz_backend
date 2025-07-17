"""Make resume_score_threshold nullable in tests table

Revision ID: rs_thresh_nullable_20250717
Revises: rs_thresh_add_20250717
Create Date: 2025-07-17
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'rs_thresh_nullable_20250717'
down_revision = 'rs_thresh_add_20250717'
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column('tests', 'resume_score_threshold', existing_type=sa.Integer(), nullable=True)

def downgrade():
    op.alter_column('tests', 'resume_score_threshold', existing_type=sa.Integer(), nullable=False)
