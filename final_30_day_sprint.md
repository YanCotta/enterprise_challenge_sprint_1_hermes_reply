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

Day 6: Observability (metrics/logs)
- Objective: Baseline metrics and structured logs.
- Actions:
  - Add prometheus-fastapi-instrumentator; expose /metrics.
  - Ensure JSON logs with correlation_id; log DB query timings at info in debug mode.
- Files:
  - main.py (instrumentator init)
  - core/logging_config.py (JSON formatter update, if needed)
- Acceptance:
  - /metrics accessible; logs include request_id and basic timings.

Day 7: Documentation and housekeeping
- Objective: Clear docs and repo hygiene.
- Actions:
  - Update main README: Compose run, health endpoints, links to ERD/schema.
  - Ensure no secrets in repo; .env.example updated.
- Acceptance:
  - README shows one-command run; DB artifacts linked; environment instructions clear.

Week 2: ML notebooks, models, and endpoints (Days 8–14)

Day 8: Notebook 01 – EDA
- Objective: Explore dataset; prepare features.
- Actions:
  - Create notebooks/01_data_exploration.ipynb: load CSV, .info(), .describe(), missing data; plots (temp/humidity/time series); stationarity notes if forecasting.
- Files:
  - notebooks/01_data_exploration.ipynb
  - docs/ml/eda_preview.png (optional)
- Acceptance:
  - Notebook committed; at least three meaningful plots saved.

Day 9: Notebook 02 – Isolation Forest (anomaly)
- Objective: Train anomaly detector; save model and chart.
- Actions:
  - Train sklearn IsolationForest on features (e.g., value or [temp, humidity]); choose features from EDA.
  - Save model to models/anomaly_detector_v1.joblib.
  - Export scatter with anomalies highlighted to docs/ml/anomaly_scatter.png.
- Files:
  - notebooks/02_anomaly_isolation_forest.ipynb
  - models/anomaly_detector_v1.joblib
  - docs/ml/anomaly_scatter.png
- Acceptance:
  - Model loads; visual shows anomalies; notebook explains choice.

Day 10: Notebook 03 – Forecast (ARIMA or Prophet)
- Objective: Train forecaster; save model and chart.
- Actions:
  - Train ARIMA (start with order (5,1,0)) or switch to Prophet if seasonality; document reasoning.
  - Save models/ts_predictor_v1.joblib.
  - Export forecast chart to docs/ml/forecast_plot.png.
- Files:
  - notebooks/03_forecast_arima.ipynb
  - models/ts_predictor_v1.joblib
  - docs/ml/forecast_plot.png
- Acceptance:
  - Forecast chart looks reasonable; notebook explains method/assumptions.

Day 11: Model registry and loader
- Objective: Robust model lifecycle.
- Actions:
  - Add models/active.json pointing to active versions.
  - Add per-model meta JSON (trained_at, data_window, metrics, checksum).
  - App startup loads models with integrity check; fallback to 503 if missing.
- Files:
  - models/active.json
  - models/anomaly_detector_v1.meta.json
  - models/ts_predictor_v1.meta.json
  - apps/api/routers/ml.py (or similar loader integration)
- Acceptance:
  - API logs show model versions loaded; failure path returns 503 with clear detail.

Day 12: ML API endpoints
- Objective: Public endpoints for prediction and anomaly detection.
- Actions:
  - Add POST /api/v1/predict (reads recent N points from Timescale, produces forecast).
  - Add POST /api/v1/detect_anomaly (classify a new reading).
  - Secure with API key scopes; add Pydantic schemas; update /docs.
- Files:
  - apps/api/routers/ml.py
  - main.py (include router)
- Acceptance:
  - curl requests return valid JSON; OpenAPI shows new endpoints.

Day 13: Tests for ML endpoints
- Objective: Quality and contracts.
- Actions:
  - Add unit tests for loader and basic inference shapes.
  - Integration tests calling /predict and /detect_anomaly with seeded data and mocked models where needed.
- Files:
  - tests/api/test_ml_endpoints.py
  - tests/unit/test_model_loader.py
- Acceptance:
  - Tests pass locally and in CI.

Day 14: README ML section and artifacts
- Objective: Document ML approach and results.
- Actions:
  - Add README sections:
    - Problem statements, dataset, model choices, charts, results, and limitations.
  - Link to notebooks, models, and charts.
- Acceptance:
  - Clear ML documentation in README; artifacts linked.

Week 3: Scale, resilience, performance, and (optional) microservices (Days 15–21)

Day 15: Resilience – timeouts, retries, and error handling
- Objective: Harden calls and DB access.
- Actions:
  - For any HTTP client (if used internally later): configure connect/read timeouts, limited retries with backoff.
  - Wrap DB queries with clear exception mapping; return 503/504 where appropriate.
- Files:
  - apps/api/dependencies/http_client.py (if needed later)
  - apps/api/routers/ml.py (timeouts on DB reads if using async with timeout)
- Acceptance:
  - Under induced slowness, endpoints degrade gracefully.

Day 16: Security – rate limiting and scopes
- Objective: Protect endpoints.
- Actions:
  - Add slowapi for rate limiting (per API key).
  - Confirm scopes: data:ingest, reports:generate already used; add ml:predict for ML endpoints if desired.
- Files:
  - apps/api/dependencies.py (scopes)
  - main.py (slowapi middleware/config)
- Acceptance:
  - Rate limit enforced; unauthorized/scopeless requests denied.

Day 17: Load testing (Locust) and tuning
- Objective: Meet performance SLOs.
- Actions:
  - Update locustfile.py to hit /api/v1/data/ingest, /predict, /detect_anomaly.
  - Tune uvicorn workers, DB pool sizes, and indices as needed.
- Files:
  - locustfile.py (updated tasks)
- Commands:
  - locust -f locustfile.py
- Acceptance:
  - Targets (example): P95 < 200ms for /predict and /detect; minimal errors at target RPS.

Day 18: Timescale tuning and indices
- Objective: Ensure query efficiency.
- Actions:
  - Validate existing indices (sensor_id, timestamp, composite index). Add missing ones if queries support them.
  - Consider continuous aggregates used by forecasting windows to reduce DB load.
- Files:
  - New Alembic migration if additional indexes needed.
- Acceptance:
  - Query plans efficient; measurable perf gain if bottlenecked.

Day 19–20: Optional microservice split (only if needed)
- Objective: Split ML services if required by scaling.
- Actions:
  - Create services/prediction_service and services/anomaly_service (FastAPI), load models at startup, expose healthz/readyz.
  - Gateway forwards requests internally via Docker network; per-service API keys.
  - Update docker-compose.yml; add health checks.
- Acceptance:
  - Gateway-to-service chain works; latency/error rate within budget.
- Note: Skip if the gateway-alone meets SLOs (preferred for simplicity).

Day 21: CI/CD and security scans
- Objective: Production-ready pipeline.
- Actions:
  - Ensure GitHub Actions runs: lint (ruff), tests (pytest), build Docker, optional trivy scan.
  - Publish Docker image on main merges (optional).
- Files:
  - ci.yml (update)
- Acceptance:
  - CI green; artifacts built; minimal warnings.

Week 4: Docs, video, polish, and final delivery (Days 22–30)

Day 22: DB documentation finish
- Objective: Competition-ready DB package.
- Actions:
  - Finalize README.md with entity/field rationales and constraints.
  - Ensure ERD PNG and schema.sql reflect current schema.
- Acceptance:
  - DB section self-contained; meets rubric.

Day 23: ML documentation finish
- Objective: Competition-ready ML package.
- Actions:
  - Ensure notebooks run top-to-bottom; outputs saved; charts present in docs/ml/.
  - Summarize results and limitations in README.
- Acceptance:
  - ML section meets rubric with clear justifications and visuals.

Day 24: Polished README and run instructions
- Objective: Single source of truth for evaluators.
- Actions:
  - Add architecture diagram (Gateway + TimescaleDB + Streamlit; optional ML services).
  - “How to run” with docker compose up -d.
  - API quickstart with curl examples for ingest, predict, detect, reports.
  - Add video link placeholder.
- Acceptance:
  - README crisp and complete; a judge can run the system in <5 minutes.

Day 25: Small runbooks and future BI integration note
- Objective: Professional touch.
- Actions:
  - Add a short “Troubleshooting & Runbooks” section (DB slow, model load fails).
  - “Future Visualization” note: Timescale continuous aggregates + Grafana; mention Streamlit in repo.
- Acceptance:
  - Adds credibility; aligns with brief’s “future visualization” requirement.

Day 26: Record 5‑minute video
- Objective: Compelling demo.
- Actions:
  - Show compose ps; health endpoints; Streamlit; ingestion; ML endpoints; Timescale data; charts; high-level architecture justification.
  - Upload unlisted to YouTube; add link to README.
- Acceptance:
  - Video within 5 minutes; link added.

Day 27: End-to-end test run + freeze prep
- Objective: Validate everything.
- Actions:
  - Fresh clone; run compose; execute a scripted sequence (ingest -> predict/detect -> report).
  - Verify artifacts (ERD PNG, schema.sql, notebooks, charts, CSV) present and accurate.
  - Tag a pre-release.
- Acceptance:
  - Smooth from scratch; no hidden deps; green tests.

Day 28: Final QA and accessibility pass
- Objective: Reduce friction for judges.
- Actions:
  - Check OpenAPI docs; add brief descriptions to new endpoints.
  - Confirm all links work in README.
  - Ensure no secrets; .env.example adequate.
- Acceptance:
  - Repository tidy; docs clean.

Day 29: Final release (freeze)
- Objective: Lock deliverable.
- Actions:
  - Create final release tag; mark that no changes will occur after submission deadline (per rules).
  - Optionally generate a GitHub release with a short changelog.
- Acceptance:
  - Repo frozen; aligns with rules.

Day 30: Buffer and celebration
- Objective: Catch last issues if any.
- Actions:
  - Respond to any feedback; minor non-code doc tweaks if allowed before hard deadline.
  - Backup video and artifacts.

Concrete file additions you’ll implement
- docker-compose.yml (stack)
- Alembic migration: Timescale retention/compression (+ optional CAGGs)
- docs/db/erd.dbml (or SQL Developer model), docs/db/erd.png
- docs/db/schema.sql (via scripts/export_schema.sh)
- README.md (entity/field constraints and rationale)
- notebooks/01_data_exploration.ipynb
- notebooks/02_anomaly_isolation_forest.ipynb
- notebooks/03_forecast_arima.ipynb
- data/sensor_data.csv
- models/anomaly_detector_v1.joblib (+ .meta.json)
- models/ts_predictor_v1.joblib (+ .meta.json)
- models/active.json
- apps/api/routers/ml.py; include in main.py
- scripts/export_schema.sh, scripts/generate_erd.sh, scripts/export_training_data.py (optional)
- Observability integration in main.py (metrics) and core/logging_config.py (JSON + correlation IDs)
- tests/api/test_ml_endpoints.py; tests/unit/test_model_loader.py
- README updates (DB/ML sections, run instructions, video link)

SLOs and acceptance thresholds (suggested)
- Functional: curl /health returns 200; /api/v1/data/ingest validates idempotency; /predict and /detect_anomaly return 200 with valid JSON.
- Performance: P95 latency < 200ms for /predict and /detect at moderate RPS (as per Locust test).
- Artifacts: ERD source+PNG, schema.sql, CSV, notebooks, models, charts all present and referenced in README.
- CI: Tests green; lint passes; Docker build succeeds.

Optional stretch (only if time remains)
- Split ML into microservices (prediction_service, anomaly_service)
- Add Grafana + Prometheus in compose (nice demo, optional)
- Drift monitoring hooks and alerts
- Canary model activation via models/active.json and % routing (within API)