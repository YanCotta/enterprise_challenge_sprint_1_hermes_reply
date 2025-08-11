"""add_timescale_policies

Revision ID: 20250811_120000
Revises: 2a6b3cf9a7fc
Create Date: 2025-08-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20250811_120000"
down_revision: Union[str, None] = "2a6b3cf9a7fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure Timescale extension exists (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

    # Add retention and compression policies to sensor_readings hypertable
    # Retain 180 days
    op.execute(
        "SELECT add_retention_policy('sensor_readings', INTERVAL '180 days');"
    )

    # Enable compression and compress chunks older than 7 days
    op.execute(
        "ALTER TABLE sensor_readings SET (timescaledb.compress);"
    )
    op.execute(
        "SELECT add_compression_policy('sensor_readings', INTERVAL '7 days');"
    )

    # Optional: create a 1-minute continuous aggregate for quick charts (commented)
    # op.execute(
    #     """
    #     CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_readings_1m
    #     WITH (timescaledb.continuous) AS
    #     SELECT time_bucket('1 minute', timestamp) AS bucket,
    #            sensor_id,
    #            avg(value) AS avg_value,
    #            min(value) AS min_value,
    #            max(value) AS max_value
    #     FROM sensor_readings
    #     GROUP BY bucket, sensor_id;
    #     """
    # )


def downgrade() -> None:
    # Remove policies; keep extension installed
    op.execute(
        "SELECT remove_retention_policy('sensor_readings');"
    )
    op.execute(
        "SELECT remove_compression_policy('sensor_readings');"
    )
    # Optionally drop CAGG
    # op.execute("DROP MATERIALIZED VIEW IF EXISTS sensor_readings_1m;")
