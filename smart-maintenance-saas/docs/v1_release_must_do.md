# v1.0 Release Must-Do Checklist

These action items consolidate the high-priority fixes we must finish before tagging the UI for v1.0. Items are drawn from `docs/latest_system_audit_1.md` and `docs/latest_system_audit_2.md`, with deployment/env work deferred to the VM rollout phase.

| Priority | Area | Task | Acceptance Criteria | Source |
|----------|------|------|---------------------|--------|
| High | ML Services | Audit the `DISABLE_MLFLOW_MODEL_LOADING` flag usage across `apps/ml/model_utils.py`, `apps/ml/model_loader.py`, `apps/api/routers/ml_endpoints.py`, and dependent services to ensure offline mode never raises when MLflow is unavailable. Add regression tests covering both enabled and disabled paths. | Flag respected for every MLflow call; new tests pass in both modes. | latest_system_audit_2.md §ML Components |
| High | API Layer | Standardize error response payloads (especially in `apps/api/routers/ml_endpoints.py` and `apps/api/routers/demo.py`) so all failures return FastAPI `HTTPException` style `{"detail": ...}` objects. Update Streamlit hint handling only if changes break compatibility. | Manual calls and automated tests confirm consistent JSON error envelopes. | latest_system_audit_2.md §API Layer |
| Medium | Event Bus | Add integration tests for the retry/DLQ behavior in `core/events/event_bus.py`, including scenarios where handlers fail repeatedly. | Tests cover success, retry, and DLQ cases; flake-free in CI. | latest_system_audit_2.md §Event Bus |
| Medium | ML Versioning | Write targeted tests for the "auto" model version resolution logic to prevent regressions when UI requests omit explicit versions. | Tests demonstrate correct fallback selection and error paths. | latest_system_audit_2.md §ML Components |
| Medium | UI Performance | Cache the Data Explorer sensor list fetch (`ui/pages/1_data_explorer.py`) with a reasonable TTL so repeated visits do not trigger avoidable latency. | Page reloads reuse cached data; cache invalidation verified after TTL expires. | latest_system_audit_2.md §UI Layer |

Once these are complete, rerun the smoke workflow (forecast → schedule → reporting) to verify a clean pass before deployment prep.
