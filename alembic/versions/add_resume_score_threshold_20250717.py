"""Add resume_score_threshold column to tests table (nullable)

Revision ID: rs_thresh_add_20250717
Revises: 83817c05fd42
Create Date: 2025-07-17
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'rs_thresh_add_20250717'
down_revision = '83817c05fd42'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('tests', sa.Column('resume_score_threshold', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('tests', 'resume_score_threshold')
