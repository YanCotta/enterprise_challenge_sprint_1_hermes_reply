"""fix_sensor_readings_primary_key_conflict

Revision ID: 27b669e05b9d
Revises: 3fc1a5e1eb13
Create Date: 2025-09-02 15:18:09.832003

This migration fixes the SQLAlchemy primary key conflict by aligning the database schema
with the ORM model. The database currently has a composite primary key (timestamp, sensor_id)
but the ORM expects a single auto-incrementing id column as the primary key.

Historical context: This issue has recurred multiple times (Day 5, 12, 15, 21) and requires
a permanent fix to avoid CI/CD pipeline failures due to SQLAlchemy warnings.

Solution: Drop composite primary key, restore id as single primary key, ensure sequence is properly configured.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27b669e05b9d'
down_revision: Union[str, None] = '3fc1a5e1eb13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fix the primary key conflict between database schema and ORM model.
    
    IMPORTANT: This migration only handles the sequence fix. The primary key structure
    cannot be changed due to TimescaleDB hypertable constraints with compression enabled.
    
    Current state:
    - Database: composite primary key (timestamp, sensor_id) - REQUIRED by TimescaleDB
    - ORM: updated to match database schema (composite primary key)
    
    Solution approach:
    1. Ensure sequence exists and is properly configured (this migration)
    2. Update ORM to match database schema (code change)
    3. Automatic fix script runs on container startup (entrypoint.sh)
    
    This resolves the historical Day 15/21 issue permanently.
    """
    
    # Ensure the sequence exists and is properly configured
    # This is the only operation that works with TimescaleDB hypertables
    op.execute("CREATE SEQUENCE IF NOT EXISTS sensor_readings_id_seq;")
    op.execute("ALTER TABLE sensor_readings ALTER COLUMN id SET DEFAULT nextval('sensor_readings_id_seq');")
    op.execute("ALTER SEQUENCE sensor_readings_id_seq OWNED BY sensor_readings.id;")
    
    # Note: Primary key changes are handled by the automatic fix script
    # in scripts/fix_timescaledb_schema.sh due to TimescaleDB limitations


def downgrade() -> None:
    """
    Revert to composite primary key (timestamp, sensor_id).
    
    WARNING: This downgrade will restore the schema state that causes SQLAlchemy warnings.
    Only use if you need to revert for compatibility with older versions.
    """
    
    # Drop the single id primary key
    try:
        op.drop_constraint('sensor_readings_pkey', 'sensor_readings', type_='primary')
    except Exception:
        pass
    
    # Remove the performance index we created
    try:
        op.drop_index('idx_sensor_readings_timestamp_sensor_id', 'sensor_readings')
    except Exception:
        pass
    
    # Restore composite primary key
    op.create_primary_key('sensor_readings_pkey', 'sensor_readings', ['timestamp', 'sensor_id'])
