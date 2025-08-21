"""Add sensor_readings composite index for performance

Revision ID: 4a7245cea299
Revises: 20250812_090000
Create Date: 2025-08-21 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4a7245cea299'
down_revision: Union[str, None] = '20250812_090000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add high-performance composite index (sensor_id first for filtering, timestamp DESC for recent-first scans)
    # Not using CONCURRENTLY here because Alembic wraps in a transaction; table size is currently modest.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_sensor_readings_sensor_timestamp ON sensor_readings (sensor_id, timestamp DESC)"
    )


def downgrade() -> None:
    op.execute(
        "DROP INDEX IF EXISTS ix_sensor_readings_sensor_timestamp"
    )