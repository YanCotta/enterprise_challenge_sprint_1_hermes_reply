# 24-Hour Deployment Critical Path
**Created:** 2025-10-02  
**Deadline:** 2025-10-03 (24 hours)  
**Objective:** Deploy functional V1.0 with Brazilian Portuguese support

---

## 🚨 EXECUTIVE SUMMARY

**Current Status:** System is 90% deployment-ready. Backend validated, UI operational with Portuguese translations, ML fallback working.

**Critical Path:** Focus on deployment execution, not feature development. System works—we need to get it online.

**Time Allocation:**
- **0-8h (MUST-DO):** Deployment blockers only — 6 items
- **8-16h (STRETCH):** Quality improvements — 2 items
- **DEFER to V1.5:** Everything else — 8+ items

---

## 🎯 TIER 1: MUST-DO (0-8 hours) - DEPLOYMENT BLOCKERS

These are the ONLY tasks that block a functional deployed system.

### 1. VM Provisioning & Setup (2 hours) ✅ ESSENTIAL
**Priority:** P0 (Can't deploy without a VM)

**Tasks:**
- [ ] Provision VM (4 vCPU, 8GB RAM, Ubuntu 22.04)
- [ ] Configure SSH access
- [ ] Install Docker + Docker Compose v2
- [ ] Open ports: 8000 (API), 8501 (UI), 5000 (MLflow)
- [ ] Configure firewall rules

**Acceptance:** Can SSH into VM, Docker running.

---

### 2. Production .env Configuration (1 hour) ⚠️ CRITICAL
**Priority:** P0 (System won't start without credentials)

**Tasks:**
- [ ] Copy `.env_example.txt` to `.env`
- [ ] Fill in REQUIRED credentials:
  ```bash
  DATABASE_URL=postgresql+asyncpg://...  # TimescaleDB Cloud
  REDIS_URL=rediss://...                 # Redis Cloud
  AWS_ACCESS_KEY_ID=...                  # S3 access
  AWS_SECRET_ACCESS_KEY=...              # S3 secret
  MLFLOW_BACKEND_STORE_URI=...           # TimescaleDB connection
  MLFLOW_ARTIFACT_ROOT=s3://...          # S3 bucket
  API_KEY=...                            # Generate secure key
  SECRET_KEY=...                         # Generate secure key
  ```
- [ ] Verify all required variables present
- [ ] Test DATABASE_URL connectivity from VM

**Acceptance:** `.env` file complete, database reachable.

**Note:** Brazilian Portuguese translations already working—no additional config needed!

---

### 3. Backend Deployment (2 hours) ✅ CORE
**Priority:** P0 (No backend = no functionality)

**Tasks:**
- [ ] Clone repository to VM: `/opt/smart-maintenance-saas`
- [ ] Copy `.env` to `smart-maintenance-saas/` directory
- [ ] Build containers: `docker compose build --no-cache`
- [ ] Start services: `docker compose up -d`
- [ ] Wait for health checks (max 3 minutes)
- [ ] Verify all 6 containers healthy:
  ```bash
  docker compose ps
  # api, ui, db, redis, mlflow, toxiproxy all "Up (healthy)"
  ```

**Acceptance:** All containers running, health endpoints return 200.

---

### 4. Backend Validation (1 hour) ✅ VERIFICATION
**Priority:** P0 (Confirm backend works before deploying UI)

**Tasks:**
- [ ] Test health endpoints:
  ```bash
  curl http://localhost:8000/health
  curl http://localhost:8000/health/db
  curl http://localhost:8000/health/redis
  ```
- [ ] Test data ingestion:
  ```bash
  export API_KEY=$(grep API_KEY .env | cut -d'=' -f2)
  curl -X POST http://localhost:8000/api/v1/data/ingest \
    -H "x-api-key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"sensor_id":"VM_TEST_001","value":25.5,"sensor_type":"temperature","unit":"celsius"}'
  ```
- [ ] Test prediction endpoint (verify MLflow connection):
  ```bash
  curl -X POST http://localhost:8000/api/v1/ml/predict \
    -H "x-api-key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"model_name":"ai4i_classifier_randomforest_baseline","model_version":"auto","features":{"Air_temperature_K":298.1,"Process_temperature_K":308.6,"Rotational_speed_rpm":1551,"Torque_Nm":42.8,"Tool_wear_min":108}}'
  ```

**Acceptance:** All endpoints return 200/201, data persists in TimescaleDB.

---

### 5. UI Deployment - Streamlit Cloud (1 hour) 🌐 RECOMMENDED
**Priority:** P0 (UI is how evaluators access the system)

**Option A: Streamlit Cloud (RECOMMENDED - Simplest)**

**Tasks:**
- [ ] Push code to GitHub (already done if on `last_developments_to_v1` branch)
- [ ] Go to https://share.streamlit.io/
- [ ] Connect repository
- [ ] Select `smart-maintenance-saas/ui/streamlit_app.py` as main file
- [ ] Configure secrets in Streamlit Cloud dashboard:
  ```toml
  [default]
  API_BASE_URL = "http://YOUR_VM_IP:8000"
  API_KEY = "same_as_backend_api_key"
  CLOUD_MODE = "true"
  DEPLOYMENT_ENV = "production"
  ```
- [ ] Deploy

**Acceptance:** UI loads at https://your-app.streamlit.app, can see homepage with Portuguese tooltips.

**Option B: VM Deployment (if Streamlit Cloud not available)**
- UI already running on VM at http://VM_IP:8501
- Update `.env` to set `API_BASE_URL=http://api:8000` (Docker network)
- Restart: `docker compose restart ui`

---

### 6. End-to-End Validation (1 hour) ✅ FINAL CHECK
**Priority:** P0 (Prove system works for evaluators)

**Critical User Journeys to Test:**

**Journey 1: Data Ingestion (1 min)**
- [ ] Open UI → Manual Sensor Ingestion page
- [ ] Click "?" tooltip → Verify Portuguese description visible
- [ ] Submit test reading (sensor_id: DEMO_001, value: 25.0)
- [ ] Verify success message with latency metrics

**Journey 2: Data Explorer (1 min)**
- [ ] Navigate to Data Explorer page
- [ ] Verify pagination works, see DEMO_001 reading
- [ ] Test sensor filter dropdown
- [ ] Click "?" tooltips → Verify Portuguese translations

**Journey 3: Prediction + Maintenance Order (2 min)**
- [ ] Navigate to Prediction page
- [ ] Click "?" tooltips → Verify Portuguese help text
- [ ] Use model: `ai4i_classifier_randomforest_baseline`
- [ ] Click "Generate Forecast"
- [ ] Verify forecast appears (~2s)
- [ ] Click "Create Maintenance Order"
- [ ] Verify maintenance schedule displayed with technician assignment

**Journey 4: Golden Path Demo (2 min)**
- [ ] Navigate to Golden Path Demo
- [ ] Click "?" tooltip → Verify Portuguese description + timeout warning
- [ ] Set sensor events: 10
- [ ] Click "Start Golden Path Demo"
- [ ] Wait for completion (~30-60s for 10 events)
- [ ] Verify all 7 stages complete

**Journey 5: Decision Log (1 min)**
- [ ] Navigate to Decision Log
- [ ] Submit test decision (request_id: REQ_001, operator: OP_001)
- [ ] Click "?" tooltips → Verify Portuguese scope note
- [ ] Verify decision appears in list below
- [ ] Test CSV export

**Acceptance:** All 5 journeys complete without errors. Portuguese tooltips visible throughout.

---

## 🎯 TIER 2: SHOULD-DO (8-16 hours) - QUALITY IMPROVEMENTS

These improve the deployment but aren't blockers. Do IF time permits after Tier 1 complete.

### 7. Deployment Automation Script (2 hours) 📜 NICE-TO-HAVE
**Priority:** P1 (Makes future deployments easier, but not required for V1.0)

**Tasks:**
- [ ] Create `scripts/deploy_vm.sh` with:
  - Pre-flight checks (Docker installed, .env exists)
  - Automated build + start
  - Health check loop (max 3 min)
  - Smoke test execution
  - Log capture

**Acceptance:** Script runs end-to-end without manual intervention.

**Defer Rationale:** Manual deployment works. Script nice for future but not required for first delivery.

---

### 8. Production Monitoring Baseline (2 hours) 📊 NICE-TO-HAVE
**Priority:** P1 (Helps post-deployment, but system works without it)

**Tasks:**
- [ ] Document expected metrics baseline:
  - Ingestion latency: <500ms
  - Prediction latency: <2s
  - Golden Path duration: <90s
  - Memory usage per container
- [ ] Set up basic Prometheus scraping (optional)
- [ ] Configure alerts for container health

**Acceptance:** Metrics baseline documented, basic monitoring in place.

**Defer Rationale:** System is self-monitoring via /metrics endpoint. Advanced monitoring post-V1.0.

---

## ⏭️ TIER 3: DEFER TO V1.5 (16+ hours)

These are explicitly out of scope for 24-hour delivery. Move to V1.5 backlog.

### Deferred Items (8+ items)

| Item | Reason | V1.5 Priority |
|------|--------|---------------|
| API key multi-key support | Single key works for demo | Medium |
| ChromaDB production policy | LearningAgent optional, system works without | Low |
| Streaming metrics dashboard | Snapshot endpoint sufficient | Medium |
| Report artifact downloads | JSON prototype adequate | Medium |
| Background SHAP processing | Explainability not critical for V1.0 | Low |
| Bulk ingestion UI | Manual ingestion sufficient | Medium |
| Advanced correlation analytics | Not required for demo | Low |
| Feature lineage visualization | Not required for demo | Low |
| Governance policy UI | Not required for demo | Low |
| SSL/HTTPS setup | HTTP works for initial demo | High (security) |
| Domain name configuration | IP address works for demo | Medium |
| Backup/restore procedures | Post-production concern | High (ops) |

---

## ⏱️ TIME ALLOCATION RECOMMENDATION

**Hours 0-2: VM Setup**
- Provision VM
- Install dependencies
- Open ports

**Hours 2-3: .env Configuration**
- Gather credentials
- Fill .env template
- Test connectivity

**Hours 3-5: Backend Deployment**
- Clone repo
- Build containers
- Start services

**Hours 5-6: Backend Validation**
- Test health endpoints
- Test ingestion
- Test prediction

**Hours 6-7: UI Deployment**
- Streamlit Cloud setup
- Configure secrets
- Deploy UI

**Hours 7-8: End-to-End Validation**
- Test all 5 critical journeys
- Verify Portuguese tooltips
- Document any issues

**Hours 8-10: (OPTIONAL) Automation Script**
- Only if Tier 1 complete ahead of schedule

**Hours 10-12: (OPTIONAL) Monitoring Setup**
- Only if Tier 1 and automation complete

---

## ✅ SUCCESS CRITERIA

**Minimum Viable Deployment (MUST HAVE):**
- ✅ Backend deployed and healthy on VM
- ✅ UI accessible via public URL (Streamlit Cloud or VM)
- ✅ All 10 pages load without errors
- ✅ Portuguese tooltips (?) visible on all pages
- ✅ Data ingestion → storage → retrieval working
- ✅ Prediction + maintenance order creation working
- ✅ Golden Path Demo completes successfully
- ✅ Decision log create/list working

**Stretch Goals (NICE TO HAVE):**
- ⭐ Deployment script working
- ⭐ Monitoring baseline documented
- ⭐ SSL certificate configured

---

## 🚫 OUT OF SCOPE (EXPLICIT DEFERRALS)

The following are **NOT** required for V1.0 delivery:

- Multi-key API authentication
- ChromaDB decision
- Streaming metrics
- Artifact downloads (PDF/CSV)
- SHAP background processing
- Bulk operations
- Advanced analytics
- Feature lineage
- Governance UI
- SSL/HTTPS (can use HTTP for demo)
- Custom domain (IP address works)
- Load testing
- Backup procedures
- CI/CD pipeline

---

## 📋 DEPLOYMENT CHECKLIST (PRINT THIS)

```
TIER 1 - MUST DO (0-8h):
[ ] 1. VM provisioned and configured (2h)
[ ] 2. .env file complete with credentials (1h)
[ ] 3. Backend deployed, all containers healthy (2h)
[ ] 4. Backend endpoints validated (1h)
[ ] 5. UI deployed on Streamlit Cloud (1h)
[ ] 6. End-to-end validation - 5 journeys (1h)

TIER 2 - SHOULD DO (8-16h):
[ ] 7. Deployment automation script (2h) - OPTIONAL
[ ] 8. Monitoring baseline documented (2h) - OPTIONAL

TIER 3 - DEFER TO V1.5:
[ ] Move 12+ items to V1.5 backlog
```

---

## 🎓 LESSONS LEARNED (PRE-MORTEM)

**What Could Go Wrong:**

1. **TimescaleDB connection fails** → Test DATABASE_URL early, verify firewall
2. **Redis connection fails** → Verify REDIS_URL format (rediss:// with SSL)
3. **S3 credentials invalid** → Test AWS credentials before MLflow startup
4. **Streamlit Cloud limits** → Have VM deployment as backup plan
5. **Portuguese tooltips not showing** → Already tested and working, no risk
6. **Golden Path timeout** → 90s guard in place, tested and working
7. **Maintenance order fails** → Already fixed timezone bugs, tested and working

**Mitigation Strategy:**
- Test each component incrementally
- Have fallback plans (VM UI if Streamlit Cloud fails)
- Use DISABLE_MLFLOW_MODEL_LOADING=true if MLflow issues (already tested)
- Document issues immediately for V1.5

---

## 🎯 FINAL RECOMMENDATION

**DO THIS:**
1. Complete Tier 1 (6 items, 8 hours)
2. Validate thoroughly (all 5 journeys)
3. Document any issues for V1.5

**DON'T DO THIS:**
1. Try to add features
2. Fix non-critical bugs
3. Optimize performance
4. Add tests
5. Refactor code

**The system works. Deploy it. Ship it. Celebrate. 🚀**

---

_Created 2025-10-02 — Deploy by 2025-10-03 deadline_
