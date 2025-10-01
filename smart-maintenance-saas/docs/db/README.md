# Database Architecture (TimescaleDB Production Design)

**Last Updated:** 2025-09-30  
**Status:** V1.0 Production Ready  
**Related Documentation:**
- [v1_release_must_do.md Section 2.1](../v1_release_must_do.md) - Database in backend capability matrix
- [Sprint 4 Changelog](../legacy/sprint_4_changelog.md) - Cloud TimescaleDB deployment achievements
- [SYSTEM_AND_ARCHITECTURE.md](../SYSTEM_AND_ARCHITECTURE.md) - High-level architecture

Authoritative description of the production time-series data layer powering ingestion, ML feature extraction, drift detection, and analytics. Cloud deployment on Render with TimescaleDB extension enabled.

#### Core Tables (Quick Summary)

- sensors: Asset registry of physical/virtual devices.
  - Key: `sensor_id` (unique business identifier), surrogate `id` (UUID)
  - Fields: `type`, `location`, `status`, timestamps
- sensor_readings: Time-series measurements (TimescaleDB hypertable).
  - PK: `(timestamp, sensor_id)`; surrogate `id` (sequence-backed, non-PK)
  - Fields: `sensor_type`, `value`, `unit`, `quality`, `sensor_metadata`, timestamps
  - Indexes: `(sensor_id, timestamp DESC)` for latest-N windows; `(timestamp)` for range scans
- anomaly_alerts: Events produced by anomaly detection.
  - PK: `id` (UUID)
  - Fields: `sensor_id`, `anomaly_type`, `severity`, `confidence`, `description`, `evidence` (JSONB), `recommended_actions` (text[]), `status`
  - Rel: FK to `sensors(sensor_id)`
- maintenance_tasks: Work items to address issues or scheduled upkeep.
  - PK: `id` (UUID)
  - Fields: `equipment_id`, `task_type`, `priority`, `status`, scheduling times, `required_skills` (text[]), `parts_needed` (text[]), timestamps
  - Rel: optional FK to `sensors(sensor_id)`; indexed on `equipment_id` and `sensor_id`
- maintenance_logs: Execution records capturing actual work performed.
  - PK: `id` (UUID)
  - Fields: `task_id`, `equipment_id`, `completion_date`, `technician_id`, `status`, `actual_duration_hours`, `notes`, timestamps
  - Rel: logically references `maintenance_tasks(id)` via `task_id`

Relationships at a glance:

- sensors 1:N sensor_readings
- sensors 1:N anomaly_alerts
- sensors 0..1:N maintenance_tasks (optional link by `sensor_id`)
- maintenance_tasks 1:N maintenance_logs (via `task_id`)

---

## 1. Purpose

Deliver a resilient, low‑latency, evolvable storage layer for:
- High‑volume sensor ingestion (predictive maintenance telemetry)
- Efficient sliding window & recent-history ML queries
- Pre‑aggregated statistics to reduce CPU and IO during analytics
- Lifecycle management (retention + compression) to control cost

---

## 2. Architectural Principles

| Principle | Implementation |
|-----------|----------------|
| Time-series native | TimescaleDB hypertable (`sensor_readings`) |
| Query locality | Composite descending index `(sensor_id, timestamp DESC)` |
| Pre-compute heavy scans | Continuous Aggregate (hourly) with refresh policy |
| Operational safety | Alembic migrations auto-run at container start; CAGG created manually (outside txn) |
| Cost control | Compression ≥7d, retention at 180d (tunable) |
| Observability | CAGG job + chunk stats inspectable via Timescale views |
| Evolvability | Narrow, focused Alembic revisions; CAGG created manually (outside txn) |

---

## 3. Core Schema (Logical)

Table | Purpose | Notes
------|---------|------
`sensors` | Asset registry | Business key = `sensor_id`
`sensor_readings` (hypertable) | Raw time-series metrics | PK: (`timestamp`, `sensor_id`) + surrogate `id` (sequence)
`anomaly_alerts` | Persisted anomaly events | Enriched by ML agents
`maintenance_logs` | Action & intervention history | Downstream analytics
(Plus) auxiliary alembic metadata tables.

Key Columns (sensor_readings):
- `timestamp TIMESTAMPTZ NOT NULL`
- `sensor_id VARCHAR(255) NOT NULL`
- `value DOUBLE PRECISION NOT NULL`
- `unit VARCHAR(50)`
- `quality DOUBLE PRECISION`
- `id INT DEFAULT nextval('sensor_readings_id_seq')` (surrogate for ORM convenience)

---

## 4. Time-Series Strategy

Feature | Rationale
--------|----------
Hypertable partitioning | Automatic chunking for time pruning & parallelism
Descending composite index | Fast “latest N” retrieval (ML sliding windows)
Additional timestamp index | Pure time-range scans & retention enforcement
CAGG Hourly summary | Pre-aggregates reduce repeated raw scans
Policies (compression + retention) | Keep working set hot; archive older compressed
Manual CAGG creation | Timescale restriction: cannot create inside Alembic transaction

---

## 5. Migration & Evolution Timeline (Changelog Trace)

| Day | Change | Outcome |
|-----|--------|---------|
| 5 | Primary key redesign attempt (compression constraints) | Avoided DROP on compressed hypertable; kept surrogate `id` |
| 12 | Composite index addition | Enabled drift & prediction window acceleration |
| 15 | Sequence recreation (`sensor_readings_id_seq`) | Fixed `NOT NULL` insert failures |
| 18 | Performance-focused index + CAGG migration created (index only) | CAGG applied manually (non-transactional) |
| 18 (Verification) | Idempotent upgrade/downgrade & refresh validation | Ensured safe replays |
| 22 | Documentation & rationale formalized | Production hand-off readiness |

---

## 6. Indexing Strategy & Rationale

Index | Purpose | Workloads Accelerated
------|---------|-----------------------
`(sensor_id, timestamp DESC)` | Locate most recent observations quickly | Drift tests, sliding ML feature windows, real-time dashboards
`(timestamp)` | Pure chronological scans | Bulk exports, retention housekeeping, backfill jobs
Primary Key (`timestamp`, `sensor_id`) | Natural uniqueness & time pruning | CAGG backfill, duplicate prevention (logical layer)

Descending order on composite index aligns with “give me last 1k points” eliminating extra sort.

---

## 7. Continuous Aggregate (CAGG)

Name: `sensor_readings_summary_hourly`  
Definition (conceptual):
```sql
SELECT
  sensor_id,
  time_bucket('1 hour', timestamp) AS hour,
  avg(value) AS avg_value,
  max(value) AS max_value,
  min(value) AS min_value,
  count(*) AS reading_count
FROM sensor_readings
GROUP BY sensor_id, hour;
```

Refresh Policy:
- Schedule: every 30 minutes
- Window: start_offset = 2h (captures late arrivals), end_offset = 30m (stability)
- Reasoning: Balances freshness vs avoiding constant recompute on “still-hot” hour

Transaction Limitation:
- Created manually via psql (cannot occur within Alembic transactional block)
- Migration includes documentation stub referencing manual step

---

## 8. Performance Benchmarks (Day 18)

Metric | Baseline (Raw) | Optimized (CAGG / Index) | Gain
-------|----------------|--------------------------|-----
Hourly aggregate fetch | ~2.4s (full scan) | ~1.5s | 37.3% faster
Aggregation rows scanned (24h) | 1,439 | 240 | 83.3% fewer rows
Single-sensor recent window lookup | Sort + filter | Index-only | Sub-ms stable
Planning time (representative query) | 8.76ms | 3.51ms | 59.9% faster

Impact:
- Lower DB CPU under concurrent forecasting & drift
- Predictable latency supports SLO (<5s drift check; achieved ~3ms endpoint time given DB offload)

---

## 9. Data Lifecycle Policies

Policy | Setting | Rationale
-------|---------|----------
Compression | Age ≥ 7 days | Keeps recent hot window uncompressed for frequent ML queries
Retention | 180 days | Balance forensic horizon & storage cost; configurable via future migration
Backfill | Natural via hypertable | CAGG recalculates historical windows on demand if needed

Compression reduces storage (target 90% typical sensor series) while keeping decompress cost acceptable for infrequent historical pulls.

---

## 10. Query Archetypes & Optimization Mapping

Archetype | Example | Optimization Lever
----------|---------|-------------------
Latest N window | Last 1,000 rows for sensor | Composite DESC index
Drift comparison | Reference vs current window (two ranges) | Composite index + narrowed range scans
Hourly dashboard | 24h summary per sensor | CAGG (pre-aggregation)
Long-range export | All rows > date | Timestamp index pruning
Anomaly root cause | Outlier band + time filter | Index assists predicate + LIMIT ordering

---

## 11. ML & Analytics Integration

Use Case | DB Dependency
---------|--------------
Feature Engineering | Rapid latest-window extraction (descending index)
Drift Detection (KS / PSI) | Two time buckets; index ensures bounded scan
Model Retraining Windows | Consistent slice retrieval ensures reproducibility
Intelligent Model Selection (metadata tagging) | DB not primary; ensures fast sensor stats for UI context
Forecasting | Hourly aggregates as engineered covariates (avoids repeated raw scans)

---

## 12. Operational Runbook

Note: Alembic migrations run automatically at container startup; use the following commands for manual control, local debugging, or recovery procedures.

Action | Command / Procedure
------|---------------------
Apply migrations | `docker compose exec api alembic upgrade heads`
Verify heads | `docker compose exec api alembic heads`
List current revision | `docker compose exec api alembic current`
Create new index migration | Inside container: `alembic revision -m "add_x"` then edit
Backfill CAGG manually | `CALL refresh_continuous_aggregate('sensor_readings_summary_hourly', NULL, NULL);`
Check refresh jobs | `SELECT * FROM timescaledb_information.jobs;`
Inspect chunk compression | `SELECT * FROM timescaledb_information.hypertable_compression_stats;`
Force export | `python scripts/export_sensor_data_csv.py [--incremental]`
Sequence integrity check | `SELECT last_value FROM sensor_readings_id_seq;`

---

## 13. Troubleshooting Matrix

Symptom | Likely Cause | Resolution
--------|--------------|-----------
CAGG not updating | Refresh policy not present / job disabled | Re-run `add_continuous_aggregate_policy`
Slow drift endpoint | Missing composite index or huge window | Confirm index; reduce window_minutes
Insert fails on `id` null | Sequence default missing (legacy migration) | Recreate sequence & set default (Day 15 fix)
Multiple alembic heads | Parallel branch merges | Manual merge revision or upgrade both heads
Permission denied during manual psql | Container user mismatch | Execute via `docker compose exec db psql …`
Large query memory | Unbounded raw scan | Utilize CAGG or add predicate narrowing

---

## 14. Observability Focus

Metric / View | Purpose
--------------|--------
`timescaledb_information.jobs` | CAGG refresh job health
Query latency (app metrics) | Detect regression post new index/migration
Chunk count / size | Capacity planning
Compression ratio | Storage efficiency tracking
Dead tuples (VACUUM stats) | Assess bloat (less critical on append-only)
Blocked sessions | Lock contention detection (should be minimal)

---

## 15. Resilience & Safety Considerations

Aspect | Mitigation
-------|-----------
Migration Blast Radius | No auto-run; explicit manual invocation
Sequence Drift | Documented recovery script (Day 15)
CAGG Creation Failure | Manual interactive step w/ documented reason
Duplicate Ingestion | Application idempotency (Redis) not DB-enforced (keeps DB lean)
Late Arrivals | Refresh offsets (2h start) incorporate stragglers
Rollback Safety | Downgrade scripts drop only objects they created (idempotent)

---

## 16. Security Posture

Control | Note
--------|-----
Least Privilege | (Recommended) separate RW vs RO roles (future enhancement)
Secrets | Connection via env (`DATABASE_URL`) only
No Dynamic SQL | All queries parameterized (ORM / psycopg)
Data Privacy | Sensor telemetry non-PII; expansion may require masking strategies
Auditability | Structured app logs w/ correlation_id + request context

---

## 17. Future Enhancements (Roadmap Alignment)

Planned | Rationale
--------|----------
Daily & weekly CAGGs | Long-horizon forecasts & seasonal analytics
Adaptive refresh scheduling | Reduce redundant refresh when low write volume
Partial indexes (quality threshold) | Specialized analytics acceleration
Tiered retention (cold archive) | Move >180d data to cheaper storage
Materialized feature snapshots | Consistent feature sets for retrain reproducibility
Row-level security (if multi-tenant) | Segregate tenant sensor data

---

## 18. Changelog Traceability Mapping

Feature / Decision | Day(s)
-------------------|-------
Hypertable + compression baseline | 5
Composite index addition & predict stabilization | 12
Entrypoint migration automation + CAGG manual step | 12+
Sequence recreation & idempotent ingestion synergy | 15
Chaos & resilience validation (Redis outages) | 15
Performance CAGG & benchmark | 18
Verification & CI hardening (Poetry, idempotency) | 18 (verification)
Documentation formalization (DB + ML) | 22
Drift automation & hourly stats usage | 23

---

## 19. Summary

Optimized TimescaleDB layer couples a descending composite index + hourly continuous aggregate + compression/retention to achieve sub‑millisecond sliding queries and 37.3% faster aggregation workloads, while maintaining operational safety through deliberate migration control and transparent performance instrumentation.

---

## 20. Reference Commands (Copy/Paste)

```bash
# Show CAGG definition
docker compose exec db psql -U smart_user -d smart_maintenance_db -c "\d+ sensor_readings_summary_hourly"

# Manual CAGG refresh (all)
docker compose exec db psql -U smart_user -d smart_maintenance_db -c \
"CALL refresh_continuous_aggregate('sensor_readings_summary_hourly', NULL, NULL);"

# Inspect jobs
docker compose exec db psql -U smart_user -d smart_maintenance_db -c \
"SELECT job_id, application_name, hypertable_name, last_run_started_at, next_start FROM timescaledb_information.jobs ORDER BY job_id;"
```

---

_All statements sourced from 30-day sprint changelog (authoritative history)._
- **Automated Rebalancing**: Dynamic chunk management based on query patterns
- **Advanced Analytics**: Built-in statistical functions and machine learning extensions

---

**Schema Evolution**: This architecture supports continuous evolution through Alembic migrations while maintaining TimescaleDB performance optimizations and ensuring zero-downtime deployments for production industrial IoT workloads.
