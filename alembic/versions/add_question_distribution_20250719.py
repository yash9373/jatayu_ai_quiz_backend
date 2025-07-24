"""Add question_distribution column to tests table (nullable JSON)

Revision ID: add_question_distribution_20250719
Revises: rs_thresh_add_20250717
Create Date: 2025-07-19
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_question_distribution_20250719'
down_revision = 'rs_thresh_add_20250717'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('tests', sa.Column('question_distribution', sa.JSON(), nullable=True))

def downgrade():
    op.drop_column('tests', 'question_distribution')
