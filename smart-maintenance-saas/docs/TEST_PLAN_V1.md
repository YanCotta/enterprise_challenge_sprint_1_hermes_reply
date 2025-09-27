# Minimal Test Plan for V1.0 Release

## Test Coverage Goals
This document outlines minimal automated test coverage for critical system flows to validate V1.0 readiness.

## Core Test Categories

### 1. API Health & Connectivity
- `/health` - System health check
- `/api/v1/ml/health` - MLflow connectivity  
- Basic endpoint responsiveness

### 2. Data Ingestion Round-Trip
- `POST /api/v1/data/ingest` - Single sensor reading
- `GET /api/v1/sensors/readings` - Verify data persistence
- Correlation ID tracking

### 3. Prediction Auto-Resolve
- `POST /api/v1/ml/predict` - Prediction with blank version
- Version auto-resolution to latest
- Latency measurement

### 4. Decision Log Workflow
- `POST /api/v1/decisions/submit` - Submit maintenance decision
- `GET /api/v1/decisions` - List decisions with filters
- Pagination and CSV export capability

### 5. Simulation Endpoints
- `POST /api/v1/simulate/drift-event` - Drift simulation
- `POST /api/v1/simulate/anomaly-event` - Anomaly simulation  
- `POST /api/v1/simulate/normal-data` - Normal data simulation
- Correlation tracking and latency recording

### 6. Golden Path Orchestration
- `POST /api/v1/demo/golden-path` - Start demo pipeline
- `GET /api/v1/demo/golden-path/status/{id}` - Poll status
- Timeout handling (90s max)
- Terminal state detection

## Test Implementation Notes

### Fast Test Requirements ( each)
- Use lightweight payloads
- Mock heavy dependencies where appropriate
- Focus on happy path + one edge case per flow

### Critical Validation Points
- No ImportError or AttributeError exceptions
- Proper HTTP status codes (200/201/404/500)
- Response structure validation
- Timeout and error handling

### UI-Level Smoke Tests
- Page load without crashes
- Safe rerun functionality
- Model metadata state differentiation
- Simulation console latency recording

## Success Criteria
- All core workflows covered by at least one test
- No runtime crashes in UI navigation
- API endpoints respond within acceptable timeouts
- Documentation reflects current system capabilities

## Deferred Testing (Post-V1.0)
- Load testing under concurrent users
- Integration with external MLflow registry
- Full end-to-end UI automation
- Performance benchmarking