# Smart Maintenance SaaS

*[**English**](README.md) | [Português](README_PORTUGUES.md)*

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/Status-V1.0%20Production%20Ready-brightgreen)](.)
[![Models](https://img.shields.io/badge/MLflow-17%2B%20Models-blue)](.)
[![Performance](https://img.shields.io/badge/P95%20Latency-2ms%20(@50u)-purple)](.)
[![Cloud](https://img.shields.io/badge/Cloud-S3%20%2B%20TimescaleDB-orange)](.)

A production‑ready Predictive & Prescriptive Industrial Maintenance platform with **revolutionary S3 serverless model loading**, cloud-native deployment (TimescaleDB, Redis, S3), enterprise-grade multi-agent system, and comprehensive event-driven architecture. **V1.0 Complete** with 95%+ production readiness achieved and all deployment blockers resolved.

---



## 📚 Documentation Index

### Core

- Main: this README
- **Final Development Roadmap**: [FINAL_DEV_ROADMAP_TO_V1.md](smart-maintenance-saas/docs/FINAL_DEV_ROADMAP_TO_V1.md) ⭐ **NEW**
- Development Orientation: [DEVELOPMENT_ORIENTATION.md](smart-maintenance-saas/docs/DEVELOPMENT_ORIENTATION.md)
- Sprint 4 Changelog: [sprint_4_changelog.md](smart-maintenance-saas/docs/sprint_4_changelog.md) ⭐ **UPDATED**
- Phase 2 Review: [SPRINT_4_END_OF_PHASE_2_REVIEW.md](smart-maintenance-saas/docs/SPRINT_4_END_OF_PHASE_2_REVIEW.md) ⭐ **NEW**
- 30-Day Sprint Changelog: [30-day-sprint-changelog.md](smart-maintenance-saas/docs/30-day-sprint-changelog.md)
- Final Sprint Summary: [final_30_day_sprint.md](smart-maintenance-saas/docs/final_30_day_sprint.md)
- Future Roadmap: [FUTURE_ROADMAP.md](smart-maintenance-saas/docs/FUTURE_ROADMAP.md)

### Architecture & Design

- System & Architecture: [SYSTEM_AND_ARCHITECTURE.md](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md)
- Comprehensive System Analysis: [COMPREHENSIVE_SYSTEM_ANALYSIS_REPORT.md](smart-maintenance-saas/docs/COMPREHENSIVE_SYSTEM_ANALYSIS_REPORT.md)
- Microservice Migration Strategy: [MICROSERVICE_MIGRATION_STRATEGY.md](smart-maintenance-saas/docs/MICROSERVICE_MIGRATION_STRATEGY.md)

### Database

- Database Docs: [db/README.md](smart-maintenance-saas/docs/db/README.md)
- ERD (dbml/png): [erd.dbml](smart-maintenance-saas/docs/db/erd.dbml), [erd.png](smart-maintenance-saas/docs/db/erd.png), [erd_darkmode.png](smart-maintenance-saas/docs/db/erd_darkmode.png)
- SQL Schema: [schema.sql](smart-maintenance-saas/docs/db/schema.sql)

### API & Config

- API Reference: [api.md](smart-maintenance-saas/docs/api.md)
- Config System: [core/config/README.md](smart-maintenance-saas/core/config/README.md)
- Logging Config: [core/logging_config.md](smart-maintenance-saas/core/logging_config.md)

### Performance & Testing

- Performance Baseline: [PERFORMANCE_BASELINE.md](smart-maintenance-saas/docs/PERFORMANCE_BASELINE.md)
- Load Test Report (Day 17): [DAY_17_LOAD_TEST_REPORT.md](smart-maintenance-saas/docs/DAY_17_LOAD_TEST_REPORT.md)
- DB Perf (Day 18): [DAY_18_PERFORMANCE_RESULTS.md](smart-maintenance-saas/docs/DAY_18_PERFORMANCE_RESULTS.md)
- Load Testing Instructions: [LOAD_TESTING_INSTRUCTIONS.md](smart-maintenance-saas/docs/LOAD_TESTING_INSTRUCTIONS.md)
- Coverage Plan: [COVERAGE_IMPROVEMENT_PLAN.md](smart-maintenance-saas/docs/COVERAGE_IMPROVEMENT_PLAN.md)
- Tests Guide: [tests/README.md](smart-maintenance-saas/tests/README.md)

### ML & Data

- ML Docs: [ml/README.md](smart-maintenance-saas/docs/ml/README.md)
- Models Summary: [MODELS_SUMMARY.md](smart-maintenance-saas/docs/MODELS_SUMMARY.md)
- Intelligent Model Selection (Live): [Dynamic Selection Section](smart-maintenance-saas/docs/MODELS_SUMMARY.md#intelligent-dynamic-model-selection-live-system)
- Project Gauntlet Plan: [PROJECT_GAUNTLET_PLAN.md](smart-maintenance-saas/docs/PROJECT_GAUNTLET_PLAN.md)
- DVC Setup Guide: [DVC_SETUP_GUIDE.md](smart-maintenance-saas/docs/DVC_SETUP_GUIDE.md)
- DVC Setup Commands: [dvc_setup_commands.md](smart-maintenance-saas/docs/dvc_setup_commands.md)

### Security & UI

- Security: [SECURITY.md](smart-maintenance-saas/docs/SECURITY.md)
- Security Audit Checklist: [SECURITY_AUDIT_CHECKLIST.md](smart-maintenance-saas/docs/SECURITY_AUDIT_CHECKLIST.md)
- UI Features (Comprehensive): [UI_FEATURES_COMPREHENSIVE.md](smart-maintenance-saas/docs/UI_FEATURES_COMPREHENSIVE.md)

### Services (Future)

- Anomaly Service: [services/anomaly_service/README.md](smart-maintenance-saas/services/anomaly_service/README.md)
- Prediction Service: [services/prediction_service/README.md](smart-maintenance-saas/services/prediction_service/README.md)

---

## 🚀 Quick Start (5 Minutes)

**Prerequisites:** Docker & Docker Compose installed + Cloud services provisioned.

**⚠️ IMPORTANT:** Sprint 4 has transitioned the system to cloud-native deployment. You'll need to populate `.env` with your cloud credentials.

```bash
git clone <repo>
cd enterprise_challenge_sprint_1_hermes_reply/smart-maintenance-saas

# Set up environment (CRITICAL STEP)
cp .env_example.txt .env
# MANUAL: Fill in your cloud credentials:
# - DATABASE_URL (cloud TimescaleDB)
# - REDIS_URL (cloud Redis)  
# - MLFLOW_TRACKING_URI, MLFLOW_ARTIFACT_ROOT (S3)
# - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

# Deploy cloud-integrated system
docker compose up -d --build

# Core services (cloud-connected):
# API:        http://localhost:8000/docs
# UI:         http://localhost:8501  
# MLflow:     http://localhost:5000 (connected to cloud backend & S3)
# Metrics:    http://localhost:8000/metrics
```

**Cloud Infrastructure Required:**
- ✅ **TimescaleDB Cloud** (Render/AWS/GCP)
- ✅ **Redis Cloud** (Render/AWS/ElastiCache)  
- ✅ **S3 Bucket** (AWS) for MLflow artifacts
- ✅ **IAM User** with S3 permissions

Datasets & models (optional, requires DVC):

```bash
cd smart-maintenance-saas
dvc pull
```
 
See DVC guides: [DVC_SETUP_GUIDE.md](smart-maintenance-saas/docs/DVC_SETUP_GUIDE.md), [dvc_setup_commands.md](smart-maintenance-saas/docs/dvc_setup_commands.md). Public data mirror: <https://drive.google.com/drive/folders/1cJvSRaBG0Fzs4D_wlUeVPM9l47RP_k3G?usp=sharing>


Stop & clean (non-destructive):

```bash
docker compose down
```

---

## 🧩 Platform Overview

| Capability | Status | Notes |
|------------|--------|-------|
| Ingestion & Idempotency | ✅ | Redis-backed SET NX EX (10m TTL) |
| Time-Series Storage | ✅ | TimescaleDB hypertable + compression + retention |
| Query Optimization | ✅ | Composite index (sensor_id, timestamp DESC) + hourly continuous aggregate |
| Observability | ✅ | Prometheus (/metrics), structured JSON logs, correlation IDs, health endpoints |
| ML Model Registry | ✅ | MLflow persistent (SQLite + volume) |
| Model Catalog | ✅ | 15+ models (anomaly, forecasting, classification, audio, vibration) |
| Drift Detection | ✅ | KS/PSI tests, /api/v1/ml/check_drift endpoint, agentized monitoring |
| Automated Retraining | ✅ | Event-driven (Redis pub/sub) retrain agent with cooldown policies |
| Security Hardening | ✅ | API key auth (X-API-Key), rate limiting (slowapi), STRIDE checklist |
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

Related docs: `./smart-maintenance-saas/docs/db/README.md`, `./smart-maintenance-saas/docs/DAY_18_PERFORMANCE_RESULTS.md`

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
| Metrics | Prometheus via prometheus-fastapi-instrumentator (`/metrics`) |
| Logging | Structured JSON + correlation_id (ContextVar) |
| Tracing | X-Request-ID propagation (RequestIDMiddleware) |
| Load Test (Day 17) | 50 users / 3m → Peak 103.8 RPS, P95 2ms, P99 3ms |
| Event Throughput | >100 events/sec capability validated |
| Performance Gains | 10× latency reduction vs baseline, DB agg 37.3% faster |

SLO Baseline:

- API P95 < 200ms (current P95 2–4ms)
- Predict cold load P99 < 3s (cached <1s)
- Drift check P95 < 5s (current 3–4ms)
- Error rate < 0.1% (core endpoints)

Key environment variables (selection):

- `API_KEY` (required for API auth); UI reads from `.env`
- `DATABASE_URL`, `REDIS_URL` (compose set via Toxiproxy for chaos testing)
- `MLFLOW_TRACKING_URI`, `MLFLOW_S3_ENDPOINT_URL` (MLflow client)
- `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `FROM_EMAIL` (email)
- `SLACK_WEBHOOK_URL` (optional drift alerts)
- `DRIFT_CHECK_ENABLED`, `DRIFT_CHECK_SCHEDULE`, `DRIFT_THRESHOLD`
- `RETRAINING_ENABLED`, `RETRAINING_COOLDOWN_HOURS`, `MAX_CONCURRENT_RETRAINING`
- `DISABLE_CHROMADB` (feature store embedding off when true)
- `API_BASE_URL` for UI (use `http://api:8000` inside Docker)

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

Model portfolio (champions):

| Task | Model | Dataset | Key Metric |
| :--- | :--- | :--- | :--- |
| Anomaly Detection | `anomaly_detector_refined_v2` | Synthetic Sensor | Unsupervised |
| Forecasting | `prophet_forecaster_enhanced_sensor-001` | Synthetic Sensor | +20.86% MAE |
| Classification | `ai4i_classifier_randomforest_baseline` | AI4I 2020 UCI | 99.9% Acc |
| Vibration Anomaly | `vibration_anomaly_isolationforest` | NASA IMS | 10% Anomaly Rate |
| Audio Classification | `RandomForest_MIMII_Audio_Benchmark` | MIMII | 93.3% Acc |
| Classification | `pump_randomforest_baseline` | Kaggle Pump | 100% Acc |
| Vibration Anomaly | `xjtu_anomaly_isolation_forest` | XJTU-SY | 10% Anomaly Rate |

---

## 🖥️ UI Highlights

- System Dashboard: real-time metrics (memory, CPU time, requests, errors) parsed from `/metrics`
- Data Ingestion & Management: manual and CSV uploads with validation
- ML Predictions with Explainable AI: SHAP integration with TreeExplainer/KernelExplainer fallback
- Predictive Analytics Dashboard: trends, anomalies, forecasts
- Maintenance Management: schedule/track/record tasks
- Visualizations: matplotlib/plotly; export reports (PDF, CSV)

Related docs: `./smart-maintenance-saas/docs/UI_FEATURES_COMPREHENSIVE.md`

---

## ✉️ Notifications

- Email Service: `core/notifications/email_service.py` (STARTTLS, HTML/plain, drift/retrain templates)
- Slack/Webhook: optional drift alerts via `SLACK_WEBHOOK_URL`
- Graceful degradation when creds missing (logs instead of failing)

Configure via `.env` (see `./smart-maintenance-saas/.env.example`).
Also available: `.env.prod.example`, `.env.test` for environment-specific overrides.

---

## 🎛️ Live Demo Simulator

FastAPI router `apps/api/routers/simulate.py` provides:

- `POST /api/v1/simulate/drift-event` – generate statistical drift
- `POST /api/v1/simulate/anomaly-event` – create outliers
- `POST /api/v1/simulate/normal-data` – baseline data

Implements background ingestion, network resilience (Docker internal + localhost), and automatic drift check trigger.

UI integrates a “Live System Demo Simulator” panel for one-click demonstrations.

---

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

Operational notes:

- `toxiproxy_init` service auto-configures DB/Redis proxies on startup
- Entry script applies TimescaleDB sequence/PK alignment fix during container boot

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

Auth & Networking:

- API authentication via `X-API-Key`; UI sends headers automatically (see `API_KEY` in `.env`)
- Docker inter-service networking via service names (`API_BASE_URL=http://api:8000` in UI)

Makefile highlights (`smart-maintenance-saas/Makefile`):

- `make build-ml` / `make rebuild-ml` – build ML image
- `make synthetic-forecast` / `make synthetic-anomaly` – run training notebooks
- `make classification-gauntlet` / `make vibration-gauntlet` / `make audio-gauntlet`
- `make run-final-analysis` – project gauntlet report
- `make test-features` – feature engineering tests
- `make logs-api` / `make logs-mlflow` / `make logs-db`

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
| List MLflow models | Open <http://localhost:5000> |
| Manual drift check | POST `/api/v1/ml/check_drift` |
| Force retrain (manual) | Trigger via retrain agent or notebook |
| Export data incremental | See Data Export section |

---


## 📄 License

MIT – see [LICENSE](./LICENSE)

---

## 🧾 Changelog Authority

All architectural & feature claims trace to: `./smart-maintenance-saas/docs/30-day-sprint-changelog.md`

---

## 🙋 Support

1. Check metrics/logs
2. Verify DB & Redis health
3. Confirm model registry persistence
4. Run drift endpoint with known sensor
5. Inspect retrain agent logs on drift events

---
