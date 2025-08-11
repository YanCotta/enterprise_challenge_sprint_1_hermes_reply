# Database Model Documentation

This document describes the relational model used by Smart Maintenance SaaS. It complements the ER diagram and the initial SQL schema.

## Entities

### sensor_readings

- id (int, PK, auto-increment)
- timestamp (timestamptz, PK)
- sensor_id (varchar(255), indexed, not null)
- sensor_type (varchar(50), not null)
- value (float8, not null)
- unit (varchar(50))
- quality (float8, default 1.0)
- sensor_metadata (jsonb)
- created_at, updated_at (timestamptz, defaults)
- Rationale: time-series hypertable for raw sensor readings. PK includes time for TimescaleDB.

### anomaly_alerts

- id (uuid, PK)
- sensor_id (varchar(255), indexed, not null)
- anomaly_type (varchar(100), not null)
- severity (int, 1..5)
- confidence (float8, 0..1)
- description (text)
- evidence (jsonb)
- recommended_actions (varchar[])
- status (varchar(50), default 'open')
- created_at, updated_at
- Rationale: captures anomaly detection events and human/auto triage.

### maintenance_tasks

- id (uuid, PK)
- equipment_id (varchar(255), indexed)
- task_type (varchar(100), not null)
- description (text)
- priority (int, default 3)
- status (varchar(50), default 'pending')
- estimated_duration_hours (float8)
- actual_duration_hours (float8)
- required_skills (varchar[])
- parts_needed (varchar[])
- assigned_technician_id (varchar(255))
- scheduled_start_time, scheduled_end_time, actual_start_time, actual_end_time
- notes (text)
- created_at, updated_at
- Rationale: workflow entity for maintenance operations.

### maintenance_logs

- id (uuid, PK)
- task_id (uuid, indexed)
- equipment_id (varchar(255), indexed)
- completion_date (timestamptz)
- technician_id (varchar(255))
- notes (text)
- status (enum MaintenanceTaskStatus)
- actual_duration_hours (float8)
- created_at, updated_at
- Rationale: immutable log of executed tasks for audit and analytics.

## Constraints and Indexes

- sensor_readings: composite PK (id, timestamp); indexes on (sensor_id), (timestamp), and composite (sensor_id, timestamp desc).
- anomaly_alerts: indexes on (id), (sensor_id).
- maintenance_tasks: indexes on (id), (equipment_id).
- maintenance_logs: indexes on (id), (task_id), (equipment_id).

## TimescaleDB Policies

- Retention: drop data older than 180 days (configurable).
- Compression: enable compression and compress chunks older than 7 days.
- Optional CAGGs: 1-minute rollups for faster analytics.

## ERD and Schema

- ERD source: `docs/db/erd.dbml`
- ERD image: `docs/db/erd.png` (generate via script or modeling tool)
- Initial SQL: `docs/db/schema.sql` (exported from live DB)

## Future Visualization

- Suitable for Grafana/TimescaleDB + Streamlit. Continuous aggregates simplify BI.
