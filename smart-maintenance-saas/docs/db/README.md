# Database Model Documentation

This document describes the finalized relational model for Smart Maintenance SaaS. It complements the ER diagram and the SQL schema.

Key updates as of 2025-08-12:

- Introduced a central `sensors` table as the source of truth for assets.
- Standardized foreign keys using `sensor_id` across dependent tables.
- Adopted database ENUMs for status fields to enforce integrity.
- Corrected the time-series primary key to `(timestamp, sensor_id)` for TimescaleDB alignment.

## Entities

### sensors (new)

- id (uuid, PK, default gen_random_uuid())
- sensor_id (varchar(255), unique, not null) — business identifier
- type (varchar(50), not null)
- location (varchar(255))
- status (enum sensor_status, default 'active')
- created_at, updated_at (timestamptz, defaults)
- Rationale: single source of truth for sensor metadata and lifecycle status.

### sensor_readings (Timescale hypertable)

- timestamp (timestamptz, PK part)
- sensor_id (varchar(255), PK part, not null) — FK to sensors.sensor_id
- value (float8, not null)
- unit (varchar(50))
- Rationale: raw time-series readings. Composite PK aligns with Timescale chunking and avoids surrogate id contention.

### anomaly_alerts

- id (uuid, PK)
- sensor_id (varchar(255), not null) — FK to sensors.sensor_id
- anomaly_type (varchar(100), not null)
- severity (int, 1..5)
- description (text)
- evidence (jsonb)
- status (enum alert_status, default 'open')
- created_at, updated_at
- Rationale: captures anomaly detection events and triage status.

### maintenance_tasks

- id (uuid, PK)
- sensor_id (varchar(255), not null) — FK to sensors.sensor_id
- task_type (varchar(100), not null)
- description (text)
- priority (int, default 3)
- status (enum task_status, default 'pending')
- scheduled_start_time (timestamptz)
- created_at, updated_at
- Rationale: streamlined tasks tied to specific sensors.

### maintenance_logs

- id (uuid, PK)
- task_id (uuid, not null) — FK to maintenance_tasks.id
- technician_id (varchar(255), not null)
- notes (text)
- actual_duration_hours (float8)
- completion_date (timestamptz, default now())
- created_at, updated_at
- Rationale: immutable log of executed maintenance activities.

## Enums

- task_status: pending | in_progress | completed | failed | cancelled
- alert_status: open | acknowledged | resolved | ignored
- sensor_status: active | inactive | maintenance | decommissioned

## Constraints and Indexes

- sensor_readings: PK (timestamp, sensor_id); indexes on (sensor_id), (timestamp) as needed per queries.
- anomaly_alerts: index (sensor_id).
- maintenance_tasks: index (sensor_id).
- maintenance_logs: index (task_id).
- sensors: unique (sensor_id).

## TimescaleDB Policies

- Retention: drop data older than 180 days (configurable).
- Compression: enable compression and compress chunks older than 7 days.
- Optional CAGGs: 1-minute rollups for faster analytics.

## ERD and Schema

- ERD source: `docs/db/erd.dbml`
- ERD image: `docs/db/erd.png` (exported from DBML tool)
- SQL schema: `docs/db/schema.sql` (aligned to ERD; migrations may evolve iteratively)

## Future Visualization

- Suitable for Grafana/TimescaleDB + Streamlit. Continuous aggregates simplify BI.
