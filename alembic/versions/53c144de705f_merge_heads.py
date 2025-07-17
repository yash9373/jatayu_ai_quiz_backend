"""merge heads

Revision ID: 53c144de705f
Revises: e21acba162a4, rs_thresh_nullable_20250717
Create Date: 2025-07-17 20:48:17.799482

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53c144de705f'
down_revision: Union[str, Sequence[str], None] = ('e21acba162a4', 'rs_thresh_nullable_20250717')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
