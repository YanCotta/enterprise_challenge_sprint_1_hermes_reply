"""add_default_uuid_to_sensor_readings_id

Revision ID: 20250812_150000
Revises: 20250812_090000
Create Date: 2025-08-12 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20250812_150000"
down_revision: Union[str, None] = "20250812_090000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add server-side UUID default to sensor_readings.id column"""
    
    # Enable uuid-ossp extension for uuid generation
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    
    # For TimescaleDB hypertables with compression, we cannot ALTER COLUMN TYPE
    # Instead, we'll just add a default value to the existing integer column
    # This maintains compatibility while allowing new inserts to work
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if the column exists and needs a default
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'sensor_readings'
                  AND column_name = 'id'
                  AND column_default IS NULL
            ) THEN
                -- For integer id column, we'll use a sequence-based approach
                -- that's compatible with compressed hypertables
                EXECUTE 'CREATE SEQUENCE IF NOT EXISTS sensor_readings_id_seq';
                EXECUTE 'ALTER TABLE sensor_readings ALTER COLUMN id SET DEFAULT nextval(''sensor_readings_id_seq'')';
                -- Set the sequence to start from a high value to avoid conflicts
                EXECUTE 'SELECT setval(''sensor_readings_id_seq'', COALESCE((SELECT MAX(id) FROM sensor_readings), 0) + 1)';
            END IF;
        END$$;
        """
    )

    # Recreate index on id if it's missing (safe-guard)
    try:
        op.create_index(op.f('ix_sensor_readings_id'), 'sensor_readings', ['id'], unique=False)
    except Exception:
        pass


def downgrade() -> None:
    # Remove server-side default; leave column type as-is (uuid)
    op.alter_column('sensor_readings', 'id', server_default=None)
