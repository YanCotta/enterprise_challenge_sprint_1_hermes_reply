# Smart Maintenance SaaS v1.0 Deployment Playbook

**Last Updated:** 2025-10-03  
**Status:** Archived - Historical Reference Only  
**Note:** This is a legacy document. For current v1.0 deployment procedures, see [V1_UNIFIED_DEPLOYMENT_CHECKLIST.md](../V1_UNIFIED_DEPLOYMENT_CHECKLIST.md) and [UNIFIED_CLOUD_DEPLOYMENT_GUIDE.md](../UNIFIED_CLOUD_DEPLOYMENT_GUIDE.md).

_Merged from the former v1.0 must-do checklist, V1 Readiness Checklist, Prioritized Backlog, and both latest system audit reports._

**System Architecture:** For comprehensive visual guides of the V1.0 system architecture, see [SYSTEM_AND_ARCHITECTURE.md](./SYSTEM_AND_ARCHITECTURE.md) which includes:
- [High-Level System Overview](./SYSTEM_AND_ARCHITECTURE.md#21-high-level-system-overview) - Complete architecture visualization
- [Multi-Agent System](./SYSTEM_AND_ARCHITECTURE.md#27-complete-multi-agent-system-architecture) - All 12 agents and their interactions
- [Data Ingestion Pipeline](./SYSTEM_AND_ARCHITECTURE.md#29-data-ingestion-and-processing-pipeline) - Event-driven data flow
- [MLOps Automation](./SYSTEM_AND_ARCHITECTURE.md#28-mlops-automation-drift-detection-to-retraining) - Drift detection and retraining
- [API Endpoints](./SYSTEM_AND_ARCHITECTURE.md#214-api-endpoints-architecture) - REST API structure
- [Deployment Architecture](./SYSTEM_AND_ARCHITECTURE.md#appendix-d-deployment-architecture-future-oriented-illustration) - Cloud deployment topology

## 1. Executive Summary

- Platform reliability remains strong (backend capability readiness 95–100% across core domains), while UI intentionally exposes the minimal set of workflows required for a truthful v1.0 demo.
- Five-day goal: polish existing pages, finish the remaining critical items, run smoke validation, and execute the VM deployment procedure with confidence.
- Advanced features (streaming metrics, artifact downloads, bulk ops, etc.) stay deferred to V1.5+; this document ensures there is a single source of truth for current scope, risks, validation, and deployment steps.
- Scope freeze: V1.0 focuses on a stable UI surfacing proven backend capabilities; no new feature breadth will be added before tag.

### Status Snapshot

| Dimension | Status | Notes |
|-----------|--------|-------|
| Backend Capabilities | ✅ Ready | Ingestion, prediction (auto version), anomaly/drift detection, scheduling, decision audit, metrics, observability all stable. |
| UI Coverage | ✅ Adequate | Data Explorer, Prediction, Decision Log, Model Metadata, Simulation, Metrics, Golden Path, Reporting prototype, Debug page all functional. |
| Deployment Prep | 🟡 In Progress | .env population and deployment automation still pending final validation; see Section 4. |
| Testing Coverage | 🟡 Minimal | Critical flows covered via targeted tests and upcoming smoke plan; broader suites deferred post v1.0. |
| Documentation Alignment | ✅ Synced | This playbook supersedes earlier checklist, backlog, and audit markdowns. |

## 2. Scope & Capability Overview

### 2.1 Backend Capability Matrix (authoritative readiness)

| Capability | Backend State | Notes |
|------------|---------------|-------|
| Data Ingestion (idempotent) | ✅ Stable | Correlation support, Redis idempotency guard. |
| Sensor Read Retrieval | ✅ Stable | Pagination, filtering, indexed queries. |
| Prediction (auto version) | ✅ Stable | Version resolution, latency capture, MLflow guard. |
| Drift Detection | ✅ Stable | KS-test implementation. |
| Anomaly Detection | ✅ Stable | Batch Isolation Forest, statistical fallback. |
| Simulation Endpoints | ✅ Stable | Drift/anomaly/normal payload generation. |
| Golden Path Orchestration | ✅ Stable | Event-driven pipeline with timeout protection. |
| Human Decision Persistence | ✅ Stable | Create/list API, decision audit log. |
| Model Registry (MLflow) | ✅ Stable | Disabled flag respected, latest version lookup. |
| Model Recommendations API | ✅ Stable | Sensor-type normalization, defensive fallbacks. |
| Reporting (JSON prototype) | ✅ Prototype | JSON-only report surface, no artifact storage. |
| Metrics (Prometheus snapshot) | ✅ Stable | Snapshot endpoint, no streaming. |
| Security (API key) | ✅ Stable | Rate limiting and key validation in place (multi-key refinement pending). |
| Redis Coordination | ✅ Stable | Configurable pool, startup guards, retry logic. |
| Observability | ✅ Stable | Structured logging, latency registry, correlation IDs. |

### 2.2 UI Exposure Matrix

| Capability | UI Exposure | Coverage Notes | V1.0 Action |
|-----------|-------------|----------------|-------------|
| Ingestion | ✅ Exposed | Manual form + verify pattern; verification sometimes races eventual consistency (expected). Page renamed to "Manual Sensor Ingestion". | ✅ VALIDATED 2025-10-02 - Fully operational. |
| Data Explorer | ✅ Exposed | Pagination, filters, cached sensor list. | ✅ VALIDATED 2025-10-02 - All functionalities operational. |
| Prediction | ✅ Exposed | Forecast persists results and maintenance orders confirm successfully with schedule details (2s latency). | ✅ VALIDATED 2025-10-02 - 100% functional after fixes. |
| Model Metadata | ✅ Exposed | Disabled vs empty state clarity. | Badge already live. |
| Drift Check | ✅ Exposed | Form-based. | None. |
| Anomaly Detection | ✅ Exposed | Form-based; humidity/voltage accepted. | None. |
| Simulation | ✅ Exposed | Drift/anomaly/normal simulations fire without `sensor_id` collisions; latency samples record per run. | Run through tabs to confirm responses and latency capture. |
| Golden Path | ✅ Exposed | Human decision stage now auto-approves via orchestrator-compatible request IDs; demo completes <90s. | Re-run with decision stage enabled to confirm success banner. |
| Decision Log | ✅ Exposed | Create/list/filter/CSV export. | Clarify no edit/delete. |
| Metrics Snapshot | ✅ Exposed | Manual/auto refresh; labelled “Snapshot Only”. | None. |
| Reporting JSON | ⚠️ Minimal | Prototype now prettifies JSON content and inlines chart previews; artifacts still deferred. | Document prototype scope and monitor for additional reports. |
| Streaming Metrics | ❌ Deferred | Backend not implemented. | Defer (see Section 3). |
| Artifact Downloads | ❌ Deferred | Persistence layer missing. | Defer. |
| Background SHAP | ❌ Deferred | Queue infra absent. | Defer. |
| Bulk Ops | ❌ Deferred | Endpoints/UI missing. | Defer. |
| Correlation Analytics | ❌ Deferred | Advanced analytics. | Defer. |
| Model Recommendation Optimization | ❌ Deferred | Optimization only. | Defer. |
| Notifications UI | ❌ Deferred | UI not built. | Defer. |
| Feature Lineage | ❌ Deferred | Visualization absent. | Defer. |
| Governance UI | ❌ Deferred | Policy UI absent. | Defer. |

### 2.3 V1.0 Deliverables (Scope Freeze)

| Deliverable | Backend Ready | UI State | Action Needed | Effort | Risk |
|-------------|---------------|----------|---------------|--------|------|
| Data Explorer | ✅ | ✅ | None (stability only). | XS | Low |
| Ingestion Form | ✅ | ✅ | Keep latency copy concise. | XS | Low |
| Prediction | ✅ | ✅ | Error hints verified. | XS | Low |
| Decision Log | ✅ | ✅ VALIDATED | Scope note: create/list only. All functionalities operational. | XS | Low |
| Model Metadata | ✅ | ✅ VALIDATED | Badge distinction confirmed. All functionalities operational. | XS | Low |
| Simulation Console | ✅ | ✅ VALIDATED | All 3 tabs (drift/anomaly/normal) working, 3ms latency. | XS | Low |
| Golden Path Demo | ✅ | ✅ VALIDATED | Completes in 64.4s with all 7 stages, human decision working. | XS | Low |
| Metrics Snapshot | ✅ | ✅ VALIDATED | Snapshot-only label present. All functionalities operational. | XS | Low |
| Reporting Prototype | ✅ | ✅ VALIDATED | JSON formatting, chart previews, maintenance feed operational. | XS | Low |
| Debug Page | ✅ | ✅ VALIDATED | Connectivity, health checks, diagnostics all operational. | XS | Low |
| Rerun Stability Layer | ✅ | ✅ | Central helper verified. | XS | Low |
| Smoke Script (CLI) | N/A | ✅ (script ready to run inside API env) | Execute before tag. | S | Low |

## 3. Deferred Scope (V1.5+ and beyond)

Streaming metrics, report artifacts (PDF/CSV), background SHAP processing, bulk ingestion and batch prediction UI, maintenance log viewer enhancements, model recommendation caching/virtualization, advanced notifications UI, multi-sensor correlation analytics, feature lineage visualization, and governance/retention policy UI remain explicitly deferred until after v1.0. Document any mention of these features as “deferred” or “prototype only”.

## 4. Priority Work Board

### 4.1 Open Critical & High-Priority Tasks

| Priority | Area | Task | Acceptance Criteria | Status / Notes |
|----------|------|------|---------------------|----------------|
| High | Security & API | Align API key validation across FastAPI middleware and UI/test fixtures (support multiple keys or documented test key). | Rate limiting tests return expected 200/429 responses; UI reaches ML endpoints without manual edits. | Open. |
| High | ML Agents | Ensure anomaly detector fallback path (IsolationForest + statistical backup) behaves correctly when `DISABLE_MLFLOW_MODEL_LOADING` is true. | AnomalyDetectionAgent integration suite green with serverless flag; manual anomaly request returns 200 with fallback payload. | Open. |
| High | Deployment | Populate production-ready `.env` (or secrets store) and validate values against `docs/DEPLOYMENT_SETUP.md`. | Deployment script finds `.env`, health checks succeed. | Open (operational). |
| High | Deployment | Finalize deployment automation (shell script + smoke test) and record execution. | `scripts/deploy_vm.sh` (or equivalent) runs end-to-end on target VM, invoking smoke tests with zero failures. | Open (wip). |
| High | Demo & Workflow | Resolve Golden Path timeout when human decision stage enabled (validation/prediction remain queued past 90s). | Demo completes with human stage on; status transitions through all stages < timeout. | Resolved 2025-09-30 – auto decision injector now mirrors orchestrator request IDs; rerun demo to verify. |
| High | UI & Scheduling | Fix prediction page "Create maintenance order" action so it confirms scheduling instead of resetting form. | Button triggers maintenance workflow and surfaces confirmation without page reset. | ✅ RESOLVED 2025-10-02 – Timezone awareness + past deadline handling fixed; maintenance orders complete successfully in 2s. |

### 4.2 Medium-Priority Improvements

| Priority | Area | Task | Acceptance Criteria | Status / Notes |
|----------|------|------|---------------------|----------------|
| Medium | Knowledge Agent | Decide on `DISABLE_CHROMADB` production policy and update LearningAgent expectations/tests. | Learning agent test suite passes under the chosen configuration; docs updated. | Open. |
| Medium | Deployment | Introduce multi-stage Docker builds (API/UI) to shrink image size and speed redeploys. | New Dockerfiles build, images functionally equivalent, size reduction documented. | Open. |
| Medium | Testing | Expand event bus integration tests to cover handler retries and DLQ paths beyond existing coverage. | Tests cover success, retry, DLQ with deterministic assertions. | Partially complete (baseline tests exist; broaden scenarios). |
| Medium | Simulation UI | Fix Simulation Console drift payload builder (`TypeError` on sensor_id) so all tabs execute successfully. | Drift/anomaly/normal simulations run without exceptions; latency samples recorded. | Resolved 2025-09-30 – sensor_id only bound once; confirm via UI pass. |
| Medium | Reporting Prototype | Improve JSON export readability (currently raw encoded blob) or document expected format. | Downloaded JSON matches structured content or docs clarify encoding. | Resolved 2025-09-30 – downloads prettify JSON and surface chart previews; keep prototype label. |

### 4.3 Low-Priority Follow-Ups

| Priority | Area | Task | Acceptance Criteria | Status / Notes |
|----------|------|------|---------------------|----------------|
| Low | Validation Agent | Provide a dict-like settings adapter (or fixture refactor) so validation agent tests can mutate configuration without monkeypatching. | `tests/integration/agents/core/test_validation_agent.py` passes using the new adapter. | Open. |
| Low | Test Infrastructure | Document/Testcontainers usage so Docker-in-Docker flows either mount the Docker socket or skip gracefully. | CI run shows Testcontainers-dependent suites run or skip with clear messaging. | Open. |
| Low | Observability | Add correlation ID to all agent/event logs and consider event payload versioning for forward compatibility. | Representative logs include correlation IDs; schema versioning plan noted. | Backlog (optional pre-tag). |
| Low | UI Enablement | Once all features stable, add contextual “?” help affordances on each UI action describing the underlying capability, data source, or tech. | Every visible action has tooltip/modal explaining purpose and backend tie-in. | Backlog (post-v1.0 polish). |
| Low | Deployment | Plan post-v1.0 cloud VM deployment (UI + API) wired to managed Postgres, Redis, S3, and ship a pt-BR localized UI variant. | Deployment runbook executed in cloud; localization toggle produces Brazilian Portuguese copy. | Backlog (post-release). |

### 4.4 Completed Milestones (for traceability)

- Hardened `DISABLE_MLFLOW_MODEL_LOADING` usage across model loader/utilities and API endpoints; added regression tests for enabled/disabled paths.
- Added deterministic ML version auto-resolution helpers/tests and normalized error payloads to FastAPI `{"detail": ...}` envelopes.
- Introduced Redis startup retries, default Docker configuration, and unit tests guarding init/teardown behavior.
- Added event bus retry/DLQ integration tests and updated agents to publish event objects directly.
- Cached Data Explorer sensor list retrieval, reducing repeated latency; retained TTL controls.
- Replaced `streamlit.experimental_rerun` with centralized `safe_rerun()` helper across all pages, preventing runtime crashes.
- Resolved latest_system_audit_1 findings: corrected Data Explorer API paths, added dropdown error handling, and hardened decision submission validation.
- Completed Golden Path, prediction, and maintenance automation upgrades documented in `ui_redesign_changelog.md`.
- Golden Path demo decision injector now issues `maintenance_approval_*` request IDs, keeping the human stage within the 90s SLA (2025-09-30).
- Prediction page retains the last inference run so maintenance scheduling confirmations persist after UI reruns (2025-09-30).
- Simulation Console payload builder avoids duplicate `sensor_id` bindings, restoring drift/anomaly execution (2025-09-30).
- Reporting prototype prettifies JSON output and previews base64 charts to improve readability while artifacts remain deferred (2025-09-30).

## 5. Risk Register (v1.0 scope)

| Risk | Impact if Occurs | Likelihood | Mitigation | Residual |
|------|------------------|------------|-----------|----------|
| Documentation drift reintroduced | Conflicting guidance, team confusion | Medium | Maintain this playbook as sole source; require updates here first. | Low |
| Golden Path intermittent failure | Demo credibility hit | Medium | Keep 90s timeout messaging, run smoke script after backend changes. | Low |
| Decision CRUD expectations | Users expect edit/delete | Medium | Prominent UI copy and docs clarifying create/list only in v1.0. | Low |
| Smoke script regressions | Reduced validation confidence | Low | Keep script minimal, run before tag; add to deployment automation. | Low |
| MLflow offline gaps | Prediction/anomaly endpoints fail without registry | Medium | Complete High-priority ML Agents task; add offline smoke test. | Low |
| Deployment secrets mismanaged | Production outage or leak | Medium | Finish .env/secrets workflow; document owner and rotation. | Medium |

## 6. Testing & Validation Plan (minimal v1.0 coverage)

| Category | What to Test | Tools / Commands | Pass Criteria |
|----------|--------------|------------------|---------------|
| API Health | `/health`, `/health/db`, `/health/redis`, `/metrics` | `curl` with API key where required | 200 responses, expected payloads. |
| Data Ingestion Round-Trip | `POST /api/v1/data/ingest` then `GET /api/v1/sensors/readings` | `curl` or smoke script | Reading appears with correct sensor/type; idempotency guard works. |
| Prediction Auto-Resolve | `POST /api/v1/ml/predict` with blank version | Smoke script or Postman | Auto version selects latest; latency logged. |
| Decision Log Workflow | `POST /api/v1/decisions/submit`, `GET /api/v1/decisions` | pytest integration or curl | Invalid payload → 422; valid payload appears in list & CSV export. |
| Simulation Endpoints | `POST /api/v1/simulate/*` | curl / tests | Responses 200, correlation_id returned. |
| Golden Path Orchestration | `POST` then `GET /status/{id}` loop | script (see audit), expect completion <90s | Status transitions through pipeline; maintenance events emitted. |
| UI Smoke | Load all Streamlit pages | Manual or Playwright smoke | No exceptions, hints visible, latency panels populate. |
| Redis/DB Persistence | Ingest data, restart services, re-query | docker-compose restart + curl | Data persists across restart. |

Run `pytest` (or `docker compose exec api pytest` within container) for targeted suites covering Redis client, ML version resolution, event bus retries, and schema validation. Supplement with manual UI walkthrough post-build.

**Note (2025-10-03):** Commands inside containers no longer require `poetry run` prefix as dependencies are installed via pip in `/opt/venv` and activated automatically.

## 7. Deployment Checklist (VM target)

1. **Prep credentials**: Copy `.env_example.txt` → `.env`, populate database URL, Redis URL, API_KEY, SECRET_KEY, JWT_SECRET, MLflow settings (or set `DISABLE_MLFLOW_MODEL_LOADING=true` for offline mode).
2. **Review secrets ownership**: assign rotation owner, store secrets in vault if available.
3. **Build images**: `docker compose build` (consider upcoming multi-stage optimization).
4. **Start stack**: `docker compose up -d` and wait for health checks (`curl http://localhost:8000/health`).
5. **Run smoke tests**: execute `scripts/smoke_test.py` (or equivalent) to verify API/UI/docs availability.
6. **Execute workflow validation**: run Golden Path script, anomaly + forecast endpoints, and sample decision submission.
7. **Check logs**: `docker compose logs api` (and others) for errors; ensure no unhandled tracebacks.
8. **Backups**: capture TimescaleDB dump (`pg_dump`) and document retention expectations.
9. **Monitoring hooks**: verify Prometheus scrape config (or note manual monitoring plan) and confirm metrics accessible.
10. **Document outcomes**: update this playbook with deployment timestamp, smoke results, and any deviations or waivers.

## 8. Monitoring & Follow-Up Questions

- Who owns production API key/secrets rotation and how often will they rotate?
- Will TimescaleDB run in Docker or managed service (define backup/restore SOP accordingly)?
- Is MLflow artifact storage local, S3, or disabled? (Decide before deployment.)
- What is the monitoring/alerting stack (Prometheus/Grafana, external tool)?
- Expected workload and scaling threshold (single VM vs future clustering)?
- SSL termination strategy (reverse proxy certificate ownership)?
- Do we need automated database backups and log shipping before GA?

## 9. Audit Traceability

- **latest_system_audit_1** (historical) issues—Data Explorer path mismatch, missing UI error handling, decision validation gaps—are resolved and folded into Section 4.4 for record keeping.
- **latest_system_audit_2** findings provide the backbone of Sections 2, 4, 6, and 7; remaining open items are explicitly tracked in Sections 4.1–4.3.
- This playbook replaces the former Prioritized Backlog, V1 Readiness Checklist, legacy audit markdowns, and standalone must-do checklist; update this file first whenever new tasks or decisions arise.

## 10. Release Readiness Overview

| Dimension | Status | Rationale |
|-----------|--------|-----------|
| Backend Core Capabilities | ✅ Ready | All critical services stable, instrumented, and covered by health checks. |
| UI Critical Workflows | ✅ Adequate | All golden-path pages functional with error handling and latency hints. |
| UI Breadth vs Backend | ⚠️ Intentional Gap | Approximately 30% of advanced backend capability deferred by design (see Section 3). |
| Performance (Observed) | ✅ Within Targets | p95 prediction <1.5s without SHAP; ingestion and data explorer responsive. |
| Reliability | ✅ Strong | Redis pool fixes, request validation, and timeout guards remove prior blockers. |
| Documentation Alignment | ✅ Synced | All roadmap, audit, and checklist content merged here. |
| Automated Tests | ⚠️ Minimal | Critical-path tests and smoke plan in place; broad coverage deferred post-v1.0. |

**Recommendation:** Proceed toward v1.0 once Section 4.1 tasks are complete or explicitly waived. Deferred features are strategic and should not block tagging.

## 11. Post-V1.0 Roadmap (Directional)

| Phase | Focus | Illustrative Items |
|-------|-------|-------------------|
| V1.1 | Hardening & Observability | Expand smoke/integration tests, add p50/p95 latency metrics, enrich demo telemetry. |
| V1.2 | Reporting & Artifacts | Implement artifact persistence/download workflow, retention schema, and UI polish. |
| V1.5 | Amplification Wave | Streaming metrics, background SHAP, bulk ops, correlation analytics, lineage, governance, notifications UI, enhanced recommendations. |

Future updates to this roadmap should continue in this playbook after v1.0 stabilization.

---

**Next update cadence:** revise after completing the High-priority tasks or immediately following the v1.0 deployment dry run—whichever happens first.
