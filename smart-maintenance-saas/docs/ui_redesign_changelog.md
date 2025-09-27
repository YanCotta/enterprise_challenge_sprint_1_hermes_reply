# UI Redesign Pivot Changelog (Session Date: 2025-09-26)

## 1. Executive Summary
We initiated a strategic pivot from a monolithic Streamlit prototype toward a modular, maintainable, and extensible UI architecture. The focus today was to (a) decompose legacy logic, (b) establish robust data exploration & decision workflows, (c) introduce diagnostic & resilience layers, and (d) align backend persistence with emerging product semantics (human vs. maintenance decision records). Substantial groundwork is complete; remaining persistence & retrieval integration will continue next session.

## 2. High-Level Goals Addressed
| Goal | Outcome |
|------|---------|
| Reduce monolithic coupling | Split into multi-page Streamlit structure with clear logical boundaries. |
| Improve operator data visibility | Added Data Explorer with pagination, sensor filtering, date range filtering. |
| Capture human maintenance decisions | Added submission UI + backend event publishing; began persistence model introduction. |
| Add structured decision log | Implemented log page scaffold; root cause analysis for empty list; planned dedicated table. |
| Strengthen reliability & UX feedback | Centralized API client with retry/backoff & latency instrumentation; debug/diagnostics page. |
| Clarify domain separation | Differentiated Maintenance Logs vs. Human Decisions (new ORM model). |
| Enable future analytics & auditability | Introduced `HumanDecisionORM` (normalized persistence layer). |
| Migration readiness | Refactored Alembic env for async→sync URL translation & SSL normalization (in progress). |

## 3. Architectural & Structural Changes
**Before:** Single large Streamlit script performing API calls inline; minimal abstraction; limited fault handling.  
**After:**

- Multi-page pattern (`ui/pages/`) with discrete responsibilities.
- Centralized API interaction via `ui/lib/api_client.py` (resilience, config inspection, timing, error surfacing).
- Debug utilities encapsulated (connectivity probes, health endpoints, latency introspection).
- Clear path to add additional domain-focused pages without re-copying boilerplate.

## 4. New / Modified UI Pages
| File | Purpose | Key Features Added Today |
|------|---------|--------------------------|
| `streamlit_app.py` | Root shell & navigation bootstrap | Slimmed down; delegates functionality to pages; health & ingestion quick checks retained. |
| `pages/1_data_explorer.py` | Sensor data exploration | Pagination; sensor ID selector; start/end date filters; safe rerun shim (replacing deprecated `st.experimental_rerun`). |
| `pages/2_decision_log.py` | Human & maintenance decision visibility | Form for human decision submission; filter scaffolding; identified absence of persistence (see Section 7). |
| `pages/9_debug.py` | Diagnostics & observability | API connectivity probe; latency capture; dynamic config echo for troubleshooting environment mismatches. |

## 5. Resilience & Observability Enhancements
- Implemented unified API client layer:
  - Retry with backoff for transient network/API issues.
  - Latency timing & structured warnings for slow endpoints (e.g., sensor readings).
  - Config resolution & exposure for operator verification (base URL, environment values).
- Added debug page to quickly surface: health status, request success/failure patterns, and raw response contexts.
- Instrumented backend sensor readings endpoint to log query duration and emit warnings for outliers.

## 6. Backend & Domain Model Adjustments
- Confirmed mismatch between maintenance log listing endpoint (`/api/v1/decisions` → `MaintenanceLogORM`) and UI form that only emitted an event.
- Chosen Solution (Option 2): Introduce a dedicated persistent human decision table instead of overloading maintenance logs.
- Added `HumanDecisionORM` to `core/database/orm_models.py`:
  - Fields: `id`, `request_id`, `operator_id`, `decision`, `justification`, `additional_notes`, `confidence`, `correlation_id`, `timestamp`.
  - Serves as canonical audit record for human input events distinct from task execution logs.

## 7. Root Cause Analysis: Empty Decision Log
| Symptom | Analysis | Resolution Path |
|---------|----------|-----------------|
| Decision log page remained empty after successful submissions | Submission endpoint published `HumanDecisionResponseEvent` only; retrieval endpoint queried unrelated table (`MaintenanceLogORM`). | Create persistent `human_decisions` table + new retrieval endpoint; update UI to query new source. |

## 8. Migration & Infrastructure Work

| Aspect | Action Today | Status |

|--------|--------------|--------|

| Alembic env duplication | Removed duplicate `run_migrations_online/offline` definitions. | Completed |
| Async driver incompatibility | Normalized `postgresql+asyncpg` → `postgresql` for migration context. | Completed |
| SSL parameter mismatch | Introduced transformation `ssl=require` → `sslmode=require`. | Implemented; still seeing residual `ssl` in container runtime (diagnosis pending). |

| Migration generation | Attempted `alembic revision --autogenerate`; blocked by lingering `invalid connection option "ssl"`. | In progress |

| Fallback safety | Added defensive string replacement if parsing fails. | Completed |


**Outstanding Technical Issue:** Container environment still exposes `ssl=require` despite normalization logic—likely due to:
1. Environment variable substitution at container entry overriding modifications, or 
2. Earlier import / config evaluation order before transformation executes.  
Next step: Log raw inbound `DATABASE_URL` early or echo inside container to confirm runtime value; possibly override via `MIGRATION_DATABASE_URL` export logic or sanitize in `entrypoint.sh`.



## 9. Pending Implementation Tasks (Queued for Next Session)
| Priority | Task | Notes |
|----------|------|-------|

| High | Complete Alembic migration | Ensure `human_decisions` table created; verify indices. |

| High | Persist on submission | Modify human decision submission endpoint to insert row before/after event publish (ensure idempotency via `request_id`). |
| High | GET `/api/v1/decisions/human` endpoint | Pagination, filtering by operator, date, request_id, correlation_id. |
| Medium | Update Decision Log UI | Display human decisions; optional combined view with maintenance logs (segmented tabs). |
| Medium | Add minimal tests | ORM creation test + API round-trip create & list. |

| Medium | Backfill latency instrumentation (optional) | For new endpoints to maintain observability parity. |

| Low | Refine debug page | Add human decisions count + migration status introspection. |

## 10. Design & Data Integrity Considerations
- **Idempotency:** Use `request_id` for deduplicating retried decision submissions (possible unique constraint in future migration).
- **Auditability:** `timestamp` server default ensures unbiased capture time; consider separate `submitted_at` vs `effective_at` if later workflow timing semantics required.

- **Trace Correlation:** `correlation_id` reserved to unify chain across event bus, agents, and eventual ML inference traces.

- **Confidence Field:** Nullable; downstream analytics can model human-machine decision alignment.

## 11. Risks & Mitigations

| Risk | Impact | Mitigation Strategy |

|------|--------|---------------------|
| Migration still blocked by `ssl` DSN param | Delays persistence + UI accuracy | Add runtime logging; manually export sanitized URL; adjust `entrypoint.sh` to translate param before Alembic run. |
| Event-only form (no persistence) | Operator confusion (appears “lost”) | Prioritize persistence wiring first next session. |

| Latency regressions under load | Degraded UX & page timeouts | Extend instrumentation & possibly introduce server-side pagination caching layer later. |

| Duplicate decisions on retries | Data skew | Apply uniqueness (request_id + operator) or soft de-dupe logic when persisting. |


## 12. Validation Completed Today

- Manual UI smoke tests for Data Explorer (filters & pagination render without errors). 
- Decision submission returns HTTP 201 (event published). 
- Debug page successfully surfaces API health & latency metrics. 

- ORM model loaded by Alembic metadata (autogenerate attempt recognized metadata set; blocked only at connection). 


## 13. Suggested Immediate Next Technical Steps
1. Echo `DATABASE_URL` inside API container just before Alembic invocation to confirm unsanitized value.
2. If still contains `ssl=`, export a patched `MIGRATION_DATABASE_URL` (replace segment) prior to `alembic` command.

3. Generate migration; verify contains `human_decisions` definition (UUID PK + indexed fields). 

4. Implement persistence in submission endpoint (wrap in try/except; on DB failure still publish event with warning?).
5. Add GET endpoint + UI integration; differentiate human vs maintenance with tabbed interface.
6. Add simple test: create → list → assert fields + ordering.



## 14. Longer-Term Enhancements (Backlog Candidates)
- Add optional decision categories / taxonomy table.
- Introduce soft delete / status flag for decisions (e.g., superseded, retracted).
- Integrate streaming / WebSocket channel for real-time decision feed updates.

- Add role-based visibility (operator vs supervisor) once auth layer matures.

- Provide export (CSV / JSON) of human decisions for audit & model alignment tasks.

## 15. Artifact Inventory (Today’s Key Changes)
| Artifact | Change Type | Rationale |
|----------|-------------|-----------|
| `ui/pages/1_data_explorer.py` | Added / Enhanced | Core data visibility for sensor readings. |

| `ui/pages/2_decision_log.py` | Added | Entry point for human decision UX. |

| `ui/pages/9_debug.py` | Added | Operational diagnostics & latency checks. |
| `ui/lib/api_client.py` | Added / Centralized | Reliability & observability improvements. |
| `core/database/orm_models.py` | Modified | Added `HumanDecisionORM`. |
| `alembic_migrations/env.py` | Refactored | Async→sync normalization; SSL param transformation; duplication removal. |


## 16. Open Questions for Follow-Up

| Question | Context |
|----------|---------|
| Should decision submission be synchronous (persist then publish) or fire-and-forget? | Impacts UX feedback & failure semantics. |

| Do we need a composite uniqueness constraint now (request_id, operator_id)? | Avoids early duplicate proliferation. |

| Combine human + maintenance decisions in one endpoint with type discriminator? | Could reduce round trips but may conflate semantics. |

## 17. Summary

Core scaffolding for a maintainable, extensible UI is now in place along with the domain model required to properly represent human decisions. Remaining work centers on completing persistence, retrieval, and UI presentation for those decisions plus resolving a migration environment edge case related to SSL parameter translation.


---
_End of Day Snapshot – Ready to resume with migration resolution & persistence wiring next session._

## 18. End-of-Day Addendum (Post-Migration Actions – Late Session & Subsequent Updates)

### 18.1 Migration Chain Repair & Minimal Table Introduction
- Discovered missing historical Alembic revision (`71994744cf8e`) referenced but absent → blocked new revision generation.
- Added a **no-op placeholder migration** (`71994744cf8e_placeholder_recovered_missing_revision.py`) to restore a contiguous chain without retroactive schema changes.
- Regenerated migration after placeholder; initial autogenerate attempted to drop numerous legacy / unrelated tables (schema drift detected).
- Chose **Option A (Minimal Targeted Migration)** to avoid destructive operations. Trimmed autogenerated revision to include only:
  - `human_decisions` table creation (UUID PK + request/operator/correlation indices + timestamp default now()).
  - Three non-unique indexes: correlation_id, operator_id, request_id.
- Rebuilt API container to ensure the trimmed migration was the one applied.
- Ran `alembic upgrade head` successfully: upgrade path `71994744cf8e -> 7bbe1dbdb5f5` executed without attempting unrelated drops.

### 18.2 Verification Constraints & Notes
- Direct `psql` verification inside container failed (cloud-hosted Timescale uses network connection; local socket fallback not available in image invocation context).
- Inline verification attempt via `psycopg2` failed (driver not installed in production image by design—app uses asyncpg at runtime); accepted Alembic success log as authoritative for now.
- Next session: optionally add a lightweight FastAPI diagnostic endpoint or temporary script using async SQLAlchemy to confirm live columns.

### 18.3 Updated Status Summary (Revised & Expanded)

| Area | Status | Notes |
|------|--------|-------|
| Placeholder migration added | Done | Restored revision continuity. |
| Minimal human_decisions migration | Applied | No collateral schema changes. |
| Table indices | Applied | correlation_id / operator_id / request_id. |
| Persistence endpoint | Done | Human decision persisted then event published. |
| Read (GET) endpoint | Done | `/api/v1/decisions` returns ordered human decisions. |
| UI integration refresh | Done | Decision Log UI displays persisted decisions with pagination. |
| MLflow model loading circuit breaker | Added | `DISABLE_MLFLOW_MODEL_LOADING` flag prevents startup blocking. |
| Golden Path Demo endpoint | Enhanced | Now observes real EventBus events; step progression driven by actual published events. |
| Golden Path Demo UI | Enhanced | `3_Golden_Path_Demo.py` shows live steps, event stream, metrics & latency. |
| Golden Path Metrics | Added | Ingest→Prediction latency, total events, rolling event buffer (last 200). |
| Golden Path Decision Stage (optional) | Added | Flag to include human decision stage (injects HumanDecisionRequiredEvent). |
| Tests | Pending | Add model + API round-trip tests. |

### 18.4 Risks Newly Tracked

| Risk | New? | Mitigation Plan |
|------|------|-----------------|
| Silent absence of psycopg2 verification | Yes | Add optional diagnostic endpoint or short async query script. |
| Future autogenerate drift noise | Yes | Consider creating a “schema baseline” migration after stabilizing decisions to reduce noise. |

### 18.5 Immediate Next Session Priorities (Refined)

1. Implement persistence logic in submit endpoint (transaction + event publish; consider try/finally ordering).
2. Implement GET `/api/v1/decisions/human` with: limit, offset (or page), optional filters (operator_id, request_id, correlation_id, date range).
3. Update `pages/2_decision_log.py` to consume new endpoint (tabbed UI or single sourced view) + optimistic refresh after submission.
4. Add simple tests (model + API create/list) to lock the contract.
5. (Optional) Add uniqueness constraint draft (request_id, operator_id) in a follow-up migration if duplicates become a concern.

### 18.6 Open Technical Questions (Carried Forward)

- Should we retroactively create a baseline squashed migration once drift is conclusively resolved?
- Do we need soft-delete or status enumeration for human decisions before audit exports?

---
_End-of-Day Addendum Recorded – Ready to resume implementation tomorrow._

### Task Completion Log (Rolling)

#### A3 – Prediction Version Auto-Resolve (2025-09-27)
Implemented new prediction page `ui/pages/4_Prediction.py`:
- Allows blank version field; auto-resolves via `/models/{model}/latest` then falls back to versions list selecting highest numeric.
- Captures client-side latency (ms) excluding SHAP processing using monotonic timer.
- Displays resolved version, prediction, confidence, and raw response expander.
- Optional SHAP section shown only when requested & present.
Verification:
- Blank version resolves correctly when endpoint responds.
- Latency metric surfaces and remains <1.5s without explainability (local env expectation).
- Failure path (unresolvable model) surfaces user-friendly message.
Next Dependencies:
- Integrate error guidance layer (B2) for richer failure hints.
- Centralize latency logging with ingestion (B4) once ingestion closed loop implemented.

#### A4 – Ingestion Closed Loop Latency (2025-09-27)
Implemented enhanced latency instrumentation in `ui/streamlit_app.py` ingestion form:

- Added precise timing using `time.perf_counter()` for POST, verification GET, and end-to-end.
- Success message now surfaces: POST ms, Verify ms, E2E ms for operator feedback & performance baselining.
- Added fallback warning if verification returns empty (eventual consistency note).
Verification:
- Manual submission produced realistic sub-500 ms POST locally; verify call latency displayed separately.
- Empty verification path message confirmed when sensor read not yet indexed.
Next Steps:
- Feed these latency metrics eventually into a lightweight local log or metrics panel (B4).

#### A5 – Decision Audit UI Completion (2025-09-27)
Enhancements applied to `ui/pages/2_decision_log.py`:
- Added filter controls: operator_id, request_id, correlation_id, start/end date.
- Added page size selector & refresh/reset controls.
- Added CSV export for the current page.
- Introduced tabs separating Human Decisions and future Maintenance Logs.
- Improved pagination buttons and correlation_id visibility.
Verification:
- Filter combinations return expected subsets (manual spot checks).
- Pagination & offset reset operate correctly.
- Exported CSV opens with correct UTF-8 header row.
Future Work:
- Integrate maintenance logs when backend endpoint finalized.
- Add tests covering filters & pagination (see Human decisions API tests task).

#### Model Metadata Explorer UI (2025-09-27)
Added `ui/pages/5_Model_Metadata.py` providing:
- Cached (5m) listing of registered models.
- Per-model version inspection with manual load trigger to avoid over-fetching.
- Tag visualization (model vs version tags) in expandable section.
- Human-readable timestamp normalization.
Verification:
- Cache refresh button clears and reloads models.
- Version load only triggers on explicit button (prevents wasteful queries).
Next Steps:
- Integrate error guidance (B2) for cases where endpoints unavailable.
- Add latency timing + caching validation test harness.

#### B2 – Error Guidance Layer (2025-09-27)
Implemented pattern-based error hinting in `ui/lib/api_client.py`:
- Added `_ERROR_PATTERNS` mapping substrings to human-readable remediation tips.
- Added `map_error_to_hint` and `format_error_with_hint` utilities for UI integration.
Usage Recommendation:
- Wrap calls: `resp = format_error_with_hint(make_api_request(...))` in pages needing hints.
Verification:
- Simulated 404 and validation errors produce contextual hints.
Future Work:
- Integrate automatically inside `make_api_request` (opt-in toggle) if pervasive adoption desired.

