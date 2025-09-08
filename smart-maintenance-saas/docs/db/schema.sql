-- Smart Maintenance SaaS - Database Schema
-- PostgreSQL + TimescaleDB schema generated to match ORM models
-- This script is idempotent where possible and safe to run multiple times. 
-- It creates necessary extensions, types, sequences, tables, and indexes.
-- There are also alembic migration scripts for schema evolution over time.
-- Run this script in psql or a database migration tool. Or use the ORM migrations.

BEGIN;

-- Required extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enum types used by ORM and extended schema
DO $$
BEGIN
	IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'maintenancetaskstatus') THEN
		CREATE TYPE maintenancetaskstatus AS ENUM (
			'PENDING', 'IN_PROGRESS', 'COMPLETED', 'PARTIALLY_COMPLETED', 'FAILED', 'CANCELLED'
		);
	END IF;
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

-- Sequences
CREATE SEQUENCE IF NOT EXISTS sensor_readings_id_seq;

-- Tables

-- sensors: registry of devices emitting readings
CREATE TABLE IF NOT EXISTS sensors (
	id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
	sensor_id varchar(255) NOT NULL,
	type varchar(50) NOT NULL,
	location varchar(255) NULL,
	status sensor_status NOT NULL DEFAULT 'active',
	created_at timestamptz DEFAULT now(),
	updated_at timestamptz DEFAULT now()
);

DO $$
BEGIN
	IF NOT EXISTS (
		SELECT 1 FROM pg_constraint WHERE conname = 'uq_sensors_sensor_id'
	) THEN
		ALTER TABLE sensors ADD CONSTRAINT uq_sensors_sensor_id UNIQUE (sensor_id);
	END IF;
END$$;

-- anomaly_alerts: alerts raised by anomaly detection agents
CREATE TABLE IF NOT EXISTS anomaly_alerts (
	id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
	sensor_id varchar(255) NOT NULL,
	anomaly_type varchar(100) NOT NULL,
	severity integer NOT NULL,
	confidence double precision NULL,
	description text NULL,
	evidence jsonb NULL,
	recommended_actions text[] NULL,
	status alert_status NOT NULL DEFAULT 'open',
	created_at timestamptz DEFAULT now(),
	updated_at timestamptz DEFAULT now(),
	CONSTRAINT fk_anomaly_alerts_sensor FOREIGN KEY (sensor_id) REFERENCES sensors(sensor_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS ix_anomaly_alerts_id ON anomaly_alerts (id);
CREATE INDEX IF NOT EXISTS ix_anomaly_alerts_sensor_id ON anomaly_alerts (sensor_id);

-- maintenance_tasks: tasks created to act on alerts/equipment
CREATE TABLE IF NOT EXISTS maintenance_tasks (
	id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
	equipment_id varchar(255) NOT NULL,
	task_type varchar(100) NOT NULL,
	description text NULL,
	priority integer NOT NULL DEFAULT 3,
	status task_status NOT NULL DEFAULT 'pending',
	estimated_duration_hours double precision NULL,
	actual_duration_hours double precision NULL,
	required_skills text[] NULL,
	parts_needed text[] NULL,
	assigned_technician_id varchar(255) NULL,
	scheduled_start_time timestamptz NULL,
	scheduled_end_time timestamptz NULL,
	actual_start_time timestamptz NULL,
	actual_end_time timestamptz NULL,
	notes text NULL,
	sensor_id varchar(255) NULL,
	created_at timestamptz DEFAULT now(),
	updated_at timestamptz DEFAULT now(),
	CONSTRAINT fk_maintenance_tasks_sensor FOREIGN KEY (sensor_id) REFERENCES sensors(sensor_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS ix_maintenance_tasks_id ON maintenance_tasks (id);
CREATE INDEX IF NOT EXISTS ix_maintenance_tasks_equipment_id ON maintenance_tasks (equipment_id);
CREATE INDEX IF NOT EXISTS ix_maintenance_tasks_sensor_id ON maintenance_tasks (sensor_id);

-- maintenance_logs: historical records of completed work
CREATE TABLE IF NOT EXISTS maintenance_logs (
	id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
	task_id uuid NOT NULL,
	equipment_id varchar(255) NOT NULL,
	completion_date timestamptz NOT NULL,
	technician_id varchar(255) NOT NULL,
	notes text NULL,
	status maintenancetaskstatus NOT NULL DEFAULT 'COMPLETED',
	actual_duration_hours double precision NULL,
	created_at timestamptz DEFAULT now(),
	updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_maintenance_logs_id ON maintenance_logs (id);
CREATE INDEX IF NOT EXISTS ix_maintenance_logs_task_id ON maintenance_logs (task_id);
CREATE INDEX IF NOT EXISTS ix_maintenance_logs_equipment_id ON maintenance_logs (equipment_id);

-- sensor_readings: time-series measurements (TimescaleDB hypertable)
CREATE TABLE IF NOT EXISTS sensor_readings (
	id integer NOT NULL DEFAULT nextval('sensor_readings_id_seq'),
	sensor_id varchar(255) NOT NULL,
	sensor_type varchar(50) NOT NULL,
	value double precision NOT NULL,
	unit varchar(50) NULL,
	timestamp timestamptz NOT NULL,
	quality double precision NULL,
	sensor_metadata jsonb NULL,
	created_at timestamptz DEFAULT now(),
	updated_at timestamptz DEFAULT now(),
	CONSTRAINT sensor_readings_pkey PRIMARY KEY (timestamp, sensor_id),
	CONSTRAINT fk_sensor_readings_sensor FOREIGN KEY (sensor_id) REFERENCES sensors(sensor_id) ON DELETE RESTRICT
);

-- Ensure sequence ownership (idempotent)
DO $$
BEGIN
	PERFORM 1 FROM pg_class c
	JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'id'
	WHERE c.relname = 'sensor_readings';
	-- Own the sequence (safe if already owned)
	EXECUTE 'ALTER SEQUENCE sensor_readings_id_seq OWNED BY sensor_readings.id';
EXCEPTION WHEN OTHERS THEN
	-- No-op on error to keep script idempotent
	NULL;
END$$;

-- Indexes for sensor_readings
CREATE INDEX IF NOT EXISTS ix_sensor_readings_sensor_id ON sensor_readings (sensor_id);
CREATE INDEX IF NOT EXISTS ix_sensor_readings_timestamp ON sensor_readings (timestamp);
-- High-performance composite index for recent-first scans per sensor
CREATE INDEX IF NOT EXISTS idx_sensor_readings_sensor_timestamp ON sensor_readings (sensor_id, timestamp DESC);
-- Optional timestamp-only DESC index used by ML queries
CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp ON sensor_readings (timestamp DESC);

-- Convert table to TimescaleDB hypertable (no-op if already hypertable)
SELECT create_hypertable('sensor_readings', 'timestamp', if_not_exists => TRUE);

COMMIT;

