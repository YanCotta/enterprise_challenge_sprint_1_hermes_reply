# Prioritized Product Backlog (Re-scoped for Minimal V1.0)

## Scope Decision (2025-09-27)

V1.0 will ship as a **Minimum Working UI** delivering only core operational value:

1. Data ingestion & sensor readings explorer
2. ML prediction (auto version resolve + latency feedback)
3. Model metadata basic explorer (cached)
4. Drift & anomaly on-demand analysis
5. Golden Path demo (instrumented; timeout protected)
6. Decision audit log (filters + CSV export)
7. Reporting (JSON only – no artifact persistence yet)
8. Metrics snapshot + latency registry (no streaming)
9. Simulation console (drift / anomaly / normal seeding)

All “plus” features (streaming metrics, artifact downloads, background SHAP, bulk ingestion, correlation analytics, governance, advanced notifications, feature lineage, model recommendations optimization) are **explicitly deferred to V1.5+**.

## V1.0 Must-Haves (Implemented – Only Light Polish Allowed)

| Area | Status | Remaining Polish | Notes |
|------|--------|------------------|-------|
| Ingestion + Explorer | ✅ | Optional CSV export | Core stable |
| Prediction | ✅ | UI surface error hints (already backend) | SHAP async deferred |
| Model Metadata | ✅ | Visual badge for disabled vs empty | Recommendations deferred |
| Drift / Anomaly | ✅ | Historical aggregation later | — |
| Simulation Console | ✅ | Optional latency table summary | Functionally complete |
| Golden Path Demo | ✅ | Add retention TTL doc note | Streaming later |
| Decision Log | ✅ | Maintenance logs tab future | Human decisions working |
| Reporting (JSON) | ✅ Prototype | Artifact storage deferred | Minimal UI retained |
| Metrics Snapshot | ✅ | Percentiles / error rate later | Streaming deferred |
| Rerun Stability Layer | ✅ | None | Central helper in place |

## V1.0 Quality Enablers (If Time Allows Before Tag)

| Item | Benefit | Effort | Priority |
|------|---------|--------|----------|
| Smoke tests: ingestion/prediction/decision/simulation/demo | Regression safety | S | HIGH |
| Model metadata empty vs disabled styling | Operator clarity | XS | HIGH |
| Latency p50/p95 computation | Better insight | S | MEDIUM |
| Golden Path completed run TTL note | Ops clarity | XS | MEDIUM |

## Deferred to V1.5 (Plus Feature Wave)

| Feature | Reason for Deferral | Original Priority | Target |
|---------|---------------------|-------------------|--------|
| Real-time metrics streaming | Non-blocking; complexity | P1 | V1.5 |
| Report artifact generation & download | Complexity; JSON adequate early | P1 | V1.5 |
| Background SHAP processing | Performance enhancer | P2 | V1.5 |
| Bulk ingestion & batch prediction | Scale efficiency | P2 | V1.5 |
| Multi-sensor correlation analytics | Advanced analytics | P3 | V1.5+ |
| Model recommendations caching/virtualization | Optimization | P3 | V1.5+ |
| Advanced notifications UI | Non-core | P4 | V1.5+ |
| Feature store visualization & lineage | Advanced MLOps | P4 | V1.5+ |
| Governance & retention policies | Low early volume | P4 | V1.5+ |

## Post-V1.0 (V1.1 Hardening Focus)

| Track | Actions |
|-------|---------|
| Testing | Add integration tests + CI gate |
| Observability | Add percentiles & error rate extraction |
| Reporting | Design artifact storage contract (directory layout, naming, retention) |
| Golden Path | Step-level metrics; structured completion summary persisted |

## Success Criteria for V1.0 Tag

1. All Must-Have areas load without runtime errors
2. Prediction latency (no SHAP) p95 <1.5s local/container baseline
3. Ingestion verify round-trip typical <1s
4. Golden Path either completes or times out with user message ≤90s
5. Decision log submission + retrieval + CSV export function
6. Model metadata clearly distinguishes: disabled / empty / error / populated
7. Smoke test suite (even minimal) executes successfully locally

## Archived Original Backlog (Historical Reference)

(Unmodified content below retained for traceability.)

---

### 1. Real-time Metrics Streaming Dashboard
 
**Problem**: Current metrics display is snapshot-based with manual refresh, limiting operational visibility.

**Proposed Solution**:

- Implement WebSocket/SSE endpoint for live metric updates
- Add auto-refresh toggle with 5s/15s/30s intervals
- Provide delta highlighting for changed values

**Effort**: Medium (3-5 days)
**Risk if Deferred**: Medium - Operators may miss critical system state changes
**Dependencies**: None - can implement incrementally

**Implementation Notes**:
```python
# Add streaming endpoint in apps/api/routers/metrics.py  
@router.websocket("/metrics/stream")
async def stream_metrics(websocket: WebSocket):
    # Send periodic metric updates
    
# Update ui/pages/6_Metrics_Overview.py with WebSocket client
```

### 2. Report Artifact Generation and Download

**Problem**: Reports generate JSON output but lack persistent storage and downloadable artifacts.

**Proposed Solution**:
- Add file storage backend (local filesystem or S3)
- Implement PDF generation for comprehensive reports
- Add download endpoints with proper MIME types

**Effort**: Medium (2-3 days)
**Risk if Deferred**: High - Essential for audit compliance and operational handoffs
**Dependencies**: File storage configuration

**Implementation Notes**:
```python
# Enhance apps/api/routers/reporting.py
@router.get("/download/{report_id}")
async def download_report(report_id: str):
    return FileResponse(path=report_path, media_type="application/pdf")
```

## Priority 2: High (Plan for V1.1 Release)

### 3. Enhanced Test Coverage for Core Workflows  

**Problem**: Limited automated test coverage for critical user paths.

**Proposed Solution**:
- Add integration tests for ingestion → retrieval round-trip
- Validate prediction auto-resolve with various model versions
- Test decision log filtering, pagination, and CSV export
- Simulate golden path orchestration with timeout scenarios

**Effort**: Small (1-2 days)  
**Risk if Deferred**: Medium - Potential regression introduction during future changes
**Dependencies**: Test environment with mock MLflow registry

### 4. Background SHAP Processing Pipeline

**Problem**: SHAP explanations can take 30+ seconds, blocking UI interaction.

**Proposed Solution**:
- Implement async job queue (Celery/Redis or FastAPI BackgroundTasks)
- Add job status polling endpoint
- Cache SHAP results with model version keys  
- Provide progress indicator in UI

**Effort**: Large (5-7 days)
**Risk if Deferred**: Low - SHAP is optional feature, users can disable it
**Dependencies**: Job queue infrastructure, result caching strategy

### 5. Bulk Data Operations Enhancement

**Problem**: Only single-record ingestion supported; no bulk import/export capabilities.

**Proposed Solution**:
- Add CSV upload endpoint with chunked processing
- Implement batch prediction API for multiple readings
- Provide progress tracking for long-running bulk operations
- Add export capabilities for large datasets

**Effort**: Medium (3-4 days)
**Risk if Deferred**: Medium - Limits operational efficiency for large-scale data management
**Dependencies**: File upload handling, progress tracking UI components

## Priority 3: Medium (V1.2+ Enhancement Candidates)

### 6. Advanced Multi-Sensor Correlation Analytics

**Problem**: Current analysis focuses on single sensors; complex equipment needs multi-sensor insights.

**Proposed Solution**:
- Add cross-sensor correlation matrix visualization
- Implement composite anomaly scoring across sensor groups
- Provide equipment-level health dashboards
- Add predictive failure modeling with multiple input sources

**Effort**: Large (7-10 days)
**Risk if Deferred**: Low - Single-sensor analysis covers primary use cases
**Dependencies**: Enhanced data model, visualization libraries

### 7. Model Recommendations Caching and Virtualization

**Problem**: Model recommendation queries have latency issues; UI enumeration not optimized.

**Proposed Solution**:
- Implement intelligent caching layer for model recommendations
- Add UI virtualization for large model lists
- Provide model performance comparison tools
- Add automated A/B testing framework for model selection

**Effort**: Medium (4-5 days)
**Risk if Deferred**: Low - Current model selection works for existing model count
**Dependencies**: Enhanced MLflow metadata extraction

## Priority 4: Low (Nice-to-Have Features)

### 8. Advanced Notification System UI

**Problem**: Alert agents exist in backend but no UI for viewing/configuring notifications.

**Proposed Solution**:
- Add notification history viewer
- Implement channel configuration (email, Slack, webhook)
- Provide alert rule management interface
- Add notification test/preview capabilities

**Effort**: Medium (3-4 days)
**Risk if Deferred**: Very Low - Backend alerts function without UI
**Dependencies**: Notification channel integrations

### 9. Feature Store Visualization and Lineage

**Problem**: No visibility into model feature lineage, drift correlation displays.

**Proposed Solution**:
- Add feature importance visualization
- Implement feature drift tracking over time
- Provide model lineage graphs
- Add feature store health monitoring

**Effort**: Large (6-8 days)
**Risk if Deferred**: Very Low - Advanced MLOps capability beyond core requirements  
**Dependencies**: Enhanced MLflow integration, graph visualization components

### 10. Governance and Retention Policies
**Problem**: No lifecycle policies for generated reports, model artifacts, or historical data.

**Proposed Solution**:
- Add configurable data retention policies
- Implement automatic artifact cleanup
- Provide data archival and restoration capabilities
- Add compliance reporting for data governance

**Effort**: Medium (4-5 days)
**Risk if Deferred**: Very Low - Manual cleanup sufficient for initial operations
**Dependencies**: Storage management framework, compliance requirements definition

## Resource Allocation Recommendations

**For V1.0 Immediate Polish (if resources available)**:
1. Real-time Metrics Streaming (Priority 1.1) - High user visibility impact
2. Report Download Capability (Priority 1.2) - Essential for operational handoffs

**For V1.1 Planning**:
1. Enhanced Test Coverage (Priority 2.3) - Foundation for stable development
2. Background SHAP Processing (Priority 2.4) - Performance improvement  
3. Bulk Data Operations (Priority 2.5) - Operational efficiency

**For V1.2+ Roadmap**:
- Advanced analytics and correlation features
- Enhanced MLOps tooling and visualization
- Governance and compliance automation

## Success Metrics for Backlog Items

| Item | Success Metric | Target |
|------|---------------|--------|
| Streaming Metrics | Dashboard update latency | <5s real-time updates |
| Report Downloads | Artifact generation time | <30s for standard reports |
| Test Coverage | Automated test success rate | >95% pass rate |  
| SHAP Processing | UI responsiveness | <2s prediction without SHAP blocking |
| Bulk Operations | Processing throughput | 1000+ records/minute |

## Risk Mitigation Strategy

**Technical Debt Prevention**:
- Maintain test coverage above 80% for new features
- Document all architectural decisions in ADRs
- Regular dependency updates and security scanning

**Performance Monitoring**:
- Set up alerts for response time degradation
- Monitor memory usage for streaming endpoints
- Track error rates for new integrations

**User Experience Protection**:
- Feature flag all new capabilities for gradual rollout
- Maintain backward compatibility for existing workflows
- Provide clear migration paths for deprecated features