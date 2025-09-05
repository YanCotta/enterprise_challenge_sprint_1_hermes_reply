# Smart Maintenance SaaS - Complete Documentation Index

## Core Documentation

### Getting Started

- **[Main README](../README.md)** - Project overview, quick start, and repository structure
- **[Backend README](./README.md)** - Docker deployment and getting started guide
- **[Development Orientation](../DEVELOPMENT_ORIENTATION.md)** - Development guidelines and best practices

### Project History & Changelog

- **[30-Day Sprint Changelog](../30-day-sprint-changelog.md)** - Complete development history and daily progress
- **[Final Sprint Summary](../final_30_day_sprint.md)** - Executive summary of sprint achievements

## System Architecture & Design

### Architecture Documentation

- **[System and Architecture](./docs/SYSTEM_AND_ARCHITECTURE.md)** - Comprehensive system architecture and design patterns
- **[System Screenshots](./docs/SYSTEM_SCREENSHOTS.md)** - Visual documentation of system interfaces
- **[Comprehensive System Analysis](./docs/COMPREHENSIVE_SYSTEM_ANALYSIS_REPORT.md)** - Detailed technical analysis report
- **[Microservice Migration Strategy](./docs/MICROSERVICE_MIGRATION_STRATEGY.md)** - Future architecture evolution plans

### Database Design

- **[Database Documentation](./docs/db/README.md)** - Database schema and design documentation
- **[Database ERD](./docs/db/erd.dbml)** - Entity Relationship Diagram source
- **[Database ERD (PNG)](./docs/db/erd.png)** - Entity Relationship Diagram visualization
- **[Database ERD (Dark Mode)](./docs/db/erd_darkmode.png)** - Entity Relationship Diagram (dark theme)
- **[Database Schema](./docs/db/schema.sql)** - Complete SQL schema definition

## API & Integration

### API Documentation

- **[API Reference](./docs/api.md)** - Complete REST API documentation and examples
- **[Configuration Management](./core/config/README.md)** - Centralized configuration system
- **[Logging Configuration](./core/logging_config.md)** - Structured JSON logging setup

## Performance & Testing

### Performance Documentation

- **[Performance Baseline](./docs/PERFORMANCE_BASELINE.md)** - Performance metrics and SLO targets
- **[Day 17 Load Test Report](./docs/DAY_17_LOAD_TEST_REPORT.md)** - Comprehensive load testing results (103.8 RPS)
- **[Day 18 Performance Results](./docs/DAY_18_PERFORMANCE_RESULTS.md)** - TimescaleDB optimization results
- **[Load Testing Instructions](./docs/LOAD_TESTING_INSTRUCTIONS.md)** - Guide for running performance tests

### Testing Documentation

- **[Test Documentation](./tests/README.md)** - Test organization and execution guide
- **[Coverage Improvement Plan](./docs/COVERAGE_IMPROVEMENT_PLAN.md)** - Test coverage strategy and current status

## Machine Learning & Data Science

### ML Documentation

- **[ML Documentation](./docs/ml/README.md)** - Machine learning models and pipelines
- **[Models Summary](./docs/MODELS_SUMMARY.md)** - Overview of all 17+ production models
- **[Project Gauntlet Plan](./docs/PROJECT_GAUNTLET_PLAN.md)** - Real-world dataset integration execution

## Security & Operations

### Security Documentation

- **[Security Documentation](./docs/SECURITY.md)** - Security architecture and implementation
- **[Security Audit Checklist](./docs/SECURITY_AUDIT_CHECKLIST.md)** - Comprehensive security audit framework

### Service Documentation

- **[Anomaly Service](./services/anomaly_service/README.md)** - Future anomaly detection microservice
- **[Prediction Service](./services/prediction_service/README.md)** - Future ML prediction microservice

---

*This index is automatically maintained and appears at the top of all documentation files for easy navigation.*

---

# Smart Maintenance SaaS – Backend

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Production-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-410%2F411%20Passing-brightgreen.svg)](#test-status)
[![Performance](https://img.shields.io/badge/Peak%20RPS-103.8-blueviolet)](.)
[![Latency](https://img.shields.io/badge/P95-2ms-purple)](.)
[![Models](https://img.shields.io/badge/MLflow-15%2B%20Models-blue)](.)

Production‑grade, event‑driven backend powering industrial predictive & prescriptive maintenance: resilient ingestion, TimescaleDB time‑series optimization, multi‑modal ML (tabular, vibration, audio, forecasting), automated drift detection & retraining, intelligent model selection, security hardening, and microservice‑ready architecture.

---

## 1. Quick Start (Backend Stack)

### Environment and Reproducibility

This project uses Docker to ensure a consistent environment and DVC to manage large data files and models. To replicate the environment and access all artifacts, follow the steps below:

1. **Clone the Repository:**
   ```bash
   git clone <REPOSITORY_URL>
   cd enterprise_challenge_sprint_1_hermes_reply
   ```

2. **Install Dependencies:**
   ```bash
   pip install dvc dvc-gdrive
   ```

3. **Synchronize Data and Models:**
   ```bash
   dvc pull
   ```
   *This command will download all versioned datasets and ML models. It may take a few minutes.*

4. **Start the Environment:**
   ```bash
   docker compose up --build
   ```

After these steps, all services, including the API, the UI, and MLflow with the pre-trained models, will be available.

### Quick Start Commands

```bash
git clone <repo>
cd enterprise_challenge_sprint_1_hermes_reply
docker compose up -d --build
# API:        http://localhost:8000/docs
# UI:         http://localhost:8501
# MLflow:     http://localhost:5000
# Metrics:    http://localhost:8000/metrics
```

Stop (preserve volumes):
```bash
docker compose down
```

Run migrations manually (intentional design – see Migration Strategy):
```bash
docker compose exec api alembic upgrade heads
```

---

## 2. Repository Structure (Backend Focus)

```
smart-maintenance-saas/
  apps/
    api/                 # FastAPI routers, ML endpoints, drift endpoint
    agents/              # Event-driven multi-agent (anomaly, scheduling, etc.)
  core/
    config/              # Pydantic settings
    events/              # Event bus + base event types (retry, DLQ-ready)
    logging_config.py    # JSON structured logging + correlation IDs
    redis_client.py      # Redis (idempotency + pub/sub)
  scripts/
    seed_data.py
    export_sensor_data_csv.py
    run_drift_check_agent.py
    retrain_models_on_drift.py
  tests/                 # 410/411 passing (1 scheduling edge case)
  alembic_migrations/    # Schema + performance index revisions
  docker/ & infrastructure/k8s/ (scaffolding)
```

---

## 3. Core Capabilities (Synchronized to Changelog)

| Capability | Status | Implementation Highlights |
|------------|--------|---------------------------|
| Ingestion Idempotency | ✅ | Redis SET NX EX (10m TTL), fallback to non-idempotent w/ warning |
| Correlation / Request IDs | ✅ | Middleware adds/propagates X-Request-ID |
| Structured Logging | ✅ | JSON logs + correlation_id ContextVar |
| Event Bus Resilience | ✅ | Tenacity retries (exp backoff: 2s/4s/6s) + DLQ hook |
| Time-Series Storage | ✅ | TimescaleDB hypertable + compression + retention |
| Performance Indexing | ✅ | (sensor_id, timestamp DESC) + timestamp index |
| Continuous Aggregate (CAGG) | ✅ | Hourly summary (avg/max/min/count) + 30m refresh policy |
| Data Export | ✅ | Full + incremental CSV export script |
| Drift Detection Endpoint | ✅ | /api/v1/ml/check_drift (KS test; PSI via agents) |
| Automated Drift Agent | ✅ | APScheduler + Redis events + Slack/webhook ready |
| Automated Retrain Agent | ✅ | Event-driven, cooldown & concurrency guard |
| ML Registry Persistence | ✅ | MLflow (SQLite backend + shared /mlruns volume) |
| Model Loader | ✅ | Cached, run URI fallback, structured exception logging |
| Intelligent Model Selection | ✅ | MLflow tags (domain=bearing|audio|tabular|forecast|pump) |
| Model Hash Validation (CI) | ✅ | Prevent silent artifact drift |
| Rate Limiting | ✅ | slowapi (example: drift endpoint 10/min per API key) |
| Security Audit & STRIDE | ✅ | SECURITY.md + SECURITY_AUDIT_CHECKLIST.md |
| Vulnerability Scanning | ✅ | Snyk job + fail on high/critical |
| Resilience / Chaos | ✅ | Toxiproxy (latency, timeout, partition) |
| Microservice Scaffolding | ✅ (Dormant) | prediction_service / anomaly_service |
| Performance Tuning | ✅ | 37.3% aggregation speed gain (CAGG) |
| Load Test Baseline | ✅ | 103.8 peak RPS, P95=2ms, P99=3ms |
| CI/CD Hardening | ✅ | Jobs: lint, tests, coverage≥80%, hash validate, ML validations |

---

## 4. Architecture Overview

### 4.1 Event-Driven Flow
Sensor ingestion → Validation → Anomaly detection → (Optional scheduling / prediction pipeline) → Drift monitoring events → Automated retrain → Registry update → Selection UI surfacing best model.

### 4.2 Why Event-Driven?
- Decouples anomaly detection, prediction, validation, scheduling.
- Enables safe future activation of microservices (strangler pattern).
- Retry + DLQ semantics allow localized failure recovery.

### 4.3 Database Strategy (TimescaleDB)
| Feature | Rationale |
|---------|-----------|
| Hypertable | Native partitioning for high-ingest time-series |
| Composite Index (sensor_id, timestamp DESC) | Accelerates sliding windows + recent drift spans |
| Timestamp Index | Pure time-range scans (bulk export / analytics) |
| Continuous Aggregate (hourly) | Pre-compute statistics → 37.3% faster ML feature queries & dashboards |
| Refresh Policy (start_offset 2h, end_offset 30m, 30m schedule) | Ensures late-arriving data stability & predictable refresh cadence |
| Compression (≥7d) + Retention (180d) | Linear cost control + historical analytic viability |

CAGG creation is executed outside Alembic (Timescale restriction: cannot create inside a transaction). Migration documents non-transactional manual step.

---

## 5. Data & Export

Full export:
```bash
docker compose exec api python scripts/export_sensor_data_csv.py
```

Incremental (appends new rows):
```bash
docker compose exec api python scripts/export_sensor_data_csv.py --incremental
```

Custom path:
```bash
docker compose exec api python scripts/export_sensor_data_csv.py --output /tmp/readings.csv
```

---

## 6. ML Platform (Project Gauntlet Consolidation)

| Phase | Domain | Outcome |
|-------|--------|---------|
| 0 | Synthetic Validation | Pipeline + infra verified |
| 1 | AI4I Classification | 99.90% accuracy ceiling identified |
| 2 | NASA Vibration | IsolationForest + OneClassSVM (10% anomaly separation) |
| 3 | MIMII Audio | MFCC + RandomForest (93.3% acc, fallback pipeline) |
| 4 | Pump Classification | 100% accuracy (perfect separation) |
| 5 | XJTU Vibration | Dual-channel advanced bearing anomaly features (22) |
| 6 | Drift & Lifecycle | Drift endpoint + agents + retraining automation |
| 7 | Intelligent Selection | Tag-based filtered model recommendations in UI |

Model Families: anomaly (IF, OCSVM), forecasting (Prophet tuned + challengers), classification (RandomForest, SVC, LightGBM), audio (MFCC + RF), vibration (statistical + frequency features), retrainable pipelines.

Intelligent Selection UI uses MLflow tags:
```
domain=audio|bearing|forecast|tabular|pump
```
Exposes recommended subset for chosen sensor type; manual override supported.

Feature Contract: Each registered model persists `feature_names.txt`; CI hash validator enforces integrity.

---

## 7. Drift & Automated Retraining

| Component | Function |
|-----------|----------|
| /api/v1/ml/check_drift | On-demand KS test (reference vs current window) |
| Drift Agent (scheduler) | Periodic KS + PSI (Evidently-style) → emits Redis event |
| Retrain Agent | Consumes events, enforces cooldown, triggers notebook/Make targets |
| Notifications | Slack/Webhook (configurable placeholders) |
| Safety | Concurrency guard & per-model cooldown (24h default) |
| Output | New MLflow model version + updated feature manifest |

Benefit: Zero-touch lifecycle; prevents silent performance decay.

---

## 8. Resilience & Chaos Engineering

| Mechanism | Detail |
|-----------|--------|
| Idempotent Ingestion | Redis SET NX — duplicate rejected returns original event_id |
| Graceful Degradation | Missing Redis → logs warning, continues (no idempotency) |
| Event Retry | Exponential backoff (2,4,6s) then DLQ hook |
| Toxiproxy | Latency / timeout / partition tests for DB & Redis |
| Manual Migration Strategy | Auto-migrate removed (prevents restart storms) |
| Recovery Lessons | Day 12 & Day 15 documented: sequence recreation & multi-head resolution |
| SLO Baseline | P95 API < 200ms (actual 2ms); Drift endpoint P95 <5s (actual ~3ms) |

---

## 9. Security & Compliance

| Area | Implementation |
|------|----------------|
| Auth | API Key header (`X-API-Key`) |
| Rate Limiting | slowapi (per key; drift endpoint 10/min) |
| Threat Model | STRIDE documented (Spoofing→Tampering→…) |
| Audit Checklist | SECURITY_AUDIT_CHECKLIST.md |
| Dependency Scans | Snyk CI (fail on high/critical) |
| Code Scans | Snyk code + bandit/safety (pipeline) |
| Logging Hygiene | No secrets; correlation IDs |
| Future Roadmap | Scope-based keys & signed model manifests |

---

## 10. Performance (Validated)

| Metric | Result | Source |
|--------|--------|--------|
| Peak Throughput | 103.8 RPS | Day 17 load test (50 users / 3m) |
| Avg Throughput | 88.8 RPS sustained | Day 17 |
| API Latency P95 | 2 ms | Day 17 |
| API Latency P99 | 3 ms | Day 17 |
| Max Observed | 124 ms | Day 17 |
| Aggregation Speed Gain | 37.3% faster | Day 18 (CAGG + indexes) |
| Rows Scanned Reduction | 83.3% fewer | CAGG hourly pre-compute |
| Forecast MAE Improvement | 20.86% vs naive | Prophet tuned |
| Pump Classification | 100% accuracy | Phase 4 |
| Vibration Anomaly Rate | 10% (clean separation) | NASA/XJTU |

---

## 11. CI/CD Workflow

| Job | Purpose |
|-----|---------|
| Lint & Type | Enforces code quality |
| Tests | 410/411 passing (1 scheduling E2E edge) |
| Coverage | Enforce ≥80% |
| Security Scan | Snyk + safety/bandit |
| Model Hash Validation | Detect unexpected artifact drift |
| ML Train Validation | Reproducibility check (anomaly / forecast matrices) |
| (Optional) Load Test | Registry & API read stress |

Poetry install hardened (pip install fallback + retries) after transient SSL issues (Day 18 verification + Day 19 refinement).

---

## 12. Microservice Migration (Dormant Scaffolding)

Services prepared (commented in compose & k8s):
- prediction_service (inference offload)
- anomaly_service (statistical & streaming analysis)

Activation Triggers (docs/MICROSERVICE_MIGRATION_STRATEGY.md):
- P95 latency > 50ms sustained
- Throughput > 200 RPS
- Infra saturation >80% CPU/memory
- Deployment coupling friction

Migration Path: Strangler — shift inference & anomaly endpoints first; preserve shared event bus & registry.

---

## 13. Known Constraints / Lessons

| Topic | Lesson |
|-------|--------|
| Continuous Aggregates | Must create outside Alembic transaction |
| Automatic Migrations | Removed (restart storm risk) |
| Multi-Head Alembic | Resolve intentionally; document no-op fixes |
| MLflow Persistence | Run URIs fallback + consistent /mlruns mount essential |
| Permissions | Use consistent UID:GID & tempfile artifact pattern to avoid cross-container denial |
| Feature Mismatch | Always validate against stored `feature_names.txt` |

---

## 14. API (Selected Endpoints)

| Endpoint | Method | Summary | Notes |
|----------|--------|---------|-------|
| /api/v1/data/ingest | POST | Ingest sensor reading | Idempotency-Key supported |
| /api/v1/ml/check_drift | POST | KS-based drift evaluation | Rate-limited |
| /api/v1/reports/generate | POST | System / anomaly / maintenance reports | Async executor offload |
| /api/v1/decisions/submit | POST | Human feedback / approval | Supports orchestration loop |
| /health | GET | Basic health | Add DB/Redis checks upcoming |
| /metrics | GET | Prometheus metrics | Instrumentator integration |

All protected endpoints require `X-API-Key`.

---

## 15. Testing Status

| Layer | Coverage |
|-------|----------|
| Unit | Model utils, feature transformers |
| Integration | DB, Redis, drift logic, export |
| E2E | Full anomaly→prediction (1 scheduling window edge failing) |
| Load | API + Registry (Locust) |
| Resilience | Toxiproxy latency/timeouts |
| Security | Rate limit & auth rejection |
| ML Integrity | Hash + artifact presence |

Failing Test Context: Maintenance scheduling slot timing (business hour constraint late in day). Low severity; workflow validated manually.

---

## 16. Operational Runbook (Essentials)

| Action | Command |
|--------|---------|
| Migrate DB | `docker compose exec api alembic upgrade heads` |
| Rebuild ML image | `make build-ml` |
| Train anomaly | `make train-anomaly` |
| Train forecast | `make train-forecast` |
| Pump classification | `make pump-gauntlet` |
| Run drift agent (already in compose) | `docker compose logs -f drift_agent` |
| Manual drift check | POST /api/v1/ml/check_drift |
| Export data (incremental) | See Data Export section |
| Validate model hashes | `python scripts/validate_model_hashes.py` |

---

## 17. Migration Strategy (Schema)

Principles:
- No automatic migrations at container start (avoid cascading crashes).
- Each performance-focused migration isolates only required changes (e.g., adding composite index).
- Continuous aggregate creation documented & executed manually (non-transactional constraint).
- Sequence restoration (Day 15) codified for future schema evolution sanity.

---

## 18. Troubleshooting Guide

| Symptom | Likely Cause | Action |
|---------|--------------|-------|
| Model 404 in predict | Artifact path / registry mismatch | Use run URI; verify /mlruns mount |
| Feature count mismatch | Serving payload stale | Fetch `feature_names.txt` from model artifacts |
| Drift endpoint slow | Large window or unindexed query | Ensure composite index present; window size tune |
| High 403 rate in load test | Missing API key | Add header X-API-Key |
| Duplicate ingestion accepted | Redis unavailable | Check logs for “idempotency disabled” warning |
| CAGG missing rows | Refresh lag | Verify refresh policy; run manual `refresh_continuous_aggregate` |

---

## 19. Performance Rationale Summary

| Optimization | Why | Result |
|--------------|-----|--------|
| Composite Index (sensor_id, timestamp DESC) | Sliding window + per-sensor drift/forecast queries | Microsecond-range lookups |
| Hourly CAGG | Pre-aggregation for ML features & dashboards | 37.3% faster aggregation; 83% fewer rows scanned |
| Retry Event Publish | Absorb transient handler failures | Prevents lost anomalies |
| Cached Model Loader | Avoid repeated MLflow artifact fetch | Sub-ms warm inference |
| Manual Migrations | Stability & blast radius control | Eliminated restart storms |

---

## 20. Future Enhancements (Tracked)

- Scope-based API keys & key rotation
- Signed model manifests + provenance
- Multi-replica Redis for distributed idempotency
- Expanded drift algorithms (population stability index already in agents; add Jensen-Shannon)
- Daily CAGG + long-horizon retention tiering
- Canary retrain validation pre-promotion

(See FUTURE_ROADMAP / migration strategy doc.)

---

## 21. References

| Document | Purpose |
|----------|---------|
| ../README.md | High-level platform overview |
| docs/SYSTEM_AND_ARCHITECTURE.md | Deep architecture narrative |
| docs/db/README.md | TimescaleDB optimization & schema |
| docs/ml/README.md | ML lifecycle, drift, retrain |
| docs/MICROSERVICE_MIGRATION_STRATEGY.md | Activation triggers |
| docs/PERFORMANCE_BASELINE.md | Load & latency SLOs |
| docs/SECURITY.md | Threat model (STRIDE) |
| docs/SECURITY_AUDIT_CHECKLIST.md | Audit workflow |
| 30-day-sprint-changelog.md | Source of truth history |

---

## 22. Changelog Authority

All statements trace to 30-day-sprint-changelog.md (Days 4–23: ingestion hardening, observability, ML phases, drift automation, performance, security, scaffolding).

---

## 23. License

Proprietary – see LICENSE.

---

## 24. Support Diagnostic Order

1. /health + logs (correlation_id presence?)  
2. Redis availability (idempotency + events)  
3. Timescale indexes & CAGG refresh state  
4. MLflow registry (model list & artifact accessible)  
5. Drift & retrain agent logs (event flow)  
6. Hash validation (integrity)  

---

<sub>Document synchronized with sprint changelog through Day 23 (drift automation & ML documentation). </sub>
