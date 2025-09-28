# Prioritized Product Backlog (Truth-Aligned for Minimal V1.0 Release in 5 Days)

Last Synchronized: 2025-09-28
Status: Scope Frozen – Only feasibility‑proven UI integrations remain in V1.0. All amplification work explicitly Deferred → V1.5.

## 1. Scope Freeze Statement (Supersedes 2025-09-27 Draft)

V1.0 = Deliver a stable UI that truthfully exposes a subset of already stable backend capabilities required to demonstrate the platform’s core value. We are **NOT** attempting feature breadth; we are proving reliability + clarity.

### 1.1 Backend Stable (Already Implemented)
- Ingestion (single event, idempotent)
- Sensor readings retrieval (paginated, filtered)
- Prediction (auto version resolve; latency captured client-side)
- Drift check (KS test)
- Anomaly detection (batch)
- Simulation endpoints (drift/anomaly/normal)
- Golden Path orchestrated demo pipeline (event-driven)
- Human decision persistence + retrieval
- Model registry + version listing (MLflow integration) – can be disabled via env flag
- Metrics (Prometheus snapshot)
- Security (API key)
- Metrics Snapshot (manual/auto refresh; NOT streaming)
- Debug / diagnostics page

### 1.3 Backend Present but NOT Yet UI Exposed (Deferred Beyond V1.0)

- Advanced reporting artifacts (only JSON prototype surfaced)
- Streaming metrics
- Background / async SHAP pipeline
- Bulk ingestion & batch prediction UI
- Maintenance logs viewer (tab placeholder only)
- Model recommendation optimization / virtualization
- Multi-sensor correlation analytics
- Feature lineage / feature store visualization
- Notification history & channel configuration
- Governance & retention policy UI

## 2. V1.0 Deliverables (Tightly Scoped)

| Deliverable | Backend Ready | UI State Now | Action Needed for V1.0 | Effort | Risk | Owner (TBD) |
|-------------|---------------|--------------|------------------------|--------|------|-------------|
| Data Explorer | ✅ | ✅ | Stability only (no change) | XS | Low |  |
| Ingestion Form | ✅ | ✅ | Ensure success/verify latency copy concise | XS | Low |  |
| Prediction | ✅ | ✅ | Completed – actionable error hints surfaced | XS | Low |  |
| Decision Audit | ✅ (Create/List) | ✅ | Completed – scope note added (create/list only) | XS | Low |  |
| Model Metadata | ✅ | ✅ | Completed – badge distinction live | XS | Low |  |
| Simulation Console | ✅ | ✅ | None (cosmetic only) | XS | Low |  |
| Golden Path Demo | ✅ | ✅ | Completed – terminal messaging polished | XS | Low |  |
| Metrics Snapshot | ✅ | ✅ | Completed – Snapshot Only label in UI | XS | Low |  |
| Rerun Stability Layer | ✅ | ✅ | None | XS | Low |  |
| Smoke Script (CLI) | N/A | ✅ | Completed – scripts/smoke_v1.py | S | Low |  |

Everything not listed above is **Deferred**.

## 3. Non-Goals (Explicitly Deferred → V1.5)

| Deferred Capability | Reason | Backend Gap? | Target Release |
|---------------------|--------|--------------|----------------|
| Real-time metrics streaming | Complexity vs value now | Yes (no stream endpoint) | V1.5 |
| Report artifacts (PDF/CSV) | Not critical to prove core value | Yes (persistence) | V1.5 |
| Background SHAP processing | Performance enhancement only | Yes (queue infra) | V1.5 |
| Bulk ingestion & batch prediction | Scale efficiency, not MVP | Yes (endpoints) | V1.5 |
| Multi-sensor correlation analytics | Advanced analytics tier | Yes | V1.5+ |
| Model recommendations caching/virtualization | Optimization only | Partial | V1.5+ |
| Advanced notifications UI | Non-core | Partial | V1.5+ |
| Feature store visualization & lineage | Advanced MLOps | Yes | V1.5+ |
| Governance & retention policies UI | Low early volume | Partial | V1.5+ |

## 4. Risk Register (V1.0 Scope Only)

| Risk | Impact if Occurs | Likelihood | Mitigation | Residual |
|------|------------------|------------|-----------|----------|
| Late doc drift reintroduced | Inconsistent messaging | Medium | Lock single deferred list (this file) | Low |
| Golden Path intermittent failures | Demo credibility | Medium | Add clearer timeout vs success messaging | Low |
| Misinterpretation of decision CRUD | User expectation mismatch | Medium | Explicit doc note (create/list only) | Low |
| Overrun adding smoke script | Reduced validation | Low | Keep script minimal (exit codes) | Low |

## 5. Acceptance Criteria for V1.0 (Updated)

1. All listed Deliverables table rows meet Action Needed column.
2. No UI page raises unhandled exception on navigation.
3. Golden Path: completes or times out with explicit user-facing reason within 90s.
4. Model Metadata: shows one of (Disabled flag, Empty registry explanation, Table of models, Error banner) – never ambiguous.
5. Decision Audit: successful submission appears in list within same session (no manual reload needed beyond existing form semantics).
6. Metrics Snapshot page clearly labeled “Snapshot Only – Streaming Deferred (V1.5)”.
7. Deferred capabilities appear only in Section 3 and nowhere else as “present”.
8. Smoke script returns exit code 0 for ingestion + prediction + decision + metrics fetch sequence.

## 6. Minimal Smoke Script (Planned Outline)

Pseudo-flow to implement (not yet present):

```bash
python scripts/smoke_v1.py \
  --ingest sensor_A 42.0 \
  --predict model_X '{"feature_1":1.2}' \
  --decision req-123 approved \
  --metrics
```

Success Criteria: All HTTP 2xx, prediction latency printed, decision echoed.

## 7. Post-V1.0 Hardening (V1.1 Candidates – Not In Scope Now)

| Track | Rationale | Example Activities |
|-------|-----------|--------------------|
| Testing | Raise confidence | Integration tests, latency assertions |
| Observability | Better insight | Add p50/p95 derivation offline |
| Reporting | Enable artifacts | Define storage schema, add persistence |
| Golden Path | Deep demo analytics | Step-level latency aggregation |

## 8. Removed Historical Backlog

Historical backlog content was removed (2025-09-28) to eliminate scope ambiguity. Full history available in version control if needed.

---
- Monitor memory usage for streaming endpoints
- Track error rates for new integrations

**User Experience Protection**:
- Feature flag all new capabilities for gradual rollout
- Maintain backward compatibility for existing workflows
- Provide clear migration paths for deprecated features

