# Smart Maintenance SaaS - Complete Documentation Index

## Core Documentation

### Getting Started

- **[Main README](./README.md)** - Project overview, quick start, and repository structure
- **[Backend README](./smart-maintenance-saas/README.md)** - Docker deployment and getting started guide
- **[Development Orientation](./DEVELOPMENT_ORIENTATION.md)** - Development guidelines and best practices

### Project History & Changelog

- **[30-Day Sprint Changelog](./30-day-sprint-changelog.md)** - Complete development history and daily progress
- **[Final Sprint Summary](./final_30_day_sprint.md)** - Executive summary of sprint achievements

## System Architecture & Design

### Architecture Documentation

- **[System and Architecture](./smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md)** - Comprehensive system architecture and design patterns
- **[System Screenshots](./smart-maintenance-saas/docs/SYSTEM_SCREENSHOTS.md)** - Visual documentation of system interfaces
- **[Comprehensive System Analysis](./smart-maintenance-saas/docs/COMPREHENSIVE_SYSTEM_ANALYSIS_REPORT.md)** - Detailed technical analysis report
- **[Microservice Migration Strategy](./smart-maintenance-saas/docs/MICROSERVICE_MIGRATION_STRATEGY.md)** - Future architecture evolution plans

### Database Design

- **[Database Documentation](./smart-maintenance-saas/docs/db/README.md)** - Database schema and design documentation
- **[Database ERD](./smart-maintenance-saas/docs/db/erd.dbml)** - Entity Relationship Diagram source
- **[Database ERD (PNG)](./smart-maintenance-saas/docs/db/erd.png)** - Entity Relationship Diagram visualization
- **[Database ERD (Dark Mode)](./smart-maintenance-saas/docs/db/erd_darkmode.png)** - Entity Relationship Diagram (dark theme)
- **[Database Schema](./smart-maintenance-saas/docs/db/schema.sql)** - Complete SQL schema definition

## API & Integration

### API Documentation

- **[API Reference](./smart-maintenance-saas/docs/api.md)** - Complete REST API documentation and examples
- **[Configuration Management](./smart-maintenance-saas/core/config/README.md)** - Centralized configuration system
- **[Logging Configuration](./smart-maintenance-saas/core/logging_config.md)** - Structured JSON logging setup

## Performance & Testing

### Performance Documentation

- **[Performance Baseline](./smart-maintenance-saas/docs/PERFORMANCE_BASELINE.md)** - Performance metrics and SLO targets
- **[Day 17 Load Test Report](./smart-maintenance-saas/docs/DAY_17_LOAD_TEST_REPORT.md)** - Comprehensive load testing results (103.8 RPS)
- **[Day 18 Performance Results](./smart-maintenance-saas/docs/DAY_18_PERFORMANCE_RESULTS.md)** - TimescaleDB optimization results
- **[Load Testing Instructions](./smart-maintenance-saas/docs/LOAD_TESTING_INSTRUCTIONS.md)** - Guide for running performance tests

### Testing Documentation

- **[Test Documentation](./smart-maintenance-saas/tests/README.md)** - Test organization and execution guide
- **[Coverage Improvement Plan](./smart-maintenance-saas/docs/COVERAGE_IMPROVEMENT_PLAN.md)** - Test coverage strategy and current status

## Machine Learning & Data Science

### ML Documentation

- **[ML Documentation](./smart-maintenance-saas/docs/ml/README.md)** - Machine learning models and pipelines
- **[Models Summary](./smart-maintenance-saas/docs/MODELS_SUMMARY.md)** - Overview of all 17+ production models
- **[Project Gauntlet Plan](./smart-maintenance-saas/docs/PROJECT_GAUNTLET_PLAN.md)** - Real-world dataset integration execution

## Security & Operations

### Security Documentation

- **[Security Documentation](./smart-maintenance-saas/docs/SECURITY.md)** - Security architecture and implementation
- **[Security Audit Checklist](./smart-maintenance-saas/docs/SECURITY_AUDIT_CHECKLIST.md)** - Comprehensive security audit framework

### Service Documentation

- **[Anomaly Service](./smart-maintenance-saas/services/anomaly_service/README.md)** - Future anomaly detection microservice
- **[Prediction Service](./smart-maintenance-saas/services/prediction_service/README.md)** - Future ML prediction microservice

---

*This index is automatically maintained and appears at the top of all documentation files for easy navigation.*

---

# Smart Maintenance SaaS

[![Proprietary License](https://img.shields.io/badge/License-Proprietary-red.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](.)
[![Models](https://img.shields.io/badge/MLflow-15%2B%20Models-blue)](.)
[![Performance](https://img.shields.io/badge/P95%20Latency-2ms%20(@50u)-purple)](.)

A production‑ready Predictive & Prescriptive Industrial Maintenance platform combining IoT ingestion, TimescaleDB time-series optimization, multi‑modal ML (tabular, vibration, audio, forecasting), automated drift detection & retraining, and resilient event-driven architecture.

---

## 🚀 Quick Start (5 Minutes)

Prerequisites: Docker & Docker Compose installed.

```bash
git clone <repo>
cd enterprise_challenge_sprint_1_hermes_reply
docker compose up -d --build
# Core services:
# API:        http://localhost:8000/docs
# UI:         http://localhost:8501
# MLflow:     http://localhost:5000
# Metrics:    http://localhost:8000/metrics
```

Stop & clean (non-destructive):
```bash
docker compose down
```

---

## 📁 Documentation Index

| Area | Reference |
|------|-----------|
| Backend & Architecture | smart-maintenance-saas/README.md |
| System Architecture | smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md |
| API Reference | smart-maintenance-saas/docs/api.md |
| Tests Guide | smart-maintenance-saas/tests/README.md |
| Performance & Load | smart-maintenance-saas/docs/PERFORMANCE_BASELINE.md |
| Security Model | docs/SECURITY.md & docs/SECURITY_AUDIT_CHECKLIST.md |
| DB Architecture | docs/db/README.md |
| ML Platform | docs/ml/README.md |
| Migration Strategy (Microservices) | docs/MICROSERVICE_MIGRATION_STRATEGY.md |
| Changelog (Source of Truth) | 30-day-sprint-changelog.md |

---

## 🧩 Platform Overview

| Capability | Status | Notes |
|------------|--------|-------|
| Ingestion & Idempotency | ✅ | Redis-backed SET NX EX (10m TTL) |
| Time-Series Storage | ✅ | TimescaleDB hypertable + compression + retention |
| Query Optimization | ✅ | Composite index (sensor_id, timestamp DESC) + hourly continuous aggregate |
| Observability | ✅ | Prometheus (/metrics), structured JSON logs, correlation IDs |
| ML Model Registry | ✅ | MLflow persistent (SQLite + volume) |
| Model Catalog | ✅ | 15+ models (anomaly, forecasting, classification, audio, vibration) |
| Drift Detection | ✅ | Scheduled KS + PSI + event emission |
| Automated Retraining | ✅ | Event-driven (Redis pub/sub) retrain agent with cooldown policies |
| Security Hardening | ✅ | API key auth, rate limiting, Snyk scan, STRIDE audit |
| Chaos & Resilience | ✅ | Toxiproxy latency/timeout tests; retrying event bus; graceful degradation |
| Microservice Scaffolding | ✅ (Dormant) | prediction_service & anomaly_service (future activation triggers) |

---

## 🗄️ Data & Database Architecture

**Core Store:** TimescaleDB  
**Table:** sensor_readings (hypertable)  
**Primary Key:** (timestamp, sensor_id)  
**Indexes:**  
- `(sensor_id, timestamp DESC)` → accelerates ML sliding windows & drift queries  
- `(timestamp)` → time-range scans  
**Continuous Aggregate:** `sensor_readings_summary_hourly` (avg, max, min, count)  
- Refresh policy: every 30m, window start offset 2h, end offset 30m  
- Achieved **37.3% query speed improvement** on aggregation workloads (validated Day 18)  
**Policies:** compression ≥ 7 days, retention 180 days (tunable)  

Benefits:
- Pre-computed hourly stats accelerate feature engineering & dashboards
- Reduced row scans (83% fewer rows for 24h aggregate queries)
- Predictable performance under load

---

## 📤 Data Export

Full export:
```bash
docker compose exec api python scripts/export_sensor_data_csv.py
```
Incremental export (appends only new rows since last run):
```bash
docker compose exec api python scripts/export_sensor_data_csv.py --incremental
```
Custom output:
```bash
docker compose exec api python scripts/export_sensor_data_csv.py --output /tmp/readings.csv
```

---

## 🔭 Observability & Performance

| Aspect | Implementation |
|--------|----------------|
| Metrics | prometheus-fastapi-instrumentator (/metrics) |
| Logging | Structured JSON + correlation_id (ContextVar) |
| Tracing Keys | X-Request-ID propagation |
| Load Test (Day 17) | 50 users / 3m → Peak 103.8 RPS, P95 2ms, P99 3ms |
| Event Throughput | >100 events/sec capability validated |
| Performance Gains | 10× latency reduction vs baseline, DB agg 37.3% faster |

SLO Baseline:
- API P95 < 200ms (current P95 2–4ms)
- Predict cold load P99 < 3s (cached <1s)
- Drift check P95 < 5s (current 3–4ms)
- Error rate < 0.1% (core endpoints)

---

## 🤖 ML Platform

**Registry:** MLflow (persistent volume)  
**Model Families:**  
- Anomaly Detection: IsolationForest (synthetic + vibration), OneClassSVM (vibration)  
- Forecasting: Prophet tuned (20.86% MAE improvement) + challenger models  
- Classification: AI4I, Pump (100% accuracy), metadata-informed feature engineering  
- Audio: MFCC + RandomForest (MIMII, synthetic fallback pathway)  
- Vibration (NASA + XJTU): Statistical + FFT features (RMS, kurtosis, crest factor, spectral energy)  

**Project Gauntlet Phases:**  
1. AI4I Classification (ceiling performance)  
2. NASA Vibration Anomaly  
3. MIMII Audio Anomaly  
4. Pump Classification (perfect separation)  
5. XJTU Run-to-Failure Extension  
6. Drift + Lifecycle Automation  
7. Intelligent Model Selection UI  

**Intelligent Model Selection (UI):**
- MLflow model tags (e.g. `domain=bearing|audio|tabular`)
- Recommended subset by sensor type; manual override allowed

**Drift & Automation:**
- Drift Agent (`scripts/run_drift_check_agent.py`) – scheduled KS & PSI, emits Redis events
- Retrain Agent (`scripts/retrain_models_on_drift.py`) – rate-limited retraining with cooldown + MLflow version increment
- Slack/Webhook notification integration (configurable)
- CI model hash validation (`scripts/validate_model_hashes.py`) prevents silent drift/source mismatch

---

## 🛡️ Security

| Control | Status | Notes |
|---------|--------|-------|
| Auth | ✅ | API Key header |
| Rate Limiting | ✅ | slowapi (e.g. /api/v1/ml/check_drift: 10/min per key) |
| Threat Model | ✅ | STRIDE documented |
| Security Audit Checklist | ✅ | docs/SECURITY_AUDIT_CHECKLIST.md |
| Dependency Scanning | ✅ | Snyk CI (high/critical fail gate) |
| Input Validation | ✅ | Pydantic schemas |
| Logging Hygiene | ✅ | No secrets in logs |
| Future | ⏳ | Scope-based API keys, signed model manifests |

---

## ♻️ Resilience & Reliability

| Mechanism | Detail |
|-----------|--------|
| Idempotent Ingestion | Redis SET NX EX (10m) prevents duplicate event publication |
| Event Bus | Retry with exponential backoff + DLQ fallback |
| Graceful Degradation | Continues without Redis (logs warning) |
| Chaos Engineering | Toxiproxy latency / timeout / partition injection |
| Migrations | Manual (intentional) to avoid restart storms (Day 12 lesson) |
| Feature Contract | feature_names.txt persisted with models |
| Automated Recovery | Drift → Event → Retrain → Registry update |

---

## 🛠️ Development & CI/CD

| Area | Notes |
|------|-------|
| Environment | All operations containerized (DEVELOPMENT_ORIENTATION guidelines) |
| Migrations | Alembic – run manually: `docker compose exec api alembic upgrade heads` |
| Continuous Aggregates | Created outside Alembic transaction (TimescaleDB limitation) |
| CI Jobs | Lint, tests (coverage ≥80%), security scan, model hash validation, optional ML validation matrix |
| Poetry Install Hardening | Switched to pip-based deterministic install with retries |
| Load Tests | Locust scenarios (API + drift + model interactions) |
| Integration Tests | Async FastAPI + DB + Redis + Toxiproxy resilience tests |

---

## 🔀 Microservice Migration (Future Triggered)

Scaffolded but dormant services:
- prediction_service (port 8001)
- anomaly_service (port 8002)

Activation triggers (docs/MICROSERVICE_MIGRATION_STRATEGY.md):
- P95 latency > 50ms sustained
- >200 req/s sustained API throughput
- Team / deployment coupling friction
- Elevated CPU / memory saturation (>80%)

Gradual strangler pattern: migrate ML inference & analytics endpoints first.

---

## 📊 Key Performance Highlights

| Metric | Result |
|--------|--------|
| Load (50 users / 3m) | Peak 103.8 RPS |
| API P95 | 2 ms |
| DB Aggregation Gain | 37.3% faster (CAGG) |
| Forecast Improvement | Prophet tuned +20.86% MAE vs naive |
| Classification (Pump) | 100% accuracy, perfect ROC-AUC |
| Drift Endpoint P95 | ~3 ms |
| Dataset (Synthetic Base) | 9,000 readings / 15 sensors |

---

## 🧪 Testing Strategy

| Layer | Focus |
|-------|-------|
| Unit | Feature transformers, model utilities |
| Integration | DB + Redis + ingestion + drift stats |
| E2E | Drift detection workflow + model load |
| Load | Mixed endpoint concurrency + ingestion stress |
| Resilience | Induced latency, timeouts (Toxiproxy) |
| Security | Rate limit, auth rejection, dependency scan |
| ML Integrity | Model hash verification + artifact presence |

---

## 🔐 Operational Runbook (Essentials)

| Action | Command |
|--------|---------|
| Apply migrations | `docker compose exec api alembic upgrade heads` |
| Rebuild ML image | `make build-ml` |
| Execute forecasting notebook | `make train-forecast` |
| List MLflow models | Open http://localhost:5000 |
| Manual drift check | POST /api/v1/ml/check_drift |
| Force retrain (manual) | Trigger via retrain agent or notebook |
| Export data incremental | See Data Export section |

---

## 📄 License

Proprietary – see [LICENSE](./LICENSE)

---

## 🧾 Changelog Authority

All architectural & feature claims trace to: [30-day-sprint-changelog.md](./30-day-sprint-changelog.md)

---

## 🙋 Support

1. Check metrics/logs
2. Verify DB & Redis health
3. Confirm model registry persistence
4. Run drift endpoint with known sensor
5. Inspect retrain agent logs on drift events

---