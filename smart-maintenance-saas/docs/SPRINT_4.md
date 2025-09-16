# Project Completion and Delivery Roadmap (Cross-Referenced, Final)

Purpose: finalize Smart Maintenance SaaS from 55% to production-ready in 2.5 weeks with a cloud-first, execution-focused plan that maximizes demo impact and reduces integration risk.

Sources for alignment

- docs/COMPONENT_ANALYSIS.md
- docs/PRODUCTION_READINESS_CHECKLIST.md
- docs/SYSTEM_ISSUES_INVENTORY.md
- docs/SYSTEM_STATE_EXECUTIVE_SUMMARY.md
- docs/COMPREHENSIVE_SYSTEM_ANALYSIS_REPORT.md

## Execution Plan for Victory (2.5 Weeks, Cloud-First)

Philosophy: invert risk and deliver a production-like Golden Path early. Prioritize cloud MLflow + storage and a hosted demo over completing every component locally.

### Cross-Reference Coverage Map (reports → tasks)

- Cloud MLflow + storage: provision Postgres/Timescale, S3, Redis; deploy MLflow with `MLFLOW_BACKEND_STORE_URI` and `MLFLOW_ARTIFACT_ROOT` (addresses “Cloud Storage 0%” and unlocks agents).
- RBAC/JWT (pragmatic): implement JWT + simple scope checks now; full RBAC later. Files: `apps/api/auth.py`, `apps/api/dependencies.py`.
- Docker builds + env + limits: fix builds, create `.env.example`, add resource limits in compose.
- Golden Path agents (focus 4): Acquisition, Validation, AnomalyDetection (loads model from cloud MLflow), Notification.
- Event bus + agent registry: wire only required agents. Files: `core/agent_registry.py`, `core/events/*`.
- UI demo tab: end-to-end flow with live narration and success signal. File: `ui/streamlit_app.py`.
- Monitoring/perf: run Locust against public API; minimal Grafana optional.
- Security & ops: JWT secrets via cloud env; backup/restore scripts; delete orphaned services.

---

### Phase 1 (Days 1–4): Stabilize Builds and Deploy Core Cloud State

Goal: eliminate biggest unknowns first. Have MLflow + artifacts in S3 and DB in the cloud, verified via real runs.

- Task 1.1: Build fixes + complete env
  - Fix `Dockerfile`, `Dockerfile.ml`, `Dockerfile.mlflow` (network retries, base pinning).
  - Produce `.env.example` with S3, cloud DB, JWT, Redis, API URLs.
  - DoD: `docker compose build` passes twice; services boot with `.env` locally.

- Task 1.2: Provision cloud data services
  - Postgres/Timescale: create managed DB; capture `DATABASE_URL`.
  - S3 bucket: set `MLFLOW_ARTIFACT_ROOT=s3://<bucket>/<path>`; provide `AWS_*`.
  - Redis: provision managed Redis; capture `REDIS_URL`.
  - DoD: connection strings validated via `psql`, `aws s3 ls`, and `redis-cli`.

- Task 1.3: Deploy MLflow to cloud (e.g., Render)
  - Configure service env:
    - `MLFLOW_BACKEND_STORE_URI=postgresql+psycopg2://...`
    - `MLFLOW_ARTIFACT_ROOT=s3://<bucket>/<path>`
    - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`
  - DoD: MLflow UI public; artifacts saved to S3 for new runs.

- Task 1.4: Re-run key training notebooks pointing to cloud MLflow
  - Re-execute selected notebooks (e.g., `05_classification_benchmark`, `08_pump_classification`).
  - Validate runs in MLflow; confirm artifacts appear in S3 path.

- Task 1.5: Seed cloud DB
  - Point a seeder (e.g., `scripts/seed_data.py`) to cloud `DATABASE_URL` and load demo rows.
  - DoD: cloud DB has sample data and indexes; API health checks against cloud DB succeed locally.

Suggested commands

```zsh
# Build reliably
docker compose build --no-cache
docker compose build

# Sanity check cloud DB (replace placeholders)
psql "postgresql://<user>:<pass>@<host>:<port>/<db>" -c "select now();"

# Sanity check S3
aws s3 ls s3://<your-bucket>/
```

Exit criteria (Gate P1)

- Public MLflow live with S3 artifacts; at least 2 recent runs visible.
- Managed Postgres/Timescale reachable; seed data loaded.
- Managed Redis reachable.

---

### Phase 2 (Days 5–8): Implement the Golden Path (4 Agents Only)

Goal: end-to-end event flow using cloud MLflow model loading; keep scope tight.

- Task 2.1: Agents required for demo
  1) DataAcquisitionAgent → publishes `SensorReadingIngestedEvent`.
  2) ValidationAgent → consumes ingress, publishes `ValidatedDataEvent` (single-event path first; batch optional).
  3) AnomalyDetectionAgent → consumes validated event; loads model using `apps/ml/model_loader.py` (cloud MLflow); publishes `AnomalyDetectedEvent`.
  4) NotificationAgent → consumes anomaly; sends real email/webhook via `core/notifications/email_service.py`.

- Task 2.2: Event bus and registry
  - Register only the 4 agents in `core/agent_registry.py` and wire minimal topics.

- Task 2.3: Remove confusion
  - Delete `services/anomaly_service` and `services/prediction_service` as redundant; commit the removal.

DoD

- API “simulate anomaly” endpoint triggers full chain and sends a real notification.
- Logs show correlation ID through all 4 agents.

Exit criteria (Gate P2)

- One-click Golden Path works locally against cloud MLflow/DB/Redis.
- Orphaned services removed; registry includes only the demo agents.

---

### Phase 3 (Days 9–13): Cloud Deploy of API/UI + Demo Polish

Goal: a hosted, evaluator-friendly demo with pragmatic security and performance proof.

- Task 3.1: Deploy API and UI to cloud (e.g., Render)
  - API env: `DATABASE_URL` (cloud), `REDIS_URL` (cloud), `JWT_SECRET`, `MLFLOW_TRACKING_URI`.
  - UI env: `API_BASE_URL` (public API URL).
  - DoD: both services public; health checks GREEN.

- Task 3.2: UI as a Demo Control Panel
  - `ui/streamlit_app.py` main tab “🚀 Demonstração ao Vivo do Golden Path”.
  - Button: “Simular Ingestão de Anomalia” → calls `/api/v1/simulate/anomaly-event`.
  - Live narration log showing each step; final success banner.

- Task 3.3: Pragmatic security
  - Implement JWT sign/verify in `apps/api/auth.py` and simple scope checks in `apps/api/dependencies.py`.
  - Store `JWT_SECRET` in cloud env; use bearer token for protected demo endpoints.

- Task 3.4: Performance proof
  - Run Locust against the public API URL and capture a screenshot ≥ 103 RPS.
  - Add image to `README.md` and link in the UI tab or docs.

Suggested commands

```zsh
# Locust against public API
locust -f locustfile.py --headless -u 200 -r 20 -t 5m --host https://<public-api-host>
```

Exit criteria (Gate P3)

- Public UI/API deployed; Golden Path completes over the internet.
- JWT-protected endpoints functional; performance screenshot saved in repo.

---

### Phase 4 (Days 14–15): Delivery Package

Goal: make the submission irrefutable with URLs, screenshots, and a focused video.

- Task 4.1: Documentation + video
  - Update `README_PORTUGUES.md` with:
    - Public UI URL and public MLflow URL.
    - Production diagram (Render + Cloud DB + S3 + Redis).
    - Locust performance screenshot.
  - Record a 5-minute video following the Golden Path live; show alert email and MLflow run.

- Task 4.2: ESP32 “check-the-box”
  - Add `/docs/esp32` (or `/ingest`) with a Wokwi simulation link and serial monitor screenshot.
  - Note in README: “pipeline supports any HTTP JSON source including ESP32 (see example)”.

Exit criteria (Gate P4)

- Docs updated with URLs and evidence; video recorded and linked.
- ESP32 evidence folder present.

---

## Golden Path Demo (quick reference)

- API button triggers: DataAcquisition → Validation → AnomalyDetection (loads model from cloud MLflow) → Notification.
- UI tab “End-to-End Flow Demo” shows live event trail and success confirmation.
- DoD: Single click produces anomaly notification and visible event trace in UI.

---

## Risks & Mitigations

- Cloud integration risk → front-load MLflow/S3/DB deployment (Phase 1) and validate with real runs.
- Security scope creep → implement JWT + scopes; defer full RBAC.
- Time risk on dashboards → prioritize demo tab; make Grafana optional.

---

## Appendix A: `.env.example` (cloud-first template)

```env
# Core
ENV=production
LOG_LEVEL=INFO

# API / Security
API_KEY=change-me
JWT_SECRET=change-me

# Database (cloud)
DATABASE_URL=postgresql+asyncpg://user:pass@db-host:5432/smart_maintenance

# Redis (cloud)
REDIS_URL=redis://redis-host:6379/0

# MLflow (cloud)
MLFLOW_TRACKING_URI=https://your-mlflow.example.com
MLFLOW_ARTIFACT_ROOT=s3://your-bucket/mlflow-artifacts
AWS_ACCESS_KEY_ID=change-me
AWS_SECRET_ACCESS_KEY=change-me
AWS_DEFAULT_REGION=us-east-1

# UI
API_BASE_URL=https://your-api.example.com

# Notifications (email/webhook)
EMAIL_SMTP_HOST=
EMAIL_SMTP_PORT=587
EMAIL_SMTP_TLS=true
EMAIL_SMTP_USER=
EMAIL_SMTP_PASS=
EMAIL_TO=

# Misc
PROMETHEUS_MULTIPROC_DIR=/tmp/prom
```

---

## Acceptance Gates (phase-based)

- Gate P1 (Day 4): MLflow live with S3 artifacts; managed Postgres/Timescale + Redis reachable; seed data loaded.
- Gate P2 (Day 8): Golden Path works locally against cloud services; orphaned services removed; agents registered.
- Gate P3 (Day 13): API/UI deployed publicly; JWT scopes enforced; performance screenshot ≥ 103 RPS committed.
- Gate P4 (Day 15): Docs updated with URLs/diagram/screenshots; 5-min video recorded; ESP32 evidence folder present.
