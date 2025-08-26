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
    
    # Create Continuous Aggregate for hourly summaries
    # Note: TimescaleDB continuous aggregates must be created outside transactions
    connection = op.get_bind()
    connection.execute(sa.text("COMMIT"))  # End current transaction
    
    connection.execute(sa.text("""
        CREATE MATERIALIZED VIEW sensor_readings_summary_hourly
        WITH (timescaledb.continuous) AS
        SELECT
            sensor_id,
            time_bucket('1 hour', timestamp) as bucket,
            AVG(value) as avg_value,
            MAX(value) as max_value,
            MIN(value) as min_value,
            COUNT(*) as num_readings
        FROM
            sensor_readings
        GROUP BY
            sensor_id, bucket
    """))
    
    # Add refresh policy for the CAGG (refresh every 30 minutes)
    connection.execute(sa.text("""
        SELECT add_continuous_aggregate_policy('sensor_readings_summary_hourly',
            start_offset => INTERVAL '3 hours',
            end_offset => INTERVAL '1 hour',
            schedule_interval => INTERVAL '30 minutes')
    """))


def downgrade() -> None:
    # Remove the continuous aggregate refresh policy
    op.execute("""
        SELECT remove_continuous_aggregate_policy('sensor_readings_summary_hourly')
    """)
    
    # Drop the continuous aggregate view
    op.execute("""
        DROP MATERIALIZED VIEW IF EXISTS sensor_readings_summary_hourly
    """)
    
    # Drop the indexes
    op.execute("""
        DROP INDEX IF EXISTS idx_sensor_readings_timestamp
    """)
    
    op.execute("""
        DROP INDEX IF EXISTS idx_sensor_readings_sensor_timestamp
    """)