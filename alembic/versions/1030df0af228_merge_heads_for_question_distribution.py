"""Merge heads for question_distribution

Revision ID: 1030df0af228
Revises: 53c144de705f, add_question_distribution_20250719
Create Date: 2025-07-19 12:39:11.527655

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1030df0af228'
down_revision: Union[str, Sequence[str], None] = ('53c144de705f', 'add_question_distribution_20250719')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
