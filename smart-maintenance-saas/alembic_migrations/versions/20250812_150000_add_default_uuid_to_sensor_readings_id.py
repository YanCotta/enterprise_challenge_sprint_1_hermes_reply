"""add_default_uuid_to_sensor_readings_id

Revision ID: 20250812_150000
Revises: 20250812_090000
Create Date: 2025-08-12 15:00:00.000000

"""
from typing import Sequence, Union

# NO-OP MIGRATION
# This migration was originally intended to alter / add defaults for sensor_readings.id.
# Current live schema diverged (composite PK on (timestamp, sensor_id)) making the
# original operations unsafe and causing failed transactions on startup.
# Per recovery plan (Day 12 stabilization) this file has been neutralized to
# preserve migration chain continuity without performing schema changes.
# Future adjustments should create a fresh migration rather than reactivating this one.

from alembic import op  # noqa: F401 (kept for consistency/reference)
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = "20250812_150000"
down_revision: Union[str, None] = "20250812_090000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:  # pragma: no cover
    """NO-OP: intentionally left blank (see header comment)."""
    pass


def downgrade() -> None:  # pragma: no cover
    """NO-OP reverse of a no-op migration."""
    pass
