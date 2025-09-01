# Final 30-Day Sprint Plan

Checklist (requirements to cover)

- Database: ERD source + exported image; initial SQL (CREATE TABLE); entity/field descriptions; constraints; future BI integration note.
- ML: Notebooks (.ipynb), dataset CSV (≥500 readings/sensor or justified synthetic), trained models (.joblib), charts (.png), problem justification and results.
- SaaS: One-command Docker Compose; health endpoints; ingestion; reporting; new /predict and /detect_anomaly endpoints; model loading lifecycle; observability.
- Docs: README sections for DB modeling, ML implementation, results, run instructions; video link (unlisted).
- Quality: Tests (unit/integration/e2e), CI; security (API key), no secrets; performance baseline; acceptance criteria met.

Key architecture decisions (consistent with repo)

- Keep PostgreSQL + TimescaleDB (already modeled/migrated/tests/docs). Don’t switch to InfluxDB.
- Keep FastAPI as API Gateway. Add ML endpoints there first; split into microservices only if needed after load testing.
- Use Alembic migrations; async SQLAlchemy; EventBus remains.
- Add lightweight model registry, observability, and resilience.

30‑Day Action Plan (detailed, step‑by‑step)

Week 1: Infra, DB artifacts, and data (Days 1–7)

Day 1: Wire Docker Compose and env
- Objective: One-command stack: db (TimescaleDB), api, ui.
- Actions:
  - Create docker-compose.yml (db, api, ui). API runs Alembic before uvicorn.
  - Ensure .env with DATABASE_URL for service-to-service (db host is “db”).
  - Verify health endpoints (/health, /health/db) in container.
- Files:
  - docker-compose.yml
  - .env (from .env.prod.example)
- Commands (zsh):
  - docker compose up -d --build
  - curl "http://localhost:8000/health"
  - curl "http://localhost:8000/health/db"
- Acceptance:
  - All services healthy; DB reachable; API docs accessible at /docs.

Day 2: Timescale policies + initial SQL schema export
- Objective: Add retention/compression/CAGG (optional), and produce initial SQL script.
- Actions:
  - New Alembic migration adding:
    - SELECT add_retention_policy('sensor_readings', INTERVAL '180 days');
    - ALTER TABLE sensor_readings SET (timescaledb.compress);
    - SELECT add_compression_policy('sensor_readings', INTERVAL '7 days');
    - Optional: CREATE MATERIALIZED VIEW CAGG for 1‑min aggregates.
  - Script to export schema as SQL (schema-only).
- Files:
  - alembic_migrations/versions/\<timestamp\>_timescale_policies.py
  - scripts/export_schema.sh
  - docs/db/schema.sql (generated)
- Commands:
  - poetry run alembic revision -m "add timescale policies"
  - poetry run alembic upgrade head
  - ./scripts/export_schema.sh
- Acceptance:
  - schema.sql committed; policies visible; migrations green.

Day 3: ERD source + exported image + DB docs skeleton
- Objective: Deliver ERD source and PNG + entity/field descriptions.
- Actions:
  - Add ERD source: docs/db/erd.dbml (or SQL Developer Data Modeler project).
  - Export ERD to docs/db/erd.png (or use eralchemy2 script).
  - Create docs/db/README.md: entities, fields, PK/FK, constraints, rationale.
- Files:
  - docs/db/erd.dbml
  - docs/db/erd.png
  - README.md
  - scripts/generate_erd.sh (optional)
- Acceptance:
  - ERD source + PNG in repo; DB README describes schema clearly.

Day 4: Ingestion hardening (idempotency + correlation IDs)
- Objective: Production-grade ingestion with duplicate protection and traceability.
- Actions:
  - Add Idempotency-Key header handling in /api/v1/data/ingest: reject duplicate (store hash/timestamp or a short-lived in‑memory cache with TTL).
  - Add request/correlation ID middleware; include in logs and responses.
- Files:
  - apps/api/middleware/request_id.py (or enable asgi-correlation-id)
  - data_ingestion.py (idempotency logic)
- Acceptance:
  - Replay with same Idempotency-Key doesn’t duplicate writes; logs show correlation_id.

Day 5: Data generation/export for ML
- Objective: Ensure ≥500 readings/sensor.
- Actions:
  - Use Streamlit “Send Test Data” and/or seed_data.py to populate.
  - Export dataset to CSV.
- Files:
  - scripts/export_training_data.py (optional) or psql COPY command
  - data/sensor_data.csv
- Commands:
  - psql "$DATABASE_URL" -c "\COPY (SELECT sensor_id,sensor_type,value,unit,timestamp FROM sensor_readings ORDER BY timestamp) TO 'data/sensor_data.csv' WITH CSV HEADER"
- Acceptance:
  - data/sensor_data.csv exists; has adequate rows per sensor.


UPDATED AND REFINED PLAN FROM NOW ON (STOPPED TO REVIEW THE PLAN ON THE END OF DAY 5 AND ELEVATED IT):

# Refined 30-Day Sprint Plan (Starting from Day 6)


Key enhancements integrated:
- **Scalability:** Early introduction of Redis for distributed idempotency (replacing in-memory cache), event bus retries for reliability, and optional microservice stubs for ML to enable horizontal scaling.
- **ML Robustness:** Use MLflow for a centralized model registry (replacing simple JSON files), Dockerized reproducible workflows with Makefiles, drift detection using Evidently AI, shared feature engineering, and telemetry for KPIs.
- **Database Optimizations:** Advanced indexing for forecasting queries and enabling continuous aggregates to reduce load on ML endpoints.
- **Security:** Early threat modeling using STRIDE, refined rate limiting tied to scopes, and JWT considerations for future auth.
- **Observability:** Expand to full Prometheus/Grafana stack post-load testing, with event lineage logging.
- **Testing:** Expanded e2e tests including drift scenarios, property-based tests for data generators.
- **Deployment/UI:** Kubernetes manifests as roadmap, Trivy scans in CI, enhanced Streamlit with previews.
- **General:** Iterative mini load tests, checksum validations, no deferments for critical items like Redis/drift (prioritized for production-readiness).

## Checklist (Requirements to Cover)

- **Database:** ERD source + exported image; initial SQL (CREATE TABLE); entity/field descriptions; constraints; indexing for ML queries; continuous aggregates; future BI integration note (e.g., Grafana dashboards).
- **ML:** Notebooks (.ipynb) with reproducible Dockerized runs via Makefiles; dataset CSV (build on existing ~9,000 readings); trained models (.joblib via MLflow); charts (.png); problem justification, results, drift detection (Evidently AI); shared feature engineering; telemetry KPIs.
- **SaaS:** One-command Docker Compose (enhanced with Redis/Grafana); health endpoints; ingestion (with Redis idempotency); reporting; /predict and /detect_anomaly endpoints; model loading lifecycle (MLflow); observability (full stack); event bus retries; optional microservice split.
- **Docs:** README sections for DB modeling (including indexes), ML implementation/results (with drift notes), run instructions (including Dockerized ML); security threat model; video link (unlisted); architecture diagram updates.
- **Quality:** Tests (unit/integration/e2e with drift/property-based); CI (with Trivy scans); security (API key scopes, rate limiting, threat model); no secrets; performance baseline (P95 < 200ms); acceptance criteria met; reproducibility guide.

## Key Architecture Decisions (Consistent with Repo, Enhanced)

- Retain PostgreSQL + TimescaleDB (already modeled/migrated/tests/docs). Add advanced indexes and continuous aggregates for efficient forecasting windows. No switch to InfluxDB.
- Retain FastAPI as API Gateway. Add ML endpoints there first; introduce microservice stubs for prediction/anomaly services (optional activation via env flag) after load testing justifies.
- Use Alembic migrations; async SQLAlchemy; enhance event bus with retries and optional persistence (Redis queues if needed).
- Implement lightweight MLflow model registry for versioning, metadata, and reproducibility (over simple JSON); include drift monitoring hooks.
- Add Redis for distributed idempotency and potential event queuing to support horizontal scaling.
- Observability: Start with logging/metrics; expand to Prometheus/Grafana for dashboards (e.g., anomaly KPIs, query latencies).
- Security: API keys with scopes; rate limiting; STRIDE threat model documented.
- Lean persistence: TimescaleDB for time-series; no polyglot DBs yet.
- Controlled complexity: Monolith-first with stubs for microservices; event-driven agents for extensibility (e.g., anomaly escalation).

## 30-Day Action Plan (Detailed, Step-by-Step)

### Week 1: Observability, Documentation, and Early Security (Days 6–7; Focus on Baseline Enhancements Post-Day 5)

Day 6: Observability (Metrics/Logs) + Event Bus Retries
- **Objective:** Establish baseline metrics, structured logs with correlation, and improve event bus reliability for agent orchestration. This builds on existing JSON logging in `core/logging_config.py` and prepares for ML integration.
- **Rationale/Context:** Correlation IDs (from Day 4 middleware) need full integration into logs/metrics for traceability across requests/events. Event bus (in `core/event_bus/`) currently lacks retries, risking lost events in high-load scenarios; add at-least-once semantics using a simple retry decorator (e.g., 3 attempts with exponential backoff).
- **Actions:**
  - Install `prometheus-fastapi-instrumentator` via Poetry (add to `pyproject.toml`).
  - Instrument FastAPI in `main.py`: Expose `/metrics` endpoint; add custom metrics for ingestion counts and DB query timings (use `sqlalchemy` event listeners in `core/database/`).
  - Update `core/logging_config.py`: Ensure JSON logs include `correlation_id` and add event lineage (e.g., `event_id` for bus events like `DataProcessedEvent`).
  - In `core/event_bus/`, add a retry decorator to publish/subscribe methods (use `tenacity` library; add to dependencies).
  - Test with `manual_test_anomaly_agent.py`: Simulate failures and verify retries.
- **Files:**
  - `main.py` (instrumentator init and include in app).
  - `core/logging_config.py` (enrich with lineage).
  - `core/event_bus/event_bus.py` (retry logic).
  - `pyproject.toml` / `poetry.lock` (add `prometheus-fastapi-instrumentator` and `tenacity`).
- **Commands (zsh):**
  - `poetry add prometheus-fastapi-instrumentator tenacity`
  - `docker compose up -d --build`
  - `curl "http://localhost:8000/metrics"` (verify output).
  - `poetry run python scripts/manual_test_anomaly_agent.py` (check logs for retries).
- **Acceptance:**
  - `/metrics` returns Prometheus data with custom counters (e.g., `ingestion_success_total`); logs show `correlation_id` and `event_id`; retries handle simulated bus failures (e.g., temp disconnect); CI tests pass.

Day 7: Documentation, Housekeeping, and Threat Model
- **Objective:** Update docs for clarity, ensure repo hygiene, and conduct a STRIDE threat model to prioritize security.
- **Rationale/Context:** With infra stable, document for evaluators/boss (e.g., link ERD/schema from Days 2-3). Threat model identifies risks like spoofing (fake API keys) or DoS (unlimited ML queries), informing later rate limiting. Use STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) on components (API, DB, ML, event bus).
- **Actions:**
  - Update main `README.md`: Add sections for one-command run (`docker compose up`), health endpoints, links to ERD (`docs/db/erd.png`), schema (`docs/db/schema.sql`), and dataset usage. Include quickstart for ingestion with curl examples.
  - Audit repo: Ensure no secrets in `.env` (use `.env.example`); add gitignore for temp files.
  - Create `docs/SECURITY.md`: Document STRIDE analysis (e.g., mitigate tampering with input validation in ML payloads; DoS via rate limiting).
  - Enhance Streamlit (`streamlit_app.py`): Add a simple timeseries preview button loading from `data/sensor_data.csv` (use `st.line_chart` with Pandas).
  - We will create a new document, docs/RISK_MITIGATION.md, containing a table of identified risks (e.g., Model Drift, Docker Resource Overload) and our planned mitigations.
  - At the end of each week, we will add a "Weekly Progress Summary" task. This involves preparing a 1-paragraph summary and a brief screen recording of the key achievements to share.
- **Files:**
  - `README.md` (updated sections).
  - `docs/SECURITY.md` (threat model).
  - `streamlit_app.py` (preview feature).
  - `.env.example` (scrubbed if needed).
- **Commands:**
  - `docker compose up -d`
  - Access Streamlit at `http://localhost:8501` and test preview.
- **Acceptance:**
  - README allows fresh clone/run in <5 mins; threat model covers all components with 2-3 mitigations each; Streamlit shows CSV preview; no secrets found (use `git grep` for check).


### Week 2: ML Notebooks, Models, Registry, and Endpoints (Days 8–14; Focus on Reproducible, Drift-Aware ML)

**Day 8: Notebook 01 – EDA + Reproducible Workflow Setup**

- **Objective:** Explore dataset; prepare features with shared engineering; set up Dockerized reproducible ML runs.
- **Rationale/Context:** Build on `data/sensor_data.csv` (~9,000 rows, 15 sensors). EDA identifies distributions/stationarity for time-series. Make workflows reproducible: Docker for env consistency (e.g., fixed library versions), Makefile for automation. Share features (e.g., scaling, lags) in `ml/features.py` for reuse in training/inference. Add DVC for dataset versioning to track changes and ensure reproducibility.
- **Actions:**
  - Install DVC via Poetry; initialize in repo root and track `data/sensor_data.csv`.
  - Create `Dockerfile.ml`: Base on Python 3.12-slim, install Poetry deps + ML libs (scikit-learn, prophet, evidently).
  - Add `Makefile`: Targets like `make eda` to run notebook in Docker.
  - Notebook: Load CSV, compute `.info()`/`.describe()`, handle missingness, plot time-series/distributions/stationarity (ADF test via statsmodels); save plots.
  - Implement `ml/features.py`: Shared transformers (e.g., MinMaxScaler for values, lag features for forecasting).
- **Files:**
  - `notebooks/01_data_exploration.ipynb`
  - `docs/ml/eda_preview.png` (exported plots).
  - `Dockerfile.ml`, `Makefile` (in root).
  - `ml/features.py` (new module under `core/ml/` or `apps/ml/`).
  - `pyproject.toml` (add scikit-learn, prophet, evidently, statsmodels, dvc).
- **Commands:**
  - `poetry add scikit-learn prophet evidently statsmodels dvc`
  - `dvc init; dvc add data/sensor_data.csv; git add data/sensor_data.csv.dvc .dvc/config; git commit -m "Add DVC tracking for dataset"`
  - `make eda` (runs notebook in Docker, saves outputs).
- **Acceptance:**
  - Notebook runs top-to-bottom in Docker; at least 3 plots (e.g., value distributions, autocorrelation); features module testable (e.g., unit test scaler); DVC tracks dataset (verify with `dvc status` clean).


**Day 9: Notebook 02 – Isolation Forest (Anomaly) + Feature Reuse**

- **Objective:** Train anomaly detector; save model via MLflow; generate charts.
- **Rationale/Context:** Use Isolation Forest for unsupervised anomalies on features like value/sensor_type. Reuse `ml/features.py` for consistency. Track with MLflow for metadata/metrics.
- **Actions:**
  - Install MLflow via Poetry; start server in compose (add service).
  - Pull latest dataset version with DVC before training.
  - Train in notebook: Fit on transformed data (from `features.py`); compute precision/recall if labels simulated; log to MLflow.
  - Save model as `anomaly_detector_v1` in MLflow registry; export anomaly scatter plot.
- **Files:**
  - `notebooks/02_anomaly_isolation_forest.ipynb`
  - `docs/ml/anomaly_scatter.png`
  - `docker-compose.yml` (add MLflow service: mlflow with SQLite backend).
- **Commands:**
  - `poetry add mlflow`
  - `dvc pull data/sensor_data.csv`
  - `docker compose up -d mlflow`
  - Run notebook: Log experiment to `http://localhost:5000`.
- **Acceptance:**
  - Model registered in MLflow with metrics (e.g., contamination rate); plot shows anomalies; notebook explains choice.


**Day 10: Notebook 03 – Forecast (ARIMA or Prophet) + Telemetry Setup**  

- **Actions**:  

  - Add mini-load test for MLflow model fetch.  

- **Files**: `locustfile.py`.  

- **Commands**: `locust -f locustfile.py --users 5 --run-time 2m`.  

- **Acceptance**: Load test passes; metrics include forecast errors.  



**Day 11: MLflow Registry Integration and Loader**  

- **Actions**:  

  - Add mini-load test for model loader (mock inference).  

  - Run AI code review for `apps/ml/model_loader.py`.  

- **Files**: `locustfile.py`, `apps/ml/model_loader.py`.  

- **Commands**: `locust -f locustfile.py --users 5`, `poetry run flake8 apps/ml/model_loader.py`.  

- **Acceptance**: Loader passes load test; review clean.  



**Day 12: ML API Endpoints + Database Indexing for Queries**  

- **Actions**:  

  - Mini-load test for `/predict` and `/detect_anomaly` with mock data.  

  - Add SLOs to `docs/PERFORMANCE_BASELINE.md` (e.g., P95 < 200ms, error rate < 0.1%).  

- **Files**: `locustfile.py`, `docs/PERFORMANCE_BASELINE.md`.  

- **Commands**: `locust -f locustfile.py --users 5`.  

- **Acceptance**: Endpoints meet SLOs in mini-test.  



**Day 13: Tests for ML Endpoints + Drift Detection Hooks**  

- **Actions**:  

  - Add e2e test for drift workflow (`tests/e2e/test_drift_workflow.py`).  

  - Mini-load test for `/check_drift`.  

- **Files**: `tests/e2e/test_drift_workflow.py`, `locustfile.py`.  

- **Commands**: `poetry run pytest tests/e2e/test_drift_workflow.py`, `locust -f locustfile.py --users 5`.  

- **Acceptance**: Drift test passes; load test stable.  



**Day 14: README ML Section, Artifacts, and Mini Load Test**  

- **Objective**: Document ML; baseline perf; add incremental data export.  

- **Actions**:  

  - Enhance `scripts/export_sensor_data_csv.py` with `--incremental` flag (append since `MAX(timestamp)`).  

  - Add test in `tests/integration/test_data_export.py` for incremental export.  

  - Update README with incremental export guide.  

  - Run mini-load test (all endpoints).  

  - Create Week 2 Loom video for ML endpoints.  

  - Log feedback in `docs/FEEDBACK_LOG.md`.  

- **Files**: `scripts/export_sensor_data_csv.py`, `tests/integration/test_data_export.py`, `README.md`, `locustfile.py`, `docs/FEEDBACK_LOG.md`.  

- **Commands**: `poetry run python scripts/export_sensor_data_csv.py --incremental`, `poetry run pytest tests/integration/test_data_export.py`, `loom record`.  

- **Acceptance**: Incremental export appends correctly; tests pass; video < 3 mins; feedback logged.  



#### Week 3: Scale, Resilience, Performance, and Microservices (Days 15–21)



**Day 15: Resilience – Timeouts, Retries, Error Handling + Redis Idempotency**  

- **Objective**: Harden system; migrate idempotency to Redis; test chaos scenarios.  

- **Actions**:  

  - Add `toxiproxy` to `docker-compose.yml` for chaos testing (Redis/DB latency/outages).  

  - Add chaos tests in `tests/integration/test_resilience.py` (e.g., Redis down, DB slow).  

  - Enable `pytest-cov` in `ci.yml` for 80/15/5 test pyramid ratio.  

  - Add `mem_limit`/`cpus` to `docker-compose.yml` (e.g., Redis: 256MB).  

- **Files**: `docker-compose.yml`, `tests/integration/test_resilience.py`, `ci.yml`.  

- **Commands**: `docker compose up -d toxiproxy`, `poetry run pytest tests/integration/test_resilience.py --cov`, `./scripts/monitor_resources.sh`.  

- **Acceptance**: Chaos tests pass; coverage > 80%; resources within limits.  



**Day 16: Security – Rate Limiting, Scopes + Threat Model Refinements**  

- **Actions**:  

  - Create `docs/SECURITY_AUDIT_CHECKLIST.md` (checklist for endpoints, scopes).  

  - Add Snyk scans to `ci.yml`.  

  - Rate limit `/check_drift` (10/min per key).  

- **Files**: `docs/SECURITY_AUDIT_CHECKLIST.md`, `ci.yml`, `main.py`.  

- **Commands**: `snyk test`, `poetry run pytest tests/api/test_rate_limits.py`.  

- **Acceptance**: Checklist complete; Snyk clean; rate limits enforced.  


Day 17: Load Testing (Locust) and Tuning + Event Bus Evaluation
- **Objective:** Meet SLOs; assess bus for persistence.
- **Rationale/Context:** Test full chain; if >100 events/sec, add Redis queues to bus.
- **Actions:**
  - Run Locust on ingest/predict/detect; tune workers/pools.
  - If needed, enhance bus with Redis (publish to queue).
- **Files:**
  - `locustfile.py` (full scenarios).
- **Commands:**
  - `locust -f locustfile.py --users 50`
- **Acceptance:**
  - P95 <200ms; no errors at target RPS; bus handles load (add queues if fails).

Day 18: Timescale Tuning, Indices + Continuous Aggregates
- **Objective:** Optimize for ML queries.
- **Rationale/Context:** Already planned; ensure CAGG reduces load (precompute windows).
- **Actions:**
  - Validate/add indexes via migration; enable CAGG if not (from Day 12).
  - Test query plans for forecasting windows.
- **Files:**
  - Alembic migration if needed.
- **Commands:**
  - `poetry run alembic upgrade head`
  - `psql $DATABASE_URL -c "EXPLAIN SELECT * FROM sensor_readings WHERE sensor_id = 'sensor-001' ORDER BY timestamp DESC LIMIT 100"`
- **Acceptance:**
  - Plans use indexes/CAGG; perf gain >20% on windows.

Day 19–20: Microservice Split (Activate if Needed) + K8s Roadmap
- **Objective:** Isolate ML if load justifies; add deployment scaffolds.
- **Rationale/Context:** Stubs from Day 12; create services with own FastAPI, model load.
- **Actions:**
  - If activated (env flag): Add `services/prediction_service/` and `services/anomaly_service/` (Dockerfiles, compose entries).
  - Gateway forwards internally.
  - Add `infrastructure/k8s/deployment.yaml` placeholders (e.g., API deployment).
- **Files:**
  - `services/prediction_service/app.py` etc.
  - `docker-compose.yml` (new services).
  - K8s files.
- **Acceptance:**
  - Chain works; latency within budget; K8s manifests valid (kubectl apply --dry-run).

**Day 21: CI/CD, Security Scans + Grafana Integration**  

- **Actions**:  

  - Add `ml-train` job in `ci.yml` with model hash validation (`docs/ml/baseline_hashes.json`).  

  - Create Week 3 Loom video for Grafana dashboards.  

  - Update `docs/FEEDBACK_LOG.md`.  

  - Re-audit `docs/SECURITY.md` using checklist.  

- **Files**: `ci.yml`, `docs/ml/baseline_hashes.json`, `docs/FEEDBACK_LOG.md`, `docs/SECURITY.md`.  

- **Commands**: `poetry run python scripts/validate_model_hashes.py`, `loom record`.  

- **Acceptance**: CI validates hashes; video < 3 mins; audit complete.  



### Week 4: Docs, Video, Polish, and Final Delivery (Days 22–30)

Day 22: DB Documentation Finish + Indexing Rationale
- **Objective:** Complete DB package.
- **Actions:**
  - Finalize `docs/db/README.md`: Add index/CAGG rationales, constraints.
  - Refresh ERD/schema if changed.
- **Acceptance:**
  - Self-contained; meets rubric.

**Day 23: ML Documentation Finish + Drift Monitoring Loop**

- **Objective:** Complete ML package; add retraining hooks.
- **Rationale/Context:** A static drift check is good, but a production system needs an automated loop.
- **Actions:**
  - Ensure notebooks reproducible; summarize in README with drift notes.
  - Add agent hook: On high drift, trigger retrain (scripted).
  - Use APScheduler in a core agent or new script for scheduled job (e.g., daily): Call `/api/v1/check_drift`, publish `DriftDetectedEvent` if PSI/KS > 0.1, notify via log and optional Slack webhook (via env var `SLACK_WEBHOOK_URL`).
- **Files:**
  - `README.md`
  - `scripts/retrain_models.py` (uses Makefile).
- **Acceptance:**
  - Docs clear; hook logs alerts.

**FINAL 9 DAYS**


## Final 9-Day Implementation Plan: Smart Maintenance SaaS

### **Overview and Rationale**
This consolidated plan provides a day-by-day roadmap to elevate the "Smart Maintenance SaaS" project for the competition. It merges the strategic focus of both original plans to maximize the "wow factor" and address critical gaps. The key objectives are:

* **Enhance Uniqueness:** Integrate explainable AI (XAI) with SHAP and a live demo simulator to dynamically showcase the system's autonomous capabilities.
* **Address Commercial Gaps:** Introduce foundational multi-tenancy to demonstrate scalability and commercial viability.
* **Strengthen Architecture:** Add model promotion safeguards in the MLOps loop and improve Redis resilience.
* **Bolster Production-Readiness:** Implement API key authentication and lightweight Prometheus monitoring.
* **Ensure Reproducibility:** Use DVC to manage datasets and models, making the project easy for judges to run.
* **Optimize Deployment:** Target a professional deployment on Render (backend) and Vercel (UI) for the final demo.

This plan assumes 4-6 hours of focused work per day, assisted by an AI coding partner.

---

### **Day 1: UI Enhancements, Explainable AI & API Security**
* **Focus:** Boost the "wow factor" and user trust from the very first screen.
* **Objective:** Polish the UI with a live dashboard, make ML models interpretable with SHAP, and secure the API endpoints.

#### **Step-by-Step Tasks**
1.  **Add System Dashboard to UI (1-2 hours):**
    * In `smart-maintenance-saas/ui/streamlit_app.py`, add a new `st.tab` titled "**📈 System Dashboard**".
    * Inside this tab, call the `/metrics` endpoint and use `st.metric` to display the key results.
    * Add an `st.line_chart` to visualize a time-series of anomaly counts or key sensor values.
2.  **Integrate SHAP for Explainable AI (2-3 hours):**
    * Add `shap` to your dependencies in `smart-maintenance-saas/pyproject.toml`.
    * In `smart-maintenance-saas/apps/api/routers/ml_endpoints.py`, modify the `/predict` function to compute SHAP values using `shap.TreeExplainer` for tree-based models (e.g., LightGBM) after making a prediction.
    * Return these SHAP values in the API response JSON.
    * In `streamlit_app.py`, when displaying a prediction, check for SHAP values and visualize them as a feature importance bar chart using `st.pyplot`.
3.  **Add Basic API Authentication (1 hour):**
    * In `smart-maintenance-saas/apps/api/dependencies.py`, create a dependency function `get_api_key` that checks for an `X-API-KEY` header and validates it against an environment variable.
    * Apply this new dependency to the routers in `data_ingestion.py` and `ml_endpoints.py`.

#### **Copilot Prompt**
"In `smart-maintenance-saas/ui/streamlit_app.py`, add a new tab 'System Dashboard' that queries the FastAPI `/metrics` endpoint and displays the results using `st.metric` and `st.line_chart`. Next, integrate SHAP: in `apps/api/routers/ml_endpoints.py`, update the `/predict` endpoint to compute and return SHAP values for tree-based models. Then, visualize these SHAP values as a bar chart in the Streamlit UI. Finally, create an API key dependency in `apps/api/dependencies.py` and apply it to the `data_ingestion` and `ml_endpoints` routers."

---

### **Day 2: Proactive Notifications & Live Demo Simulator**
* **Focus:** Make the system's autonomous intelligence visible and interactive.
* **Objective:** Implement email notifications for key system events and build a simulator to demonstrate the full MLOps loop on demand.

#### **Step-by-Step Tasks**
1.  **Implement Email Notifications (1-2 hours):**
    * Create a new file `smart-maintenance-saas/core/notifications/email_service.py`.
    * Inside, create a function `send_email(to, subject, body)` using Python's `smtplib`, configured via environment variables (e.g., `SMTP_HOST`, `SMTP_USER`).
    * In `smart-maintenance-saas/scripts/run_drift_check_agent.py`, call this service to send an alert when drift is detected.
    * In `smart-maintenance-saas/scripts/retrain_models_on_drift.py`, call this service to confirm a successful model retrain.
2.  **Build the Live Demo Simulator (2-3 hours):**
    * Create a new router `smart-maintenance-saas/apps/api/routers/simulate.py`.
    * Define a `POST /api/v1/simulate/drift-event` endpoint. This endpoint will use `numpy` to generate a batch of synthetic data exhibiting clear drift and post it to the `/api/v1/ingest` endpoint.
    * In `streamlit_app.py`, add a section "**🚀 Live System Demo**" with a button that calls the simulation endpoint and shows a status message like `st.status`.

#### **Copilot Prompt**
"Create an email notification service in `core/notifications/email_service.py` using `smtplib` and environment variables. Integrate this service into the agents in `scripts/run_drift_check_agent.py` and `scripts/retrain_models_on_drift.py` to send alerts. Next, create a new FastAPI router in `apps/api/routers/simulate.py` with a `/simulate/drift-event` endpoint that generates and ingests synthetic data with drift. Finally, add a button in `ui/streamlit_app.py` to trigger this simulation."

---

### **Day 3: MLOps Safeguards & Multi-Tenancy Foundations**
* **Focus:** Address commercial and technical gaps to demonstrate foresight and scalability.
* **Objective:** Implement a crucial model promotion safeguard and lay the architectural groundwork for multi-tenancy.

#### **Step-by-Step Tasks**
1.  **Implement Model Promotion Safeguards (2 hours):**
    * In `smart-maintenance-saas/scripts/retrain_models_on_drift.py`, after a new model is trained and registered in MLflow, add a validation step.
    * Compare the new model's performance on a holdout dataset against the current production model.
    * If the new model is better, use the `mlflow.MlflowClient` to automatically transition its stage from `None` to **`Staging`**, logging that it's ready for manual review before production.
2.  **Add Multi-Tenancy Foundations (2-3 hours):**
    * Create a new Alembic migration: `alembic revision -m "add_tenant_id_to_tables"`.
    * In the new migration file, add a `tenant_id` column (e.g., `sa.Column('tenant_id', sa.String, nullable=False, server_default='default_tenant')`) to the `sensor_readings` and `maintenance_logs` tables.
    * Update the Pydantic models (e.g., `SensorReadingPayload`) and CRUD operations (`crud_sensor_reading.py`) to handle and store the new `tenant_id` field.

#### **Copilot Prompt**
"In `scripts/retrain_models_on_drift.py`, after registering a new model, use the `mlflow.MlflowClient` to transition the model version to the 'Staging' stage only if its evaluation metrics are better than the current production model's. Next, create an Alembic migration to add a `tenant_id` string column to the `sensor_readings` and `maintenance_logs` tables. Finally, update the Pydantic models and CRUD operations in `apps/api/routers/data_ingestion.py` and `core/database/crud/crud_sensor_reading.py` to handle this new `tenant_id` field."

---

### **Day 4: Monitoring & Redis Resilience**
* **Focus:** Bolster production-ready claims with professional monitoring and improved fault tolerance.
* **Objective:** Integrate Prometheus for application monitoring and configure Redis for high availability.

#### **Step-by-Step Tasks**
1.  **Integrate Prometheus Monitoring (2 hours):**
    * Add `prometheus-fastapi-instrumentator` to `pyproject.toml`.
    * In `smart-maintenance-saas/apps/api/main.py`, import `Instrumentator` and instrument the app to expose a `/metrics` endpoint.
    * Update `docker-compose.yml` to add a `prometheus` service and a placeholder for `grafana`.
2.  **Enhance Redis Resilience (1-2 hours):**
    * In `docker-compose.yml`, update the Redis configuration to use a basic high-availability setup with a master and a sentinel.
    * Document the failover strategy in a new `docs/SCALABILITY.md` file.

#### **Copilot Prompt**
"Integrate Prometheus metrics into the FastAPI app in `apps/api/main.py` using `prometheus-fastapi-instrumentator`. Then, update the `docker-compose.yml` file to add Prometheus and Grafana services. Finally, modify the Docker Compose Redis setup to include a Sentinel for failover."

---

### **Day 5: Reproducibility with DVC**
* **Focus:** Ensure anyone can easily run and evaluate the project.
* **Objective:** Use Data Version Control (DVC) to manage datasets and models, making the project fully reproducible.

#### **Step-by-Step Tasks**
1.  **Implement DVC (2-3 hours):**
    * Run `dvc init` in the project root.
    * Configure a DVC remote storage (e.g., `dvc remote add -d myremote gdrive://...` or an S3 bucket).
    * Track your data and models: `dvc add data/` and `dvc add models/`.
    * Push the versioned data to remote storage: `dvc push`.
2.  **Update Documentation (1 hour):**
    * In `README.md`, add a "**Reproducibility**" section.
    * Clearly explain the setup steps: `git clone ...`, `pip install ...`, and `dvc pull`.

#### **Copilot Prompt**
"Guide me through setting up DVC in the `smart-maintenance-saas` project. Show me the commands to initialize DVC, add the `data/` and `models/` directories, configure a remote, and push the data. Finally, provide the markdown for a 'Reproducibility' section in the `README.md` that explains how to use `dvc pull`."

---

### **Day 6: Deployment Preparation**
* **Focus:** Prepare for a polished, professional, and always-on public demo.
* **Objective:** Deploy the backend services and the user interface to modern cloud platforms.

#### **Step-by-Step Tasks**
1.  **Finalize Docker Configuration (1 hour):** Ensure the `docker-compose.yml` file and associated Dockerfiles are clean and production-ready.
2.  **Deploy Backend to Render (2 hours):** Create a new Web Service on Render for the FastAPI backend. Configure it to build from your Git repository and set up all necessary environment variables.
3.  **Deploy UI to Vercel (2 hours):** Create a new project on Vercel for the Streamlit UI. Point it to your repository and configure the backend API URL as an environment variable.
4.  **End-to-End Testing (1 hour):** Thoroughly test the live application, especially the live demo simulator, to ensure the UI and backend are communicating correctly.

---

### **Day 7: Presentation Assets & Deployment Guide**
* **Focus:** Craft a compelling and clear narrative for the judges.
* **Objective:** Create the final documentation and video script, highlighting the project's key strengths.

#### **Step-by-Step Tasks**
1.  **Draft Deployment Guide (2 hours):** Create `docs/DEPLOYMENT_GUIDE.md`. Outline a strategy for scaling the application on a platform like AWS ECS Fargate, mentioning how multi-tenancy and monitoring would work in that environment.
2.  **Script 5-Minute Video (3 hours):** Write a detailed script for the presentation video. Structure it around the project's story, focusing on the live demo simulator, the SHAP explanations, and the proactive notifications as the main highlights.

---

### **Day 8: Final Polish & Testing**
* **Focus:** Iron out any remaining bugs and refine the user experience.
* **Objective:** Conduct comprehensive end-to-end testing on the deployed application and polish all documentation.

#### **Step-by-Step Tasks**
1.  **Full End-to-End Testing (3 hours):** Run through every feature of the live application. Test the simulation, authentication, multi-tenancy filtering (with test data), and notifications.
2.  **UI/UX Polish (2 hours):** Fix any minor UI inconsistencies, improve loading messages, and ensure all text is clear and error-free.
3.  **Documentation Review (1 hour):** Proofread the `README.md`, `DEPLOYMENT_GUIDE.md`, and all code comments for clarity and consistency.

---

### **Day 9: Video Production & Final Submission**
* **Focus:** Produce the final video and freeze the codebase for submission.
* **Objective:** Record a polished demo video, tag a final release, and prepare for submission.

