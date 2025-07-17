"""merge heads

Revision ID: e21acba162a4
Revises: rs_thresh_add_20250717, c2757b2a7133
Create Date: 2025-07-17 20:27:48.840798

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e21acba162a4'
down_revision: Union[str, Sequence[str], None] = ('rs_thresh_add_20250717', 'c2757b2a7133')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
