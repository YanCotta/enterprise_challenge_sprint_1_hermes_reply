# V1.0 Deployment Validation Checklist

**Status:** Pre-Deployment Validation  
**Date:** 2025-10-02  
**Related:** [v1_release_must_do.md](./v1_release_must_do.md) - V1.0 Deployment Playbook

## Pre-Deployment Validation Steps

### 1. Environment Preparation

- [ ] `.env` file populated with production credentials
- [ ] All secrets validated (DATABASE_URL, REDIS_URL, API_KEY, etc.)
- [ ] Docker daemon running
- [ ] Docker Compose v2 installed
- [ ] Adequate disk space (min 10GB free)
- [ ] Network connectivity verified

### 2. Container Health Checks

#### 2.1 Build Services
```bash
cd smart-maintenance-saas
docker compose build --no-cache
```
**Expected:** Clean build with no errors

#### 2.2 Start Stack
```bash
docker compose up -d
```
**Expected:** All services start successfully

#### 2.3 Verify Service Health
```bash
# Check all containers are running
docker compose ps

# Check API health
curl -H "x-api-key: $API_KEY" http://localhost:8000/health

# Check database
curl -H "x-api-key: $API_KEY" http://localhost:8000/health/db

# Check Redis
curl -H "x-api-key: $API_KEY" http://localhost:8000/health/redis

# Check UI is accessible
curl http://localhost:8501
```

**Expected:** All endpoints return 200 OK

### 3. Backend API Smoke Tests

#### 3.1 Run Automated Smoke Test
```bash
# Inside API container
docker compose exec api poetry run python scripts/smoke_v1.py
```

**Expected Results:**
```json
{
  "ingest": {"status": "ok"},
  "prediction": {"status": "ok"},
  "decision": {"status": "ok"},
  "metrics": {"status": "ok"},
  "overall": "pass"
}
```

#### 3.2 Manual API Endpoint Tests

##### Data Ingestion
```bash
curl -X POST http://localhost:8000/api/v1/data/ingest \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "TEST_001",
    "value": 25.5,
    "sensor_type": "temperature",
    "unit": "celsius"
  }'
```
**Expected:** HTTP 200, `{"status": "event_published"}`

##### Prediction (Auto Version)
```bash
curl -X POST http://localhost:8000/api/v1/ml/predict \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "ai4i_classifier_randomforest_baseline",
    "model_version": "auto",
    "features": {
      "Air_temperature_K": 298.1,
      "Process_temperature_K": 308.6,
      "Rotational_speed_rpm": 1551,
      "Torque_Nm": 42.8,
      "Tool_wear_min": 108
    }
  }'
```
**Expected:** HTTP 200, prediction returned with auto-resolved version

##### Decision Submission
```bash
curl -X POST http://localhost:8000/api/v1/decisions/submit \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test_req_001",
    "decision": "approve",
    "justification": "Validation test",
    "operator_id": "test_operator"
  }'
```
**Expected:** HTTP 201, decision recorded

### 4. UI Functional Tests (Manual)

#### 4.1 Core Pages Navigation
- [ ] Home page loads (http://localhost:8501)
- [ ] Data Explorer accessible
- [ ] Decision Log accessible
- [ ] Golden Path Demo accessible
- [ ] Prediction page accessible
- [ ] Model Metadata accessible
- [ ] Simulation Console accessible
- [ ] Metrics Overview accessible
- [ ] Reporting Prototype accessible
- [ ] Debug page accessible

#### 4.2 Data Explorer Page Tests
- [ ] Page loads without errors
- [ ] Sensor dropdown populates
- [ ] Date filters work
- [ ] Pagination functions
- [ ] Data table displays readings
- [ ] CSV export downloads
- [ ] No console errors in browser

#### 4.3 Prediction Page Tests
- [ ] Page loads without errors
- [ ] Sensor type selector works
- [ ] Model dropdown populates
- [ ] Forecast generates successfully
- [ ] Chart displays forecast data
- [ ] Historical context expander works
- [ ] "Create Maintenance Order" button functions
- [ ] Confirmation stays visible after scheduling
- [ ] Latency metrics display

#### 4.4 Golden Path Demo Tests
- [ ] Demo starts successfully
- [ ] Progress indicators update
- [ ] Pipeline steps show status
- [ ] Events tab displays events
- [ ] Metrics tab shows latency
- [ ] Demo completes within 90s
- [ ] With human decision stage: completes successfully
- [ ] Success message displays
- [ ] Correlation ID visible

#### 4.5 Decision Log Tests
- [ ] Page loads without errors
- [ ] Decision submission form works
- [ ] Submitted decisions appear in list
- [ ] Filters function (operator, request_id, dates)
- [ ] Pagination works
- [ ] CSV export downloads
- [ ] Create/list scope acknowledged (no edit/delete)

#### 4.6 Simulation Console Tests
- [ ] All three tabs load (Drift, Anomaly, Normal)
- [ ] Drift simulation executes without errors
- [ ] Anomaly simulation executes
- [ ] Normal simulation executes
- [ ] Each returns correlation ID
- [ ] Latency metrics recorded
- [ ] Recent runs section displays
- [ ] No TypeError on sensor_id binding

#### 4.7 Reporting Prototype Tests
- [ ] Page loads without errors
- [ ] Report types selectable
- [ ] Reports generate successfully
- [ ] JSON preview displays
- [ ] Chart previews render (if available)
- [ ] Download button works
- [ ] JSON is properly formatted
- [ ] Maintenance schedule feed displays

### 5. Integration Tests

#### 5.1 End-to-End Workflow
1. [ ] Ingest sensor data via UI
2. [ ] Verify data appears in Data Explorer
3. [ ] Run prediction on sensor
4. [ ] Create maintenance order from prediction
5. [ ] Verify order appears in reporting feed
6. [ ] Submit human decision
7. [ ] Verify decision in Decision Log

#### 5.2 Golden Path End-to-End
1. [ ] Start Golden Path Demo
2. [ ] Monitor pipeline progression
3. [ ] Verify all stages complete
4. [ ] Check events list is populated
5. [ ] Confirm maintenance scheduled event
6. [ ] Verify metrics captured

### 6. Performance Validation

- [ ] Prediction latency < 2s (without SHAP)
- [ ] Data Explorer loads < 2s
- [ ] Golden Path completes < 90s
- [ ] Ingestion E2E < 5s
- [ ] No memory leaks (stable over 10 min)
- [ ] No CPU spikes during idle

### 7. Error Handling Tests

#### 7.1 API Error Scenarios
- [ ] Invalid API key → 401 Unauthorized
- [ ] Malformed payload → 422 Validation Error
- [ ] Missing required fields → 422
- [ ] Rate limit exceeded → 429 (if tested)
- [ ] Service unavailable → Graceful degradation

#### 7.2 UI Error Scenarios
- [ ] Backend down → Clear error message
- [ ] Empty data sets → Appropriate empty state
- [ ] Invalid inputs → Validation feedback
- [ ] Timeout scenarios → Timeout message
- [ ] Network errors → Retry guidance

### 8. Documentation Verification

- [ ] README.md accurate
- [ ] API docs match endpoints (`/docs`)
- [ ] Deployment guide current
- [ ] UI redesign changelog updated
- [ ] V1 deployment playbook accurate
- [ ] Architecture diagrams match reality

### 9. Security Checks

- [ ] API key authentication enforced
- [ ] HTTPS ready (if applicable)
- [ ] No secrets in logs
- [ ] No secrets in error messages
- [ ] Rate limiting functional (where enabled)
- [ ] Input validation working

### 10. Pre-Deployment Final Checks

- [ ] All containers running
- [ ] No error logs in `docker compose logs`
- [ ] Database migrations applied
- [ ] MLflow accessible (if enabled)
- [ ] Redis connectivity confirmed
- [ ] Disk space adequate
- [ ] Backup strategy documented
- [ ] Rollback plan defined

---

## Post-Deployment Validation

### 1. VM/Cloud Deployment Verification

- [ ] Services accessible via public URL
- [ ] SSL/TLS certificates valid
- [ ] Health endpoints responding
- [ ] Smoke test passes in production
- [ ] UI loads for external users
- [ ] API responds to external requests

### 2. Production Monitoring

- [ ] Prometheus metrics accessible
- [ ] Logs aggregation working
- [ ] Alert channels configured
- [ ] Backup automation verified

---

## Issues Log

| Date | Issue | Severity | Resolution | Status |
|------|-------|----------|------------|--------|
| 2025-10-02 | Initial validation | - | Document created | ✅ |
|  |  |  |  |  |

---

## Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Developer | Yan Cotta | | |
| QA | | | |
| DevOps | | | |

---

**Next Steps After Validation:**
1. Address any failed checks
2. Document all workarounds
3. Update v1_release_must_do.md with outcomes
4. Proceed to VM deployment
5. Run production smoke tests
6. Tag V1.0 release

**Validation Status:** 🟡 IN PROGRESS
