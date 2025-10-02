# Smart Maintenance SaaS - V1.0 Unified Deployment Checklist

**Version:** 1.0  
**Last Updated:** 2025-10-02  
**Status:** 🟡 Pre-Production - Ready for Final Steps  
**Next Milestone:** VM Deployment for Final Delivery

---

## 📋 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Validation Status](#2-validation-status)
3. [System Capabilities Matrix](#3-system-capabilities-matrix)
4. [Critical Pre-Deployment Tasks](#4-critical-pre-deployment-tasks)
5. [Deployment Procedures](#5-deployment-procedures)
6. [Post-Deployment Validation](#6-post-deployment-validation)
7. [Known Issues & Resolutions](#7-known-issues--resolutions)
8. [Deferred Scope (V1.5+)](#8-deferred-scope-v15)
9. [Sign-Off & Release](#9-sign-off--release)

---

## 1. Executive Summary

### 1.1 Current Status

**All backend services are operational and passing automated smoke tests. All 10 UI pages have been validated as fully functional. The system is production-ready pending final internationalization and deployment automation.**

| Dimension | Status | Readiness |
|-----------|--------|-----------|
| Backend Capabilities | ✅ Production-Ready | 100% |
| UI Pages Validation | ✅ Complete (10/10) | 100% |
| Critical Workflows | ✅ Validated | 100% |
| Performance Benchmarks | ✅ Within Targets | 100% |
| Documentation | ✅ Current | 100% |
| Internationalization | 🟡 Framework Ready | 0% (Pending) |
| Deployment Automation | 🟡 Planned | 0% (Pending) |
| Production .env | 🟡 Template Ready | 0% (Pending) |

### 1.2 V1.0 Scope Definition

**Core Principle:** V1.0 delivers a stable, minimal UI exposing proven backend capabilities for demonstration to Brazilian company evaluators. Advanced features are explicitly deferred to V1.5+.

**Included:**
- ✅ Complete data ingestion pipeline (manual + API)
- ✅ Real-time prediction with maintenance scheduling
- ✅ Multi-agent event-driven architecture (12 agents)
- ✅ Drift/anomaly detection with simulations
- ✅ Decision audit log with human-in-the-loop
- ✅ Model registry integration (MLflow)
- ✅ Golden Path Demo (end-to-end workflow)
- ✅ Metrics snapshot and reporting prototype
- ✅ Brazilian Portuguese translations (framework ready)

**Explicitly Deferred to V1.5+:**
- ❌ Streaming metrics dashboard
- ❌ Report artifact downloads (PDF/CSV)
- ❌ Background SHAP processing
- ❌ Bulk ingestion UI
- ❌ Advanced correlation analytics
- ❌ Feature lineage visualization
- ❌ Governance policy UI

### 1.3 Timeline to Production

| Phase | Tasks | Effort | Status |
|-------|-------|--------|--------|
| **Phase 1: Internationalization** | Portuguese tooltips for all 10 pages | 4-6h | 🟡 Next |
| **Phase 2: Backend Finalization** | API keys, ML fallback, .env setup | 6-9h | 🟡 Pending |
| **Phase 3: Deployment Automation** | VM script, smoke tests, rollback docs | 3-4h | 🟡 Pending |
| **Phase 4: VM Deployment** | Execute deployment, external validation | 2-3h | 🟡 Pending |
| **Phase 5: Production Monitoring** | Monitoring baseline, final docs | 2-3h | 🟡 Pending |

**Total Estimated Effort:** 17-25 hours  
**Recommended Start:** Phase 1 (highest user impact)

---

## 2. Validation Status

### 2.1 Backend Validation Results (✅ COMPLETE - 2025-10-02)

#### Container Health (6/6 Services Running)
```
smart_maintenance_api       - Up (healthy) - Port 8000
smart_maintenance_ui        - Up (healthy) - Port 8501
smart_maintenance_db        - Up (healthy) - Port 5433
smart_maintenance_redis     - Up (healthy) - Port 6379
smart_maintenance_mlflow    - Up (healthy) - Port 5000
smart_maintenance_toxiproxy - Up           - Port 8474
```

#### Automated Smoke Test Results
```json
{
  "ingest": {
    "status": "warn",
    "latency_ms": 4.0,
    "note": "Eventual consistency - expected behavior"
  },
  "prediction": {
    "status": "ok",
    "latency_ms": 719.4,
    "model_version": "1"
  },
  "decision": {
    "status": "ok",
    "latency_ms": 1110.2
  },
  "metrics": {
    "status": "ok",
    "latency_ms": 2.3
  },
  "overall": "pass"
}
```

#### API Endpoint Validation
- ✅ `/health` - 200 OK (<100ms)
- ✅ `/health/db` - Connected
- ✅ `/health/redis` - Connected
- ✅ `/api/v1/data/ingest` - Event published (4ms)
- ✅ `/api/v1/ml/predict` - Prediction working (719ms, auto version)
- ✅ `/api/v1/decisions/submit` - Decision recorded (1110ms)
- ✅ `/metrics` - Prometheus metrics available (2.3ms)
- ✅ `/api/v1/sensors/readings` - Data retrieval working
- ✅ `/api/v1/demo/golden-path` - Demo starts successfully

#### Performance Benchmarks
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Prediction Latency | <2000ms | 719ms | ✅ Excellent |
| Decision Write | <5000ms | 1110ms | ✅ Good |
| Health Check | <500ms | <100ms | ✅ Excellent |
| Metrics Endpoint | <1000ms | 2.3ms | ✅ Excellent |
| Golden Path Demo | <90s | 64.4s | ✅ Excellent |
| Simulation API | N/A | 3ms | ✅ Excellent |

### 2.2 UI Validation Results (✅ COMPLETE - 2025-10-02)

#### All Pages Operational (10/10)

| Page | Status | Validation Details |
|------|--------|-------------------|
| **1. Manual Sensor Ingestion** | ✅ 100% | Form submission, verification, latency display. Renamed from "streamlit app". |
| **2. Data Explorer** | ✅ 100% | Pagination, filters, CSV export, sensor dropdown, date ranges all functional. |
| **3. Decision Log** | ✅ 100% | Create/list/filter/CSV export working. Create/list scope confirmed. |
| **4. Golden Path Demo** | ✅ 100% | 64.4s completion, all 7 stages working, human decision stage functional. |
| **5. Prediction** | ✅ 100% | **Critical fixes applied:** Maintenance order creation working (2s, full schedule). |
| **6. Model Metadata** | ✅ 100% | Model list, disabled/enabled badges, expandable details all operational. |
| **7. Simulation Console** | ✅ 100% | All 3 tabs (drift/anomaly/normal) working, 3ms latency, correlation IDs validated. |
| **8. Metrics Overview** | ✅ 100% | Snapshot display, auto/manual refresh, "Snapshot Only" label present. |
| **9. Reporting Prototype** | ✅ 100% | JSON generation, prettified downloads, chart previews, maintenance feed. |
| **10. Debug** | ✅ 100% | Connectivity checks, health endpoints, latency samples, config inspection. |

#### Critical Workflow Validations

**Golden Path Demo (✅ VALIDATED)**
```
Duration: 64.4 seconds (target: <90s)
Stages: 7/7 completed
Events Generated: 68
Human Decision Stage: ✅ Working
Correlation ID: Tracked throughout
```

**Prediction → Maintenance Order (✅ VALIDATED)**
```
Forecast Generation: ✅ Success
Maintenance Order Creation: ✅ Success (2005ms)
Schedule Details Displayed: ✅ Full JSON response
Assigned Technician: tech_002
Scheduled Start: 2025-10-03T08:00:00Z
Optimization Score: 0.85
```

**Simulation Console (✅ VALIDATED)**
```
Drift Simulation: ✅ 50 events, 3ms, correlation ID validated
Anomaly Simulation: ✅ 50 events (10 anomalies), 3ms, correlation ID validated
Normal Simulation: ✅ 100 events over 60 mins, 3ms, correlation ID validated
```

### 2.3 Critical Fixes Applied (2025-10-02)

#### Fix #1: Prediction Page - DateTime Timezone Mismatch
**Issue:** Maintenance order creation timing out after 20s with timezone comparison errors.

**Root Cause:** Comparing offset-naive `datetime.utcnow()` with offset-aware datetime objects in `scheduling_agent.py`.

**Resolution:**
- Changed all `datetime.utcnow()` → `datetime.now(timezone.utc)`
- Added `timezone` to imports
- **Files Modified:** `apps/agents/decision/scheduling_agent.py` (lines 9, 265-267)

**Result:** Timezone comparison errors eliminated.

#### Fix #2: Prediction Page - Past Deadline Logic
**Issue:** After timezone fix, still timing out with "No available slot found for technician tech_002".

**Root Cause:** Historical forecast data with past deadlines (Sept 16) causing invalid scheduling windows where `preferred_time_window_end < preferred_time_window_start`.

**Resolution:**
- Added past deadline detection: `if predicted_failure_date < now:`
- Implemented 7-day future window fallback for demo scenarios
- Added validation: `if preferred_deadline < preferred_start:` extend deadline
- **Files Modified:** `apps/agents/decision/scheduling_agent.py` (lines 201-225)

**Result:** Historical forecasts now schedule in next 7 days, real-time predictions use actual dates. Maintenance orders complete successfully in ~2s.

#### Fix #3: Homepage Title
**Issue:** Sidebar showing generic "streamlit app" instead of descriptive name.

**Resolution:**
- Changed page_title from "Smart Maintenance SaaS" to "Manual Sensor Ingestion"
- Changed icon from 🔧 to 📡
- **Files Modified:** `ui/streamlit_app.py` (line 15)

**Result:** Clear, descriptive sidebar navigation.

---

## 3. System Capabilities Matrix

### 3.1 Backend Capabilities (Production-Ready)

| Capability | Status | Implementation | Notes |
|------------|--------|----------------|-------|
| **Data Ingestion** | ✅ Stable | Redis idempotency guard, correlation support | Eventual consistency expected |
| **Sensor Read Retrieval** | ✅ Stable | Pagination, filtering, indexed queries | Cached sensor list (TTL) |
| **Prediction (Auto Version)** | ✅ Stable | MLflow version resolution, latency capture | Guard for disabled MLflow |
| **Drift Detection** | ✅ Stable | KS-test implementation | Event-driven |
| **Anomaly Detection** | ✅ Stable | Batch IsolationForest + statistical fallback | Serverless-ready |
| **Simulation Endpoints** | ✅ Stable | Drift/anomaly/normal payload generation | Correlation ID tracked |
| **Golden Path Orchestration** | ✅ Stable | Event-driven pipeline, timeout protection | 90s SLA |
| **Human Decision Audit** | ✅ Stable | Create/list API, decision log persistence | No edit/delete in V1.0 |
| **Model Registry** | ✅ Stable | MLflow integration, disabled flag respected | Offline mode available |
| **Model Recommendations** | ✅ Stable | Sensor-type normalization, defensive fallbacks | |
| **Reporting (JSON)** | ✅ Prototype | JSON-only report surface | No artifacts in V1.0 |
| **Metrics (Prometheus)** | ✅ Stable | Snapshot endpoint | No streaming in V1.0 |
| **Security (API Key)** | ✅ Stable | Rate limiting, key validation | Multi-key refinement pending |
| **Redis Coordination** | ✅ Stable | Configurable pool, startup guards, retry logic | |
| **Observability** | ✅ Stable | Structured logging, latency registry, correlation IDs | |
| **Scheduling Agent** | ✅ Stable | Maintenance task scheduling, timezone-aware | Fixed 2025-10-02 |

### 3.2 Multi-Agent Architecture (12 Agents)

| Agent | Purpose | Status | Notes |
|-------|---------|--------|-------|
| **ValidationAgent** | Schema validation, data quality | ✅ Active | |
| **PredictionAgent** | ML inference orchestration | ✅ Active | |
| **AnomalyDetectionAgent** | Anomaly detection with fallback | ✅ Active | |
| **DriftDetectionAgent** | Distribution drift detection | ✅ Active | |
| **SchedulingAgent** | Maintenance task scheduling | ✅ Active | Fixed 2025-10-02 |
| **NotificationAgent** | Alert distribution | ✅ Active | Slack optional |
| **ReportingAgent** | Report generation | ✅ Active | JSON prototype |
| **LearningAgent** | Knowledge base management | ✅ Active | ChromaDB optional |
| **DataIngestionAgent** | Sensor data persistence | ✅ Active | |
| **MetricsCollectorAgent** | Observability metrics | ✅ Active | |
| **DecisionAuditAgent** | Human decision tracking | ✅ Active | |
| **OrchestratorAgent** | Workflow coordination | ✅ Active | Golden Path |

### 3.3 UI Capabilities Mapping

| Backend Capability | UI Exposure | Coverage | V1.0 Status |
|-------------------|-------------|----------|-------------|
| Data Ingestion | ✅ Exposed | Manual form + verification | ✅ Validated |
| Sensor Readings | ✅ Exposed | Data Explorer (full CRUD read) | ✅ Validated |
| Prediction | ✅ Exposed | Forecast + maintenance orders | ✅ Validated |
| Model Metadata | ✅ Exposed | List + status badges | ✅ Validated |
| Drift Detection | ✅ Exposed | Form-based checks | ✅ Validated |
| Anomaly Detection | ✅ Exposed | Form-based checks | ✅ Validated |
| Simulation | ✅ Exposed | 3 simulation types | ✅ Validated |
| Golden Path | ✅ Exposed | End-to-end demo | ✅ Validated |
| Decision Log | ✅ Exposed | Create/list/filter/export | ✅ Validated |
| Metrics | ✅ Exposed | Snapshot view | ✅ Validated |
| Reporting | ⚠️ Prototype | JSON generation only | ✅ Validated |
| Streaming Metrics | ❌ Deferred | Not implemented | V1.5+ |
| Artifact Downloads | ❌ Deferred | Not implemented | V1.5+ |
| Background SHAP | ❌ Deferred | Not implemented | V1.5+ |
| Bulk Operations | ❌ Deferred | Not implemented | V1.5+ |
| Feature Lineage | ❌ Deferred | Not implemented | V1.5+ |
| Governance UI | ❌ Deferred | Not implemented | V1.5+ |

---

## 4. Critical Pre-Deployment Tasks

### 4.1 Phase 1: Brazilian Portuguese Internationalization (HIGH PRIORITY)

**Status:** 🟡 Framework Ready - Integration Pending  
**Effort:** 4-6 hours  
**Owner:** Development Team  
**Deadline:** Before VM deployment

#### Requirements
- Add "?" help tooltips to all UI text elements
- Provide Brazilian Portuguese (pt-BR) translations for all content
- Support Brazilian company evaluation requirements

#### Translation Framework Status
- ✅ Framework created: `ui/lib/i18n_translations.py`
- ✅ 175+ text elements translated (EN/PT-BR pairs)
- ✅ Helper functions implemented:
  - `get_translation()` - Retrieve specific translation
  - `help_tooltip()` - Display bilingual help
  - `bilingual_text()` - Combine EN + PT text
- ✅ All 10 pages covered + common UI elements

#### Implementation Approach (Recommended)

**Option A: Tooltip System (Recommended for V1.0)**
```python
# Add to each page:
from lib.i18n_translations import help_tooltip, get_translation

st.title(get_translation("prediction", "title", "en"))
help_tooltip(
    "prediction", 
    "forecast_description",
    "Generate ML-powered failure predictions"
)
```

**Advantages:**
- Quick implementation (4-6h)
- No architectural changes
- Immediate availability
- Preserves existing workflows

**Option B: Full i18n Framework (Post-V1.0)**
- Language selector in sidebar
- Complete UI rewrite with translation keys
- Session state for language preference
- Effort: 16-20 hours

#### Pages Requiring Integration

| Page | Elements | Priority | Status |
|------|----------|----------|--------|
| Manual Sensor Ingestion | ~15 | High | 🟡 Pending |
| Data Explorer | ~20 | High | 🟡 Pending |
| Decision Log | ~15 | High | 🟡 Pending |
| Golden Path Demo | ~25 | High | 🟡 Pending |
| Prediction | ~30 | Critical | 🟡 Pending |
| Model Metadata | ~15 | Medium | 🟡 Pending |
| Simulation Console | ~20 | Medium | 🟡 Pending |
| Metrics Overview | ~10 | Low | 🟡 Pending |
| Reporting Prototype | ~15 | Low | 🟡 Pending |
| Debug | ~10 | Low | 🟡 Pending |

**Total Translation Items:** 175 text elements

#### Acceptance Criteria
- [ ] All 10 pages have Portuguese tooltips
- [ ] Help text displays without UI disruption
- [ ] Translations accurate and professional
- [ ] No performance degradation
- [ ] User can understand all functionality in Portuguese

### 4.2 Phase 2: Backend High-Priority Tasks

**Status:** 🟡 Pending  
**Effort:** 6-9 hours  
**Can Run in Parallel with Phase 1**

| Priority | Task | Acceptance Criteria | Effort | Status |
|----------|------|---------------------|--------|--------|
| **High** | API key validation alignment | Support multiple keys, align FastAPI middleware with UI/test fixtures. Rate limiting tests return 200/429 as expected. | 2-3h | 🟡 Open |
| **High** | ML anomaly fallback with `DISABLE_MLFLOW_MODEL_LOADING=true` | Verify IsolationForest + statistical backup. AnomalyDetectionAgent integration suite green with serverless flag. | 2-3h | 🟡 Open |
| **High** | Populate production `.env` file | All credentials populated and validated against `DEPLOYMENT_SETUP.md`. Health checks succeed with production config. | 1-2h | 🟡 Open |
| **Medium** | ChromaDB production policy | Decide on `DISABLE_CHROMADB` setting. LearningAgent tests pass under chosen configuration. | 1-2h | 🟡 Open |

#### API Key Validation Details
- Current state: Single test key in use
- Required: Multiple key support or documented test key
- Files to update:
  - FastAPI middleware: `apps/api/main.py`
  - UI requests: Search for `x-api-key` usage
  - Test fixtures: `tests/conftest.py`

#### ML Anomaly Fallback Details
- Test with `DISABLE_MLFLOW_MODEL_LOADING=true`
- Verify IsolationForest instantiation
- Confirm statistical backup (z-score) works
- Run integration test suite for AnomalyDetectionAgent

#### Production .env Template
```bash
# Database
DATABASE_URL=postgresql://user:password@timescaledb.cloud:5432/maindb

# Redis
REDIS_URL=redis://user:password@redis.cloud:6379/0

# Security
API_KEY=prod_key_xxxxxxxxxxxxx
SECRET_KEY=jwt_secret_xxxxxxxxxxxxx

# AWS (for MLflow artifacts)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1

# MLflow
MLFLOW_TRACKING_URI=https://mlflow.example.com
# OR for offline mode:
# DISABLE_MLFLOW_MODEL_LOADING=true

# Optional
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
DISABLE_CHROMADB=false

# App Config
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### 4.3 Phase 3: Deployment Automation

**Status:** 🟡 Planned  
**Effort:** 3-4 hours  
**Depends on:** Phase 2 completion

#### Deployment Script Requirements

Create `scripts/deploy_vm.sh` with:

```bash
#!/bin/bash
set -e

echo "🚀 Smart Maintenance SaaS V1.0 Deployment"

# 1. Pre-flight checks
command -v docker >/dev/null 2>&1 || { echo "Docker required"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "Docker Compose required"; exit 1; }

# 2. Validate .env
if [ ! -f .env ]; then
  echo "❌ .env file not found"
  exit 1
fi

# Check required vars
required_vars=("DATABASE_URL" "REDIS_URL" "API_KEY" "SECRET_KEY")
for var in "${required_vars[@]}"; do
  grep -q "^${var}=" .env || { echo "❌ Missing ${var} in .env"; exit 1; }
done

# 3. Build images
echo "📦 Building Docker images..."
docker compose build --no-cache

# 4. Start services
echo "🏃 Starting services..."
docker compose up -d

# 5. Health check loop (max 3 minutes)
echo "🏥 Waiting for services to be healthy..."
max_attempts=36
attempt=0
while [ $attempt -lt $max_attempts ]; do
  if docker compose ps | grep -q "unhealthy"; then
    echo "⏳ Services starting... ($attempt/$max_attempts)"
    sleep 5
    ((attempt++))
  else
    echo "✅ All services healthy"
    break
  fi
done

if [ $attempt -eq $max_attempts ]; then
  echo "❌ Services failed to become healthy"
  docker compose logs --tail=50
  exit 1
fi

# 6. Run smoke tests
echo "🧪 Running smoke tests..."
docker compose exec -T api python scripts/smoke_v1.py

# 7. Capture logs
echo "📋 Capturing deployment logs..."
docker compose logs > deployment_logs_$(date +%Y%m%d_%H%M%S).txt

echo "✅ Deployment complete!"
echo "🌐 UI: http://localhost:8501"
echo "🔧 API: http://localhost:8000"
echo "📊 MLflow: http://localhost:5000"
```

#### Rollback Procedure

Create `scripts/rollback.sh`:

```bash
#!/bin/bash
echo "⚠️  Rolling back deployment..."

# Stop services
docker compose down

# Restore previous version (if using git tags)
git checkout <previous-tag>

# Rebuild and restart
docker compose build
docker compose up -d

echo "✅ Rollback complete"
```

#### Acceptance Criteria
- [ ] `deploy_vm.sh` runs end-to-end on target VM
- [ ] All pre-flight checks execute
- [ ] Health check loop validates services
- [ ] Smoke tests execute and pass
- [ ] Logs captured for review
- [ ] Rollback procedure documented and tested

---

## 5. Deployment Procedures

### 5.1 Pre-Deployment Checklist

#### Environment Preparation
- [ ] `.env` file populated with production credentials
- [ ] All secrets validated (DATABASE_URL, REDIS_URL, API_KEY, etc.)
- [ ] Docker daemon running on target VM
- [ ] Docker Compose v2 installed
- [ ] Adequate disk space (min 10GB free)
- [ ] Network connectivity verified
- [ ] Firewall rules configured (ports 8000, 8501, 5000)

#### Code Preparation
- [ ] All Phase 1-3 tasks completed
- [ ] Git repository on latest commit
- [ ] All tests passing locally
- [ ] Documentation updated
- [ ] V1.0 tag ready to create

#### VM Preparation
- [ ] VM provisioned (recommended: 4 vCPU, 8GB RAM)
- [ ] OS updated (Ubuntu 22.04 LTS recommended)
- [ ] SSH access configured
- [ ] Non-root user with docker permissions
- [ ] Domain/subdomain configured (if applicable)
- [ ] SSL certificate ready (if using HTTPS)

### 5.2 Deployment Execution Steps

#### Step 1: Clone Repository
```bash
ssh user@vm-hostname
cd /opt
sudo git clone <repository-url> smart-maintenance-saas
cd smart-maintenance-saas/smart-maintenance-saas
```

#### Step 2: Configure Environment
```bash
# Copy and edit .env
cp .env_example.txt .env
nano .env  # Populate all production values

# Validate .env
./scripts/validate_env.sh  # Create this if needed
```

#### Step 3: Execute Deployment
```bash
# Make script executable
chmod +x scripts/deploy_vm.sh

# Run deployment
./scripts/deploy_vm.sh
```

#### Step 4: Monitor Deployment
```bash
# Watch logs
docker compose logs -f

# Check service status
docker compose ps

# Verify health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl http://localhost:8000/health/redis
```

#### Step 5: Run Smoke Tests
```bash
# Automated smoke test
docker compose exec api python scripts/smoke_v1.py

# Manual API tests
export API_KEY=$(grep API_KEY .env | cut -d'=' -f2)

# Test ingestion
curl -X POST http://localhost:8000/api/v1/data/ingest \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"sensor_id":"TEST_VM_001","value":25.5,"sensor_type":"temperature","unit":"celsius"}'

# Test prediction
curl -X POST http://localhost:8000/api/v1/ml/predict \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model_name":"ai4i_classifier_randomforest_baseline","model_version":"auto","features":{"Air_temperature_K":298.1,"Process_temperature_K":308.6,"Rotational_speed_rpm":1551,"Torque_Nm":42.8,"Tool_wear_min":108}}'
```

#### Step 6: UI Validation
```bash
# Open browser
http://<vm-ip-or-domain>:8501

# Test all critical pages:
# 1. Manual Sensor Ingestion - submit test reading
# 2. Data Explorer - verify pagination
# 3. Prediction - generate forecast + maintenance order
# 4. Golden Path Demo - run full demo
# 5. Decision Log - submit test decision
```

### 5.3 Deployment Troubleshooting

| Issue | Diagnosis | Resolution |
|-------|-----------|------------|
| Services fail to start | Check logs: `docker compose logs` | Review .env, check port conflicts |
| Database connection fails | Test DATABASE_URL | Verify credentials, network access |
| Redis connection fails | Test REDIS_URL | Verify credentials, firewall rules |
| UI not accessible | Check port 8501 | Verify firewall, check container logs |
| API not accessible | Check port 8000 | Verify firewall, check container logs |
| Smoke tests fail | Check error details | Review specific endpoint errors |
| MLflow errors | Check MLFLOW_TRACKING_URI or disable flag | Set `DISABLE_MLFLOW_MODEL_LOADING=true` |

---

## 6. Post-Deployment Validation

### 6.1 External Validation Checklist

Once deployed to VM with public access:

- [ ] UI accessible via public URL
- [ ] All 10 pages load without errors
- [ ] Golden Path Demo completes successfully
- [ ] Prediction → Maintenance Order workflow works
- [ ] Data Explorer displays readings
- [ ] Decision Log records submissions
- [ ] Simulation Console runs all 3 simulation types
- [ ] Health endpoints respond to external requests
- [ ] API responds with correct authentication
- [ ] SSL/TLS certificates valid (if HTTPS configured)

### 6.2 Performance Validation

- [ ] Prediction latency <2s
- [ ] Golden Path completes <90s
- [ ] Health checks respond <500ms
- [ ] UI page loads <3s
- [ ] No memory leaks (monitor over 30 minutes)
- [ ] No CPU spikes during idle

### 6.3 Security Validation

- [ ] API key authentication enforced
- [ ] Invalid API keys return 401
- [ ] Rate limiting functional (if enabled)
- [ ] No secrets in logs
- [ ] No secrets in error messages
- [ ] HTTPS enforced (if configured)
- [ ] Input validation working

### 6.4 Monitoring Setup

- [ ] Prometheus metrics accessible: `/metrics`
- [ ] Log aggregation working
- [ ] Disk space monitoring configured
- [ ] Container restart policy validated
- [ ] Backup strategy documented
- [ ] Alert channels configured (optional)

---

## 7. Known Issues & Resolutions

### 7.1 Resolved Issues

| Date | Issue | Severity | Resolution | Status |
|------|-------|----------|------------|--------|
| 2025-10-02 | Prediction page maintenance order timeout (timezone) | Critical | Changed `datetime.utcnow()` → `datetime.now(timezone.utc)` in scheduling_agent.py | ✅ Resolved |
| 2025-10-02 | Prediction page "no available slot" error | Critical | Added past deadline detection with 7-day future window fallback | ✅ Resolved |
| 2025-10-02 | Homepage sidebar shows "streamlit app" | Minor | Changed page_title to "Manual Sensor Ingestion" | ✅ Resolved |
| 2025-09-30 | Golden Path timeout with human decision stage | High | Auto decision injector mirrors orchestrator request IDs | ✅ Resolved |
| 2025-09-30 | Simulation Console TypeError on sensor_id | Medium | Fixed sensor_id binding in payload builder | ✅ Resolved |
| 2025-09-30 | Reporting JSON export unreadable | Low | Prettified JSON downloads with chart previews | ✅ Resolved |

### 7.2 Known Limitations (Non-Blocking)

| Limitation | Impact | Workaround | Future Plan |
|------------|--------|------------|-------------|
| Ingestion verification lag | Smoke test shows "warn" status | Expected - eventual consistency | Document as designed behavior |
| Missing SLACK_WEBHOOK_URL | Warning in logs | Optional feature | Configure if Slack integration needed |
| Reporting prototype (JSON only) | No PDF/CSV artifacts | Prototype scope | V1.5+ artifact storage |
| Metrics snapshot only | No streaming dashboard | Snapshot refresh | V1.5+ streaming implementation |
| Decision Log (create/list only) | No edit/delete UI | V1.0 scope limitation | V1.5+ CRUD expansion |

### 7.3 Open Issues (To Address Before Production)

| Priority | Issue | Impact | Target Resolution |
|----------|-------|--------|-------------------|
| High | API key multi-key support | Testing friction | Phase 2 |
| High | ML fallback validation with DISABLE_MLFLOW_MODEL_LOADING | Deployment flexibility | Phase 2 |
| Medium | ChromaDB production policy | Optional feature config | Phase 2 |

---

## 8. Deferred Scope (V1.5+)

The following capabilities are explicitly out-of-scope for V1.0 and documented for future releases:

### 8.1 UI Features (Deferred)
- ❌ Streaming metrics dashboard with real-time updates
- ❌ Report artifact downloads (PDF/CSV generation)
- ❌ Background SHAP processing with job queue
- ❌ Bulk ingestion UI for batch uploads
- ❌ Maintenance log viewer enhancements
- ❌ Advanced notifications UI
- ❌ Language selector with full i18n framework
- ❌ Edit/delete capabilities in Decision Log
- ❌ Model recommendation caching/virtualization
- ❌ Interactive feature lineage visualization
- ❌ Governance and retention policy UI

### 8.2 Backend Features (Deferred)
- ❌ Multi-sensor correlation analytics
- ❌ Advanced model recommendation optimization
- ❌ Report artifact storage layer
- ❌ WebSocket support for streaming
- ❌ Job queue infrastructure (Celery/RQ)
- ❌ Advanced caching layers
- ❌ Multi-tenancy support

### 8.3 Infrastructure (Deferred)
- ❌ Kubernetes deployment manifests
- ❌ Multi-stage Docker builds (optimization)
- ❌ Advanced monitoring dashboards (Grafana)
- ❌ Automated backup/restore procedures
- ❌ Blue-green deployment automation
- ❌ Load balancer configuration
- ❌ CDN integration

---

## 9. Sign-Off & Release

### 9.1 Pre-Release Checklist

- [ ] All Phase 1-4 tasks completed
- [ ] All validation checkboxes marked
- [ ] All known issues resolved or documented
- [ ] Deployment tested on clean VM
- [ ] External smoke tests passing
- [ ] Documentation reviewed and current
- [ ] Brazilian Portuguese translations implemented
- [ ] Production .env configured
- [ ] Backup/rollback procedures documented
- [ ] Monitoring baseline established

### 9.2 Release Approval

| Role | Name | Approval | Date |
|------|------|----------|------|
| Lead Developer | Yan Cotta | ⬜ Pending | |
| QA Validation | | ⬜ Pending | |
| DevOps/Deployment | | ⬜ Pending | |
| Product Owner | | ⬜ Pending | |

### 9.3 Release Artifacts

Once approved, create:

- [ ] Git tag: `v1.0.0`
- [ ] Release notes documenting:
  - All validated features
  - Known limitations
  - Deployment instructions
  - Brazilian Portuguese support
- [ ] Docker images tagged with `v1.0.0`
- [ ] Deployment logs archived
- [ ] Performance baseline documented
- [ ] Monitoring screenshots captured

### 9.4 Post-Release Actions

- [ ] Create V1.5 planning document
- [ ] Schedule retrospective meeting
- [ ] Archive V1.0 deployment logs
- [ ] Update public documentation
- [ ] Announce release to stakeholders
- [ ] Begin monitoring production metrics
- [ ] Schedule first production backup

---

## 📚 Related Documentation

- **Architecture:** [SYSTEM_AND_ARCHITECTURE.md](./SYSTEM_AND_ARCHITECTURE.md) - Complete system architecture with diagrams
- **Deployment Guide:** [DEPLOYMENT_SETUP.md](./DEPLOYMENT_SETUP.md) - Environment configuration details
- **API Documentation:** [api.md](./api.md) - REST API endpoints and examples
- **UI Changelog:** [ui_redesign_changelog.md](./ui_redesign_changelog.md) - UI evolution history
- **Security Guide:** [SECURITY.md](./SECURITY.md) - Security practices and policies
- **Models Summary:** [MODELS_SUMMARY.md](./MODELS_SUMMARY.md) - ML models documentation
- **Executive Summary:** [EXECUTIVE_SUMMARY.md](./EXECUTIVE_SUMMARY.md) - High-level project overview

---

## 📞 Quick Reference

### Essential Commands

```bash
# Start stack
cd smart-maintenance-saas
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f api
docker compose logs -f ui

# Run smoke tests
docker compose exec api python scripts/smoke_v1.py

# Restart services
docker compose restart api ui

# Stop stack
docker compose down

# Full cleanup (WARNING: destroys data)
docker compose down -v
```

### Essential URLs

- **UI:** http://localhost:8501
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health
- **Metrics:** http://localhost:8000/metrics
- **MLflow:** http://localhost:5000

### Support Contacts

- **Technical Issues:** [Create GitHub Issue]
- **Deployment Support:** Yan Cotta
- **Documentation:** See `docs/` directory

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-02  
**Status:** 🟡 Pre-Production - Awaiting Phase 1-4 Completion  
**Next Milestone:** VM Deployment for Brazilian Company Evaluation

---

**END OF UNIFIED DEPLOYMENT CHECKLIST**
