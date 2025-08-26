"""add_continuous_aggregates_and_indices_for_sensor_readings

Revision ID: 0907b6dcc25b
Revises: 20250812_150000
Create Date: 2025-08-26 19:29:38.573638

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0907b6dcc25b'
down_revision: Union[str, None] = '20250812_150000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create indexes for improved ML query performance
    
    # Index for sensor_id + timestamp queries (most common ML pattern)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_sensor_readings_sensor_timestamp 
        ON sensor_readings (sensor_id, timestamp DESC)
    """)
    
    # Index for timestamp-only queries (time range filtering)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp 
        ON sensor_readings (timestamp DESC)
    """)
    
    # Note: TimescaleDB continuous aggregates cannot be created within Alembic transactions
    # They must be created manually via direct psql commands as documented in:
    # - DAY_18_PERFORMANCE_RESULTS.md
    # - 30-day-sprint-changelog.md (Day 18 section)
    # 
    # Manual commands used for production deployment:
    # 1. CREATE MATERIALIZED VIEW sensor_readings_summary_hourly...
    # 2. SELECT add_continuous_aggregate_policy(...)
    #
    # This limitation is due to TimescaleDB requiring continuous aggregates
    # to be created outside of transaction blocks, while Alembic wraps
    # all DDL operations in transactions.


def downgrade() -> None:
    # Note: TimescaleDB continuous aggregate and refresh policy removal
    # cannot be performed within Alembic transactions.
    # 
    # For manual downgrade, use these commands via psql:
    # 1. SELECT remove_continuous_aggregate_policy('sensor_readings_summary_hourly');
    # 2. DROP MATERIALIZED VIEW IF EXISTS sensor_readings_summary_hourly CASCADE;
    #
    # Only the indexes can be safely removed via Alembic:
    
    # Drop the indexes (safe within transactions)
    op.execute("""
        DROP INDEX IF EXISTS idx_sensor_readings_timestamp
    """)
    
    op.execute("""
        DROP INDEX IF EXISTS idx_sensor_readings_sensor_timestamp
    """)