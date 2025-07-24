"""
Alembic migration to merge heads: 1030df0af228 and add_test_status_enum_and_timestamps_20250721
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'merge_heads_for_test_status_20250721'
down_revision = ('1030df0af228', 'add_test_status_enum_and_timestamps_20250721')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
