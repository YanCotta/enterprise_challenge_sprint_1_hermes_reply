# Smart Maintenance SaaS

## V1.0 System Capabilities & Final UI Execution Blueprint

**Status:** Authoritative V1.0 Execution Plan  
**Date:** 2025-09-26  
**Author:** Automated Engineering Assistant  
**Purpose:** Provide a single, actionable blueprint that (a) inventories real backend capabilities, (b) classifies feature maturity, (c) defines the re-architected Streamlit UI, and (d) lays out a realistic 4–5 day refactor sprint to ship a stable, credible V1.0. Experimental or partial features are quarantined to preserve user trust.

---

## 0. Executive Summary

The backend (FastAPI + TimescaleDB + MLflow + Redis + EventBus) is production-aligned: ingestion, prediction, drift/anomaly analysis, simulation, and model metadata are reliable. The current Streamlit UI lags—monolithic, mixed-quality, and interleaving broken placeholders with working flows. We will refactor to a modular, capability-first UI with:

- Clear separation: Stable vs 🧪 Under Development.
- Predictable performance (defer SHAP; cache metadata).
- Modular pages under `ui/pages/` enabling incremental evolution.
- Closed-loop ingestion verification and latency surfacing for key operations.

Primary Outcome: A trustworthy “Analyst / Ops Dashboard” reflecting only what works today while transparently staging forthcoming capabilities.

---
## 1. Capability Inventory (Backend Truth Source)

| Domain | Capability | Endpoint(s) / Component | Current State | Notes / Evidence |
|--------|-----------|-------------------------|---------------|------------------|
| Data Ingestion | Single sensor reading ingest w/ idempotency | `POST /api/v1/data/ingest` (`data_ingestion.py`) | Stable | Redis-backed idempotency (graceful degrade) emits `SensorDataReceivedEvent` |
| Data Retrieval | List sensor readings (paged) | `GET /api/v1/sensors/readings` | Stable (enhanced) | Returns normalized schema `SensorReadingPublic`; supports `sensor_id`, `limit`, `offset`, `start_ts`, `end_ts` (Day 2 enhancement) |
| Data Retrieval | List sensors + stats | `GET /api/v1/sensors/sensors` | Stable | Provides counts + first/last timestamps |
| Simulation | Generate drift / anomaly / normal synthetic data (async ingestion) | `POST /api/v1/simulate/drift-event`, `/anomaly-event`, `/normal-data` | Stable (API) | BackgroundTasks schedule ingestion; UI previously unstable due to nested expanders |
| ML Prediction | Model prediction (auto version, feature adaptation, optional SHAP) | `POST /api/v1/ml/predict` | Stable (core prediction) | Feature adaptation & confidence extraction present; SHAP optional now (flag) |
| ML Prediction | Model version listing / resolution | `GET /api/v1/ml/models/{model}/versions`, `/latest` | Stable | Supports UI auto-resolve strategy |
| ML Anomaly Detection | Batch anomaly evaluation | `POST /api/v1/ml/detect_anomaly` | Stable | Uses loaded anomaly model; returns structured anomaly alerts |
| ML Drift | Distributional drift check (KS test) | `POST /api/v1/ml/check_drift` | Stable | Window-based KS test; returns counts + p-value + flags |
| ML Health | ML service health | `GET /api/v1/ml/health` | Stable | Validates registry accessibility (loads known model version) |
| Event System | Event publication bus | `EventBus`, coordinator | Stable (internal) | Used by ingestion + future decision/report events |
| Reporting | Report generation (threaded) | `POST /api/v1/reports/generate` (assuming prefix) | Prototype | Returns structured JSON; lacks artifact persistence / download |
| Human Decisions | Submit + list decisions (audit) | `POST /api/v1/decisions/submit`, `GET /api/v1/decisions` | Retrieval backend complete (UI viewer pending) | Day 2: decision history endpoint implemented; UI table scheduled next |
| Explainability | SHAP explainability | `compute_shap_explanation` path in `ml_endpoints.py` | Degraded | Works for tree models; KernelExplainer may be slow; now optional |
| Metrics | Prometheus scrape passthrough | `GET /metrics` (FastAPI app) | Stable (raw) | Parsing done client-side; no streaming timeseries yet |
| Model Loader | MLflow registry integration + feature schema extraction | `apps/ml/model_loader.py` | Stable | Caching dict; loads feature_names.txt if present |
| Redis Integration | Idempotency & potential caching | `redis_client.py` | Stable (core ops) | Used for ingestion idempotency only currently |
| Database | TimescaleDB storage (sensor readings) | ORM `SensorReadingORM` | Stable | Query path validated by dataset preview fix |
| Security | API key scoped access | dependency `api_key_auth` | Stable | Scopes enforced per router |

---
## 2. Capability Classification

### 2.1 Stable (Production-Ready Baseline)
- Data ingestion (single event)
- Sensor readings retrieval + sensor list
- Simulation API endpoints (drift/anomaly/normal)
- Prediction (model load, version resolution, feature adaptation)
- Drift and anomaly detection endpoints
- ML health check
- Raw metrics retrieval
- Model version metadata endpoints

### 2.2 Degraded / Performance-Risky
- SHAP explainability (latency risk on non-tree models)
- Model recommendation logic (UI-side enumeration—heavy; not yet optimized)
- Metrics visualization (static snapshot vs live streaming)

### 2.3 Prototype / Incomplete
- Report generation (no artifact or file export)
- Decision log UI (backend retrieval implemented Day 2; viewer not yet built)
- Orchestrated golden-path demo (placeholder only)

### 2.4 Missing (Documented Intent, No Implementation Yet)
-
- Decision audit/history UI timeline (enhanced view; basic list done)
- Downloadable reports (PDF/CSV/HTML)
- Real-time metrics streaming or push updates
- Background SHAP with caching or pre-computed explanations
- Multi-step pipeline orchestration UI (trigger + progress timeline)

---
## 3. UI Redesign Objectives
1. Remove user confusion by surfacing ONLY stable features in the default navigation.
2. Provide a clear boundary for experimental / under-development items (sandbox zone).
3. Optimize perceived performance (defer or async-load heavyweight panels—version metadata, SHAP, model recommendations).
4. Establish modular component functions to reduce monolithic Streamlit file complexity (goal: < 300 lines per functional module).
5. Prepare for incremental activation (feature flags / dynamic registry of panels).

---
## 4. Proposed Information Architecture

### 4.1 Primary Navigation (Stable)
| Section | Purpose | Components |
|---------|---------|------------|
| Overview Dashboard | System health snapshot + key KPIs | Metrics summary, recent ingestion stats, drift/anomaly quick indicators |
| Data Explorer | View & filter recent sensor readings | Paginated table, sensor filter, export CSV, date filters |
| Ingestion | Manual entry + CSV upload + immediate verification | Single reading form, upload widget, post-ingest confirmation block |
| ML Prediction | Deterministic prediction + optional explainability | Model selector (version auto-resolve), feature form, prediction result, optional SHAP tab |
| Drift & Anomaly | On-demand analysis tools | Drift check form, anomaly detection batch form, results panels |
| Simulation Console | Generate synthetic data to seed system | Drift, anomaly, normal data generation cards + status/results |

### 4.2 Secondary Navigation (Expandable / Collapsible Sidebar Group)
| Group: Advanced Analytics |
| - Reporting (prototype) |
| - Model Metadata Explorer (versions, stages, feature schema) |

### 4.3 Experimental Zone
Label: "🧪 Under Development"
| Experimental Panel | Status Note |
|--------------------|-------------|
| Golden Path Orchestration | Placeholder – awaiting event-driven pipeline assembly |
| Decision Audit Trail | Backend endpoint implemented (Day 2) – UI viewer pending |
| Report Artifact Downloads | Pending file generation & storage |
| Live Metrics Streaming | Requires push or periodic incremental diff fetch |
| Model Recommendations (Cached) | Awaiting caching layer & UI virtualization |

---
## 5. Page-Level Functional Specs

### 5.1 Overview Dashboard
**Inputs:** None (auto-load + manual refresh button)  
**Data Sources:** `/metrics`, `/api/v1/sensors/readings?limit=5`, aggregated counts  
**Widgets:**
- KPI bar (Ingested last 24h, Distinct sensors, Drift checks run, Anomalies detected)
- Metrics summary (memory, cpu secs, success vs error counts)
- Recent readings table (5 latest) with sensor badge
**Refresh Strategy:** 10–15s polling (configurable)

### 5.2 Data Explorer
**Core Contract:** Reliable retrieval & exploration; must load in < 2s for 100 rows  
**Features (MVP):**
- Server-side pagination controls (limit/offset)
- Sensor ID dropdown (populated from `/sensors` endpoint)
- Sort client-side (initial sort by timestamp DESC)
- Export: st.download_button building CSV from currently loaded page
- Quality badge coloring (if `quality` present)

### 5.3 Ingestion Page
**Flow:**
1. Manual form (sensor_id, sensor_type, value, unit, timestamp optional default now)
2. POST ingestion; display success event_id
3. Auto-fire verification: GET `/api/v1/sensors/readings?limit=1&sensor_id=X` and show the persisted row
4. CSV Upload Section: parse file → iterate rows → show progress + successes/failures summary
**Resilience:** Correlation ID visible; support Idempotency-Key optional header field input (advanced expander)

### 5.4 ML Prediction
**Modes:** Standard Prediction | Prediction + Explainability  
**Controls:** Model name (select), version (auto resolved + editable), feature inputs, explain checkbox  
**Panels:**
- Results (prediction, confidence, version resolved, latency metric)
- Explainability (collapsible) only rendered when SHAP returned
**Performance Guard:** If SHAP > 5s previously, persist recommendation to run without explainability (local session state)

### 5.5 Drift & Anomaly
- Drift Form: sensor_id, window_minutes, p_value_threshold, min_samples → response cards (p-value, drift flag)
- Anomaly Form: sensor_readings JSON editor OR quick generator referencing last N from DB
- Historical context (future): store previous drift checks (not in MVP)

### 5.6 Simulation Console
Refactor into three horizontally stacked or accordion sections (Drift | Anomaly | Normal). Each:
- Form → status spinner → summary metrics (events generated, simulation id)
- Info panel: next expected system reactions

### 5.7 Advanced: Reporting (Prototype)
- Form: report_type (enum), timeframe, format (disabled except JSON), include_sections multi-select
- Call generate endpoint → show JSON
- Disabled Download button with tooltip: “Artifact export not yet implemented”

### 5.8 Advanced: Model Metadata Explorer
- Model name input → fetch versions list → table (version, stage, status, created)
- Secondary fetch: feature schema presence (if available) displayed inline
- Potential caching: 5m TTL (st.cache_data)

### 5.9 Experimental Sandbox (🧪)
Cards with disclaimers + CTA buttons disabled or linking to placeholder panels.

---
## 6. Component Refactoring Plan

| Legacy Monolith Section | New Module Target | Action |
|-------------------------|-------------------|--------|
| Metrics + Prediction + Ingestion blended | `ui/pages/overview.py` | Extract metrics & KPIs |
| Prediction block | `ui/pages/prediction.py` | Isolate, add latency timing |
| Ingestion forms | `ui/pages/ingestion.py` | Move + wrap verification logic |
| Dataset preview logic | `ui/pages/data_explorer.py` | Streamlined retrieval wrapper |
| Simulation sections | `ui/pages/simulation.py` | Clean status pattern (no nested expanders) |
| Drift/Anomaly forms | `ui/pages/analysis.py` | Consolidate ML diagnostics |
| Advanced features | `ui/pages/advanced_reporting.py` | Keep prototype minimal |
| Experimental features | `ui/pages/experimental.py` | Feature flag ready |
| Shared API utilities | `ui/lib/api_client.py` | Central retry + error normalization |
| Shared widgets (tables, badges) | `ui/lib/components.py` | Reusable rendering primitives |

---
## 7. Endpoint → UI Mapping

| UI Panel | Endpoint(s) | Data Flow Summary |
|----------|-------------|-------------------|
| Overview | `/metrics`, `/api/v1/sensors/readings`, `/api/v1/sensors/sensors` | Parallel fetch; aggregate counts |
| Data Explorer | `/api/v1/sensors/readings`, `/api/v1/sensors/sensors` | Pagination + sensor filter |
| Ingestion | `/api/v1/data/ingest`, `/api/v1/sensors/readings` (verification) | POST then immediate GET verify |
| Prediction | `/api/v1/ml/models/{m}/latest`, `/api/v1/ml/models/{m}/versions`, `/api/v1/ml/predict` | Resolve version → predict → optionally SHAP |
| Drift & Anomaly | `/api/v1/ml/check_drift`, `/api/v1/ml/detect_anomaly`, `/api/v1/sensors/readings` | Retrieve samples (future), analyze |
| Simulation | `/api/v1/simulate/*` | POST async ingestion; no polling yet |
| Reporting (Prototype) | `/api/v1/reports/generate` | One-shot request |
| Model Metadata | `/api/v1/ml/models/{m}/versions`, `/api/v1/ml/models/{m}/latest` | Listing + stage awareness |
| Experimental | (future: decision history, orchestration) | Guarded placeholders |

---
## 8. UX & Performance Guidelines

| Concern | Guideline | Implementation Detail |
|---------|-----------|-----------------------|
| Perceived Latency | Defer SHAP rendering | Gate behind checkbox (already added) |
| Heavy Calls | Cache model version lists | `st.cache_data(ttl=300)` in metadata explorer |
| Error Clarity | Actionable remediation tips | Map common substrings ("not found", "features") to hints |
| Layout Focus | One logical task per page | Avoid vertical mega-scroll |
| Resilience | Timeouts & retries centralized | Single helper wrapping requests with exponential backoff |
| Observability | Log UI timing for critical calls | Add debug line: prediction latency, ingestion round-trip |
| Accessibility | Semantic headings + short labels | Use title case, avoid overloaded emoji |

---
## 9. Under Development Zone Policy
**Entry Criteria:** Feature lacks one of: reliability, acceptable latency, complete UX loop, or security assurance.  
**Presentation Rules:**
- Neutral styling (no green success tones)
- Explicit disclaimer block: “Preview – Not production ready”
- Links to roadmap issue / task identifier
- Disabled destructive actions (if any)

---
## 10. Execution Roadmap (Refactor Sprint)

### 10.1 Day-by-Day Micro Plan (Derived + Merged)

| Day | Focus | Tasks (Ref) | Key Files (create / modify) |
|-----|-------|-------------|-----------------------------|
| 1 | Structural Extraction & Critical Data UX | A1 (Explorer fix), A4 (Ingestion verify), Structure bootstrap | `ui/pages/overview.py`, `ui/pages/data_explorer.py`, `ui/pages/ingestion.py`, refactor `streamlit_app.py` |
| 2 | Prediction & Decision Foundations | A3 (Version auto-resolve hardening), A5 (Decision log scaffold) | `apps/api/routers/ml_endpoints.py`, `apps/api/routers/decisions.py` (new), `ui/pages/prediction.py`, `ui/pages/decision_log.py` |
| 3 | Demo Orchestration & Performance | A7 (Golden Path baseline), B1 (Caching) | `apps/api/routers/demo.py` (new), `ui/pages/experimental.py`, add caching decorators |
| 4 | Polish, Advanced Panels, QA | B2–B5 (error UX, metrics clarity), Acceptance checklist | `ui/lib/api_client.py`, `ui/lib/components.py`, docs update |
| 5 (buffer) | Risk Burn-down & Contingency | Deferred edge cases, load spot-check | N/A (stabilization) |

### 10.2 Task Breakdown with Acceptance Criteria

| Task ID | Title | Description / Actions | Done When |
|---------|-------|-----------------------|-----------|
| A1 | Dataset Explorer Restoration | Implement paginated call to `/api/v1/sensors/readings`; add sensor filter, CSV export. | ✅ (Day 1) 100 rows load <2s; filtering works; no 500s. |
| A2 | UI Structural Stability + Date Filters | Extract simulation & prediction out of monolith; remove nested anti-patterns; add backend date filtering. | ✅ (Day 2) Monolith deconstructed; date filters working server-side. |
| A3 | Prediction Version Auto-Resolution | Use `/models/{m}/latest` fallback to `/versions`; embed latency capture; explain toggle. | 🔄 Pending (next) Predict succeeds with empty version input; latency printed <1.5s w/o SHAP. |
| A4 | Ingestion Closed Loop | After POST, GET verify last row; show diff if mismatch. | ✅ (Day 1) Success panel shows persisted reading fields + latency + history. |
| A5 | Decision Log Prototype | Create read endpoint + table view (even if skeletal). | 🟡 Backend done (Day 2); UI table pending. |
| A6 | Reporting Isolation | Move prototype to Advanced group; mark limitations clearly. | Primary nav has no broken report entry. |
| A7 | Golden Path Minimal Orchestration | Basic POST triggers synthetic ingest + anomaly + status poll via Redis key. | Status screen shows progressing states until COMPLETE. |
| B1 | MLflow Metadata Caching | Wrap expensive calls with `st.cache_data(ttl=300)` or in-process dict. | Model version list retrieval <3s subsequent calls. |
| B2 | Error Guidance Layer | Map common backend errors to actionable hints (features mismatch, 404, etc.). | Users always see a hint block when errors occur. |
| B3 | Metrics Clarification | Remove misleading “live” labeling; add refresh timestamp. | Dashboard shows “Last updated: ISO time”. |
| B4 | Latency Telemetry | Measure & display prediction + ingestion round-trip times. | Latency metrics visible beside result. |
| B5 | Environmental Indicator | Show badge (Local / Container / Cloud) from env var. | Badge renders in sidebar header. |

> NOTE: A6 can be concurrent with A3/A4 if capacity allows.
| Order | Task | Outcome | Est |
|-------|------|---------|-----|
| 1 | Create modular `ui/pages` structure & shared libs | Foundation for decomposition | 0.5d |
| 2 | Extract stable Overview + Data Explorer pages | Clean separation | 0.5d |
| 3 | Move prediction panel & add latency metric | Faster iteration | 0.5d |
| 4 | Ingestion page w/ verification refactor | Trustworthy ingestion UX | 0.5d |
| 5 | Simulation & Analysis pages | Remove crash patterns | 0.5d |
| 6 | Advanced + Experimental group creation | Clear boundary | 0.25d |
| 7 | Model metadata explorer (cached) | Faster model workflows | 0.5d |
| 8 | Reporting prototype isolation | Prevent scope bleed | 0.25d |
| 9 | Central API client + error mapping | Consistent resilience | 0.5d |
| 10 | Polish: badges, export, disclaimers | Production readiness | 0.5d |

Total ~5.0d (core) + 1 buffer day (risk / polish).

---
## 11. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Hidden coupling in current monolith | Breakage on extraction | Incremental extraction + feature flag gating |
| SHAP latency persists | User abandons feature | Async background job + polling (future ticket) |
| Model registry enumeration slow | Perceived slowness on load | Lazy load only when prediction page opened |
| CSV upload large files | UI freeze | Stream rows + progressive feedback |
| Eventual audit/log endpoints delayed | Compliance gap | Provide interim export of decision submissions (local session log) |

---
## 12. Acceptance Criteria (Redesigned UI Initial Release)
- Navigation shows ONLY: Overview, Data Explorer, Ingestion, Prediction, Drift & Anomaly, Simulation, Advanced (collapsed), Experimental (collapsed)
- No broken panels accessible from primary navigation
- All stable endpoints respond < 2s p95 for single-user scenario
- Prediction without explainability < 1.5s p95 (local env) for baseline model
- SHAP disabled by default for non-tree models after >5s prior run (session heuristic)
- Dataset Explorer reliably renders 100 recent readings with filter
- Ingestion shows persisted record within 2 refresh attempts (< 1s typical)

---
## 13. Future Enhancements (Post-Refactor)
- Decision audit service & UI timeline view
- Report artifact generation (PDF + CSV bundles)
- Streaming metrics via websocket or polling diff
- Background SHAP job queue + persisted explanations
- Multi-sensor correlation & composite anomaly panel
- Feature store lineage visualization

---
## 14. Summary

## 15. Source File Reference Index (Quick Lookup)

| Category | Path / File | Purpose |
|----------|-------------|---------|
| API – Ingestion | `apps/api/routers/data_ingestion.py` | Idempotent single reading ingestion |
| API – Readings | `apps/api/routers/sensor_readings.py` | Paged readings + sensor list |
| API – ML Models | `apps/api/routers/ml_endpoints.py` | Prediction, versions, drift, anomaly, health |
| API – Simulation | `apps/api/routers/simulate.py` | Synthetic drift/anomaly/normal generation |
| API – Reporting | `apps/api/routers/reporting.py` | Prototype report generation |
| API – Decisions | `apps/api/routers/decisions.py` | Decision history & retrieval (backend complete) |
| API – (Planned) Demo | `apps/api/routers/demo.py` (to create) | Golden path orchestration endpoints |
| ML Loader | `apps/ml/model_loader.py` | MLflow registry loader + feature schema discovery |
| Event Bus | `core/events/event_bus.py` | Event publish/subscribe core |
| Redis Client | `core/redis_client.py` | Idempotency + future caching foundation |
| DB ORM | `core/database/orm_models.py` | SensorReadingORM and related models |
| UI Root | `ui/streamlit_app.py` | Current monolith to be decomposed |
| UI Planned Modules | `ui/pages/*.py` | New modular pages (overview, prediction, etc.) |
| Shared UI Lib (planned) | `ui/lib/api_client.py` | Central request + retries + error mapping |
| Shared UI Components | `ui/lib/components.py` | Tables, badges, KPI cards |
| Docs – Unified | `docs/UNIFIED_SYSTEM_DOCUMENTATION.md` | System-wide canonical reference |
| Docs – Models | `docs/MODELS_SUMMARY.md` | Registry performance & versions |
| Docs – Security | `docs/SECURITY.md` | Security model & scopes |
| Docs – Performance | `docs/PERFORMANCE_BASELINE.md` | Baseline & SLO targets |

---
**Action Next:** Approve this merged blueprint → begin A1/A4 extraction + scaffold `ui/pages` + add API client shell.
This blueprint grounds the UI in *actual* backend capabilities, reducing cognitive overhead and eliminating user-facing dead ends. By modularizing pages, gating unstable features, and enforcing latency-conscious patterns (optional SHAP, on-demand metadata), we set a sustainable base for iterative expansion toward enterprise-grade predictive maintenance workflows.

> Ready for review. Next step: approve structure → scaffold `ui/pages/*` & shared libs → migrate stable blocks.
