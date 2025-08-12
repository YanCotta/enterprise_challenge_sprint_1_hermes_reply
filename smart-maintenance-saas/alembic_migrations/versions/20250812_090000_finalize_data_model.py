"""finalize_data_model

Revision ID: 20250812_090000
Revises: 20250811_120000
Create Date: 2025-08-12 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PGEnum


# revision identifiers, used by Alembic.
revision: str = "20250812_090000"
down_revision: Union[str, None] = "20250811_120000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure uuid extension is available
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # Create ENUM types if not present
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sensor_status') THEN
                CREATE TYPE sensor_status AS ENUM ('active','inactive','maintenance','decommissioned');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'alert_status') THEN
                CREATE TYPE alert_status AS ENUM ('open','acknowledged','resolved','ignored');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_status') THEN
                CREATE TYPE task_status AS ENUM ('pending','in_progress','completed','failed','cancelled');
            END IF;
        END$$;
        """
    )

    # sensors table
    op.create_table(
        'sensors',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('sensor_id', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('status', PGEnum('active','inactive','maintenance','decommissioned', name='sensor_status', create_type=False), nullable=False, server_default=sa.text("'active'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_unique_constraint('uq_sensors_sensor_id', 'sensors', ['sensor_id'])

    # anomaly_alerts: status enum + FK
    with op.batch_alter_table('anomaly_alerts') as batch_op:
        batch_op.alter_column(
            'status',
            existing_type=sa.String(length=50),
            type_=PGEnum('open','acknowledged','resolved','ignored', name='alert_status', create_type=False),
            postgresql_using='status::alert_status',
            existing_nullable=False
        )
    op.create_foreign_key(
        'fk_anomaly_alerts_sensor', 'anomaly_alerts', 'sensors', ['sensor_id'], ['sensor_id'], ondelete='RESTRICT'
    )

    # maintenance_tasks: add sensor_id, status enum + FK
    op.add_column('maintenance_tasks', sa.Column('sensor_id', sa.String(length=255), nullable=True))
    with op.batch_alter_table('maintenance_tasks') as batch_op:
        batch_op.alter_column(
            'status',
            existing_type=sa.String(length=50),
            type_=PGEnum('pending','in_progress','completed','failed','cancelled', name='task_status', create_type=False),
            postgresql_using='status::task_status',
            existing_nullable=False
        )
    op.create_foreign_key(
        'fk_maintenance_tasks_sensor', 'maintenance_tasks', 'sensors', ['sensor_id'], ['sensor_id'], ondelete='RESTRICT'
    )
    op.create_index('ix_maintenance_tasks_sensor_id', 'maintenance_tasks', ['sensor_id'], unique=False)

    # sensor_readings: FK to sensors, change PK to (timestamp, sensor_id) and drop id
    op.create_foreign_key(
        'fk_sensor_readings_sensor', 'sensor_readings', 'sensors', ['sensor_id'], ['sensor_id'], ondelete='RESTRICT'
    )
    try:
        op.drop_index(op.f('ix_sensor_readings_id'), table_name='sensor_readings')
    except Exception:
        pass
    try:
        op.drop_constraint('sensor_readings_pkey', 'sensor_readings', type_='primary')
    except Exception:
        pass
    with op.batch_alter_table('sensor_readings') as batch_op:
        try:
            batch_op.drop_column('id')
        except Exception:
            pass
    op.create_primary_key('sensor_readings_pkey', 'sensor_readings', ['timestamp', 'sensor_id'])
    op.execute("DROP SEQUENCE IF EXISTS public.sensor_readings_id_seq CASCADE;")


def downgrade() -> None:
    # sensor_readings: restore id and old PK
    try:
        op.drop_constraint('sensor_readings_pkey', 'sensor_readings', type_='primary')
    except Exception:
        pass
    with op.batch_alter_table('sensor_readings') as batch_op:
        batch_op.add_column(sa.Column('id', sa.Integer(), autoincrement=True, nullable=False))
    op.create_index(op.f('ix_sensor_readings_id'), 'sensor_readings', ['id'], unique=False)
    op.create_primary_key('sensor_readings_pkey', 'sensor_readings', ['id', 'timestamp'])
    try:
        op.drop_constraint('fk_sensor_readings_sensor', 'sensor_readings', type_='foreignkey')
    except Exception:
        pass

    # maintenance_tasks: drop FK/col, status back to varchar
    try:
        op.drop_index('ix_maintenance_tasks_sensor_id', table_name='maintenance_tasks')
    except Exception:
        pass
    try:
        op.drop_constraint('fk_maintenance_tasks_sensor', 'maintenance_tasks', type_='foreignkey')
    except Exception:
        pass
    with op.batch_alter_table('maintenance_tasks') as batch_op:
        try:
            batch_op.drop_column('sensor_id')
        except Exception:
            pass
        batch_op.alter_column('status', type_=sa.String(length=50), postgresql_using='status::text')

    # anomaly_alerts: drop FK and convert status back to varchar
    try:
        op.drop_constraint('fk_anomaly_alerts_sensor', 'anomaly_alerts', type_='foreignkey')
    except Exception:
        pass
    with op.batch_alter_table('anomaly_alerts') as batch_op:
        batch_op.alter_column('status', type_=sa.String(length=50), postgresql_using='status::text')

    # Drop sensors
    try:
        op.drop_constraint('uq_sensors_sensor_id', 'sensors', type_='unique')
    except Exception:
        pass
    op.drop_table('sensors')
