# UI Runtime Error Analysis (2025-09-27)

## 1. Summary

During post-fix validation the UI surfaced five categories of runtime errors:

1. AttributeError: `streamlit` has no attribute `experimental_rerun` (multiple pages)
2. ImportError: `record_latency_sample` missing in Simulation Console
3. False negative state on Model Metadata ("No models found") while MLflow disabled
4. (Latent) Potential silent failures if rerun not supported (no user feedback)
5. Lack of centralized rerun abstraction causing code drift vs. redesign blueprint guidance.

These errors disrupted navigation for Decision Log, Golden Path Demo, Model Metadata Explorer, Metrics Overview, and Simulation Console pages.

## 2. Error Inventory & Root Cause Mapping

| # | Page / Component | Raw Error Snippet | Immediate Cause | Deeper Root Cause | Classification |
|---|------------------|-------------------|-----------------|-------------------|----------------|
| 1 | Decision Log (`2_decision_log.py`) | `AttributeError: module 'streamlit' has no attribute 'experimental_rerun'` | Direct call to deprecated/removed API in running image build | Local file earlier patched but container still used cached layer or code duplication; lack of centralized helper | Breakage / API drift |
| 2 | Golden Path Demo (`3_Golden_Path_Demo.py`) | Same as above | Same pattern | Same; inconsistent redeploy sequence | Breakage / API drift |
| 3 | Model Metadata (`5_Model_Metadata.py`) | Same as above | Refresh button invoked removed API | Page-level shim recreated duplication risk | Breakage / API drift |
| 4 | Metrics Overview (`6_Metrics_Overview.py`) | Same as above | Auto-refresh loop used removed API | Inconsistent Streamlit version vs design assumptions | Breakage / API drift |
| 5 | Simulation Console (`7_Simulation_Console.py`) | `ImportError: cannot import name 'record_latency_sample'` | Function was added in source but container running older revision / name mismatch | Missing compatibility fallback | Missing symbol / backward compatibility |
| 6 | Model Metadata (behavior) | Displays "No models found" when MLflow disabled | Guard present but user expectation unclear | Need explicit cause vs empty state differentiation | UX clarity gap |

## 3. Cross-Reference With Redesign Docs

| Issue | SYSTEM_CAPABILITIES_AND_UI_REDESIGN.md Section | ui_redesign_changelog.md Section | Alignment Gap |
|-------|----------------------------------------------|----------------------------------|---------------|
| Rerun API instability | Sections 3 & 8 (Performance & UX guidelines) – call for modular resilience | Sections 4 & 5 emphasize centralized API client & resilience | Helper not centralized across pages initially |
| Simulation latency recording import | Section 8 (Observability) | Section 5 (Resilience & Observability Enhancements) | Wrapper existed but page imported stale symbol without fallback |
| Model Metadata empty state | Capability Inventory (ML Model Management) | Changelog Model Metadata Explorer entry | Lacked explicit disabled-state messaging vs. absence of models |

## 4. Root Cause Themes

- API Evolution Drift: Streamlit version removed `experimental_rerun`, pages retained explicit calls.
- Decentralized Shims: Multiple per-page `_safe_rerun` functions increased patch surface & risk.
- Deployment Cache Invalidation: Container likely served older code during early testing; reinforcing need for single import location.
- Missing Defensive Imports: Lack of try/except fallback around optional utilities (latency recorder) led to hard crash instead of degraded observability.
- UX Ambiguity: Empty model list indistinguishable from disabled MLflow configuration without cause-specific messaging.

## 5. Remediation Actions Implemented

| Action | File(s) | Description | Status |
|--------|---------|-------------|--------|
| Introduced centralized rerun utility | `ui/lib/rerun.py` | Adds `safe_rerun()` with graceful no-op fallback | Done |
| Refactored pages to use central helper | `2_decision_log.py`, `3_Golden_Path_Demo.py`, `5_Model_Metadata.py`, `6_Metrics_Overview.py` | Removed local `_safe_rerun` definitions | Done |
| Added latency recorder fallback | `7_Simulation_Console.py` | Wrapped import in try/except; added no-op fallback | Done |
| Added environment flag messaging (prior) | `5_Model_Metadata.py` | Clarifies disabled MLflow scenario | Done |
| Established error analysis doc | `UI_ERROR_ANALYSIS_2025-09-27.md` | Canonical trace & mapping | Done |

## 6. Remaining Gaps / Follow-Up

| Gap | Proposed Action | Priority |
|-----|-----------------|----------|
| Need proactive health/rerun capability badge | Add small indicator when rerun not supported | Low |
| Model Metadata: differentiate disabled vs empty | Add explicit badge + disabled state rationale | Medium |
| Simulation Console: show latency summary table reuse | Render recent latency registry subset | Medium |
| Automated regression tests (UI-level) | Add smoke test script invoking pages via `streamlit run` headless + HTTP health checks | Medium |
| Central import contract docs | Add section in developer docs referencing `lib.rerun.safe_rerun` | Low |

## 7. Verification Plan

1. Rebuild UI container: `docker compose build ui && docker compose restart ui`.
2. Manually navigate each affected page; confirm no AttributeError or ImportError.
3. Trigger Golden Path demo; observe auto-refresh functioning via `safe_rerun`.
4. Trigger Simulation runs; confirm no crash and latency entries recorded (if backend responses succeed).
5. Toggle MLflow disable flag and observe correct informational message.

## 8. Acceptance Criteria for Fix Closure

- Zero occurrences of direct `st.experimental_rerun` in `ui/pages/` (verified via grep).
- Simulation Console loads without import errors and records at least one latency entry per simulation.
- Model Metadata Explorer: Disabled message shown only when env flag set; otherwise shows either models or meaningful empty state.
- Golden Path Demo: Auto-refresh cycles without raising exceptions until completion or failure state.

## 9. Risk Assessment Post-Fix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Future Streamlit API removal of `rerun` | Medium | Medium | Central helper now isolates change |
| Latency recorder API rename again | Low | Low | Try/except fallback defends |
| User confusion on empty model list | Medium | Low | Add improved message (planned) |

## 10. Next Incremental Enhancements (Optional for V1.0)

- Add unified toast / banner when running in degraded (no-rerun) environment.
- Add metrics to count auto-refresh cycles for Golden Path & Metrics pages.
- Provide a tiny backend endpoint to validate available models when MLflow disabled (could list last-known cache).

---
Document Owner: Automated Engineering Assistant  
Timestamp: 2025-09-27T00:00:00Z
