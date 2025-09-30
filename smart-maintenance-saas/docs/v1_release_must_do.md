# v1.0 Release Must-Do Checklist

These action items consolidate the high-priority fixes we must finish before tagging the UI for v1.0. Items are drawn from `docs/latest_system_audit_1.md` and `docs/latest_system_audit_2.md`, with deployment/env work deferred to the VM rollout phase.

| Priority | Area | Task | Acceptance Criteria | Source |
|----------|------|------|---------------------|--------|
| High | ML Services | Audit the `DISABLE_MLFLOW_MODEL_LOADING` flag usage across `apps/ml/model_utils.py`, `apps/ml/model_loader.py`, `apps/api/routers/ml_endpoints.py`, and dependent services to ensure offline mode never raises when MLflow is unavailable. Add regression tests covering both enabled and disabled paths. | Flag respected for every MLflow call; new tests pass in both modes. | latest_system_audit_2.md §ML Components |
| High | API Layer | Standardize error response payloads (especially in `apps/api/routers/ml_endpoints.py` and `apps/api/routers/demo.py`) so all failures return FastAPI `HTTPException` style `{"detail": ...}` objects. Update Streamlit hint handling only if changes break compatibility. | Manual calls and automated tests confirm consistent JSON error envelopes. | latest_system_audit_2.md §API Layer |
| High | Platform Services | Ensure the FastAPI startup sequence initializes Redis via `core.redis_client.init_redis_client` so demo and ML endpoints no longer crash with “Redis client not initialized” under Docker/cloud settings. Add regression coverage for the health check and teardown path. | Pytest demo flows and `/api/v1/ml` endpoints operate without manual Redis bootstrapping. | Test run 2025-09-30 redis failure |
| High | Security & API | Align API key validation so automated tests and UI clients can reach ML endpoints (allow multiple keys or inject test key). Update shared test fixtures and documentation. | Rate limiting tests pass with expected 200/429 behavior; UI confirms 200 responses. | Test run 2025-09-30 api-key 403 |
| High | Event Bus | Update agent handlers and tests to the new `EventBus.publish(event_obj)` contract and verify DLQ/retry logging with real event objects. | Scheduling, human interface, and anomaly agent integrations publish/consume events without AttributeError; DLQ tests still pass. | Test run 2025-09-30 event bus change |
| High | ML Agents | Restore anomaly detector fallback readiness when serverless mode is active—guarantee `IsolationForest` mocks and statistical paths stay wired, or update tests/settings accordingly. | AnomalyDetectionAgent integration suite green with default serverless settings. | Test run 2025-09-30 anomaly agent |
| Medium | Validation Agent | Provide a dict-like settings adapter (or refactor fixtures) so validation agent tests can mutate configuration again. | `tests/integration/agents/core/test_validation_agent.py` passes without monkey patches. | Test run 2025-09-30 validation agent |
| Medium | UI Layer | Replace deprecated `streamlit.experimental_rerun` usage with the supported `st.rerun()` and refresh related stability tests. | `tests/test_v1_stability.py` passes; manual UI smoke run unaffected. | Test run 2025-09-30 streamlit |
| Medium | ML Versioning | Re-check `_resolve_model_version` fallback path for registry outages so auto mode selects the first loadable version. | `tests/unit/api/test_ml_version_resolution.py` passes with deliberate registry failure. | Test run 2025-09-30 ml versioning |
| Medium | Knowledge Agent | Decide on DISABLE_CHROMADB policy for production vs. tests; update LearningAgent health expectations or re-enable embeddings in Docker. | Learning agent integration suite passes under chosen configuration. | Test run 2025-09-30 learning agent |
| Low | Test Infrastructure | Document/adjust Testcontainers usage so Docker-in-Docker flows succeed (mount Docker socket or skip when unavailable). | Test suites relying on Testcontainers either run or skip cleanly in CI. | Test run 2025-09-30 testcontainers |
| Medium | Event Bus | Add integration tests for the retry/DLQ behavior in `core/events/event_bus.py`, including scenarios where handlers fail repeatedly. | Tests cover success, retry, and DLQ cases; flake-free in CI. | latest_system_audit_2.md §Event Bus |
| Medium | ML Versioning | Write targeted tests for the "auto" model version resolution logic to prevent regressions when UI requests omit explicit versions. | Tests demonstrate correct fallback selection and error paths. | latest_system_audit_2.md §ML Components |
| Medium | UI Performance | Cache the Data Explorer sensor list fetch (`ui/pages/1_data_explorer.py`) with a reasonable TTL so repeated visits do not trigger avoidable latency. | Page reloads reuse cached data; cache invalidation verified after TTL expires. | latest_system_audit_2.md §UI Layer |

Once these are complete, rerun the smoke workflow (forecast → schedule → reporting) to verify a clean pass before deployment prep.

## Completion Tracker

- [x] Hardened the `DISABLE_MLFLOW_MODEL_LOADING` flag across `apps/ml/model_loader.py`, `apps/ml/model_utils.py`, and `apps/api/routers/ml_endpoints.py`, plus regression tests in `tests/unit/ml/test_model_loader_disable.py` and `tests/unit/api/test_ml_version_resolution.py`.
- [x] Added ML version auto-resolution tests and shared helper coverage in `apps/api/routers/ml_endpoints.py` / `tests/unit/api/test_ml_version_resolution.py`.
- [x] Introduced event bus retry and DLQ integration tests in `tests/integration/test_event_bus_retry.py`.
- [x] Cached Data Explorer sensor list fetch via `_fetch_sensor_options()` in `ui/pages/1_data_explorer.py` to cut redundant API calls.
