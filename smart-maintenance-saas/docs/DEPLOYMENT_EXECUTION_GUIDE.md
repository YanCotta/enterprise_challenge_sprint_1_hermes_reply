# V1.0 Deployment Execution Guide
**Date:** 2025-10-03  
**Deadline:** Today (24h delivery)  
**Status:** Ready to Deploy ✅

---

## 📋 Pre-Flight Checklist

- ✅ `.env` configured with production keys
- ✅ TimescaleDB Cloud credentials validated
- ✅ Redis Cloud (Render) credentials validated
- ✅ AWS S3 credentials configured
- ✅ Code tested locally (ML fallback, Portuguese UI)
- ⏳ VM provisioning (YOUR NEXT STEP)

---

## 🎯 TASK 1: VM Provisioning (YOU DO THIS - 30 minutes)

### Option A: AWS EC2 (Recommended)

**1. Launch Instance:**
```bash
# Via AWS Console or CLI
Instance Type: t3.medium (2 vCPU, 4GB) or t3.large (2 vCPU, 8GB)
OS: Ubuntu 22.04 LTS
Storage: 30GB SSD
Security Group: Open ports 22, 8000, 8501, 5000
```

**2. Configure Security Group:**
- Port 22: SSH (your IP only)
- Port 8000: API (0.0.0.0/0 - public)
- Port 8501: UI (0.0.0.0/0 - public, if not using Streamlit Cloud)
- Port 5000: MLflow (0.0.0.0/0 - public for experiment tracking)

**3. Connect via SSH:**
```bash
# Download your .pem key, then:
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@YOUR_VM_IP
```

### Option B: Google Cloud VM

```bash
gcloud compute instances create smart-maintenance-vm \
  --machine-type=e2-standard-2 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --tags=http-server,https-server

# Open firewall
gcloud compute firewall-rules create allow-api --allow tcp:8000
gcloud compute firewall-rules create allow-ui --allow tcp:8501
gcloud compute firewall-rules create allow-mlflow --allow tcp:5000
```

### Option C: Azure VM

```bash
az vm create \
  --resource-group smart-maintenance-rg \
  --name smart-maintenance-vm \
  --image Ubuntu2204 \
  --size Standard_B2s \
  --admin-username azureuser \
  --generate-ssh-keys

# Open ports
az vm open-port --port 8000 --resource-group smart-maintenance-rg --name smart-maintenance-vm
az vm open-port --port 8501 --resource-group smart-maintenance-rg --name smart-maintenance-vm
az vm open-port --port 5000 --resource-group smart-maintenance-rg --name smart-maintenance-vm
```

### Option D: DigitalOcean Droplet (Simplest)

1. Go to https://cloud.digitalocean.com/
2. Create Droplet:
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Basic - $12/mo (2 vCPU, 4GB RAM)
   - **Datacenter:** Choose closest to you
   - **Firewall:** Add custom rules for 8000, 8501, 5000
3. Note the IP address

**Once VM is ready, continue to Task 2.**

---

## 🔧 TASK 2: Install Docker on VM (YOU DO THIS - 10 minutes)

**SSH into your VM, then run:**

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (avoid sudo)
sudo usermod -aG docker $USER

# Install Docker Compose v2
sudo apt-get install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version

# You may need to log out and back in for group changes
exit
# Then SSH back in
```

**Expected output:**
```
Docker version 24.0.x
Docker Compose version v2.20.x or higher
```

---

## 📦 TASK 3: Deploy Backend to VM (I'LL HELP - 30 minutes)

**On your VM:**

```bash
# 1. Clone repository
cd /opt
sudo mkdir -p smart-maintenance-saas
sudo chown $USER:$USER smart-maintenance-saas
cd smart-maintenance-saas

# Option A: Clone via HTTPS (if repo is public)
git clone https://github.com/YanCotta/enterprise_challenge_sprint_1_hermes_reply.git .
cd smart-maintenance-saas

# Option B: If repo is private, use SSH or copy files manually
# You can use scp from your local machine:
# scp -r /home/yan/Documents/Git/enterprise_challenge_sprint_1_hermes_reply/smart-maintenance-saas/* ubuntu@VM_IP:/opt/smart-maintenance-saas/

# 2. Copy .env file from your local machine
# On your LOCAL machine, run:
scp /home/yan/Documents/Git/enterprise_challenge_sprint_1_hermes_reply/smart-maintenance-saas/.env ubuntu@YOUR_VM_IP:/opt/smart-maintenance-saas/.env

# Or manually create .env on VM and paste contents
nano .env
# Paste your .env contents, then Ctrl+X, Y, Enter

# 3. Verify .env is present
cat .env | grep API_KEY
# Should show: API_KEY=9K5jDmlKIag0ME7Io_nadv7tYrZtLxwpfyaxHYRFTIQ5Hc36LBJcjn4Nbxa6IO4T

# 4. Build containers (this takes 5-10 minutes)
docker compose build --no-cache

# 5. Start services
docker compose up -d

# 6. Wait 30 seconds for initialization
sleep 30

# 7. Check container health
docker compose ps
# All containers should show "Up (healthy)"

# 8. Check logs for errors
docker compose logs api | tail -50
docker compose logs mlflow | tail -50
```

**Expected output from `docker compose ps`:**
```
NAME                STATUS              PORTS
api                 Up (healthy)        0.0.0.0:8000->8000/tcp
ui                  Up (healthy)        0.0.0.0:8501->8501/tcp
db                  Up (healthy)        5432/tcp
redis               Up (healthy)        6379/tcp
mlflow              Up (healthy)        0.0.0.0:5000->5000/tcp
toxiproxy           Up                  8474/tcp
```

---

## ✅ TASK 4: Backend Validation (I'LL HELP - 15 minutes)

**On your VM, test each endpoint:**

```bash
# Store your API key in environment
export API_KEY="9K5jDmlKIag0ME7Io_nadv7tYrZtLxwpfyaxHYRFTIQ5Hc36LBJcjn4Nbxa6IO4T"

# Test 1: Health check
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"1.0.0",...}

# Test 2: Database health
curl http://localhost:8000/health/db
# Expected: {"status":"healthy","database":"connected",...}

# Test 3: Redis health
curl http://localhost:8000/health/redis
# Expected: {"status":"healthy","redis":"connected",...}

# Test 4: Data ingestion
curl -X POST http://localhost:8000/api/v1/data/ingest \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "DEPLOY_TEST_001",
    "value": 25.5,
    "sensor_type": "temperature",
    "unit": "celsius"
  }'
# Expected: {"message":"Data ingested successfully",...}

# Test 5: ML Prediction (verify MLflow connection)
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
# Expected: {"prediction": [0 or 1],...}
```

**If all 5 tests pass → Backend is DEPLOYED ✅**

**Troubleshooting:**

```bash
# If containers aren't healthy:
docker compose logs api --tail=100
docker compose logs mlflow --tail=100

# Common issues:
# 1. Database connection failed → Check DATABASE_URL in .env
# 2. Redis connection failed → Check REDIS_URL in .env (must be rediss://)
# 3. S3 connection failed → Check AWS credentials in .env

# Restart if needed:
docker compose down
docker compose up -d
```

---

## 🌐 TASK 5: UI Deployment (YOU DO THIS - 20 minutes)

### Option A: Streamlit Cloud (RECOMMENDED - Free & Easy)

**1. Push to GitHub (if not already done):**
```bash
# On your LOCAL machine
cd /home/yan/Documents/Git/enterprise_challenge_sprint_1_hermes_reply
git add .
git commit -m "Production deployment - ready for V1.0"
git push origin main
```

**2. Deploy on Streamlit Cloud:**
- Go to https://share.streamlit.io/
- Click "New app"
- Select your repository: `YanCotta/enterprise_challenge_sprint_1_hermes_reply`
- Main file path: `smart-maintenance-saas/ui/streamlit_app.py`
- Click "Advanced settings" → "Secrets"

**3. Add Secrets (in TOML format):**
```toml
[default]
API_BASE_URL = "http://YOUR_VM_IP:8000"
API_KEY = "9K5jDmlKIag0ME7Io_nadv7tYrZtLxwpfyaxHYRFTIQ5Hc36LBJcjn4Nbxa6IO4T"
CLOUD_MODE = "true"
DEPLOYMENT_ENV = "production"
```

**4. Deploy!**
- Click "Deploy"
- Wait 2-3 minutes for build
- Note your URL: `https://your-app.streamlit.app`

**5. Test:**
- Open the URL
- Homepage should load with Portuguese tooltips
- Click "?" icons → should see Portuguese descriptions

### Option B: VM Deployment (if Streamlit Cloud unavailable)

**Your UI is already running on the VM at `http://YOUR_VM_IP:8501`**

Just update the `.env` on VM to use internal Docker network:

```bash
# On VM:
cd /opt/smart-maintenance-saas
nano .env

# Change this line:
API_BASE_URL=http://api:8000

# Save and restart UI:
docker compose restart ui

# Test:
curl http://localhost:8501
# Should return HTML content
```

Then access via browser: `http://YOUR_VM_IP:8501`

---

## 🧪 TASK 6: End-to-End Validation (YOU DO THIS - 20 minutes)

**Open your deployed UI (Streamlit Cloud or VM) and test:**

### Journey 1: Manual Sensor Ingestion (2 min)
1. Click "Manual Sensor Ingestion" in sidebar
2. Click "?" tooltip → **Verify Portuguese description visible** ✅
3. Fill form:
   - Sensor ID: `E2E_TEST_001`
   - Value: `25.0`
   - Sensor Type: `temperature`
   - Unit: `celsius`
4. Click "Ingest Reading"
5. **Verify:** Success message shows latency metrics

### Journey 2: Data Explorer (2 min)
1. Click "Data Explorer" in sidebar
2. **Verify:** Pagination shows total readings
3. **Verify:** Can see `E2E_TEST_001` reading in table
4. Test sensor filter dropdown
5. Click "?" tooltips → **Verify Portuguese translations** ✅

### Journey 3: Prediction + Maintenance Order (3 min)
1. Click "Prediction" in sidebar
2. Click "?" tooltips → **Verify Portuguese help text** ✅
3. Use model: `ai4i_classifier_randomforest_baseline`
4. Click "Generate Forecast"
5. **Verify:** Forecast appears in ~2 seconds
6. Click "Create Maintenance Order"
7. **Verify:** Maintenance schedule appears with technician assignment

### Journey 4: Golden Path Demo (3 min)
1. Click "Golden Path Demo" in sidebar
2. Click "?" tooltip → **Verify Portuguese + timeout warning** ✅
3. Set sensor events: `10`
4. Click "Start Golden Path Demo"
5. **Verify:** Progress bar updates through 7 stages
6. **Verify:** Completion in 30-60 seconds
7. **Verify:** Summary shows all stages completed

### Journey 5: Decision Log (2 min)
1. Click "Decision Log" in sidebar
2. Submit test decision:
   - Request ID: `REQ_E2E_001`
   - Operator: `OP_TEST`
3. Click "?" tooltips → **Verify Portuguese scope note** ✅
4. **Verify:** Decision appears in list below
5. Click "Export CSV"
6. **Verify:** CSV downloads successfully

### ✅ Success Criteria:
- [ ] All 5 journeys complete without errors
- [ ] Portuguese tooltips (?) visible on all pages
- [ ] Data flows: Ingest → Store → Retrieve
- [ ] Predictions return in <3 seconds
- [ ] Golden Path completes in <90 seconds
- [ ] No 500 errors in browser console

**If all checks pass → V1.0 IS DEPLOYED! 🎉**

---

## 📊 Post-Deployment Checklist

Once validation passes:

1. **Document URLs:**
   ```
   API: http://YOUR_VM_IP:8000
   UI: https://your-app.streamlit.app (or http://YOUR_VM_IP:8501)
   MLflow: http://YOUR_VM_IP:5000
   ```

2. **Share with stakeholders:**
   - UI URL for testing
   - API documentation: `http://YOUR_VM_IP:8000/docs`
   - MLflow dashboard for experiment tracking

3. **Monitor first 24 hours:**
   ```bash
   # On VM:
   docker compose logs -f api
   docker compose logs -f mlflow
   
   # Check resource usage:
   docker stats
   ```

4. **Create V1.5 backlog** (from 24H_DEPLOYMENT_CRITICAL_PATH.md):
   - Multi-key API auth
   - SSL/HTTPS setup
   - Custom domain
   - Monitoring dashboard
   - Backup procedures

---

## 🆘 Troubleshooting

### Issue: Containers not healthy
```bash
docker compose logs api --tail=100
# Check for database connection errors
# Verify .env credentials match cloud services
```

### Issue: UI can't reach API
```bash
# If using Streamlit Cloud:
# - Verify API_BASE_URL uses public IP (not localhost)
# - Verify port 8000 is open in VM firewall
# - Test: curl http://YOUR_VM_IP:8000/health from your local machine

# If using VM UI:
# - Verify API_BASE_URL=http://api:8000 (Docker network)
```

### Issue: MLflow can't load models
```bash
# Check S3 connection:
docker compose exec api python3 -c "import boto3; print(boto3.client('s3').list_buckets())"

# If fails, verify AWS credentials in .env
# Alternative: Enable DISABLE_MLFLOW_MODEL_LOADING=true in .env (ML fallback mode)
```

### Issue: Database connection timeout
```bash
# Test from VM:
apt-get install -y postgresql-client
psql "postgresql://tsdbadmin:y6t6ba5hh0ivs0wv@jz07aq1uaz.tchf3tc6vd.tsdb.cloud.timescale.com:37776/tsdb?sslmode=require"

# If connection fails:
# - Check TimescaleDB Cloud firewall (allow VM IP)
# - Verify credentials haven't expired
```

---

## 🎯 Next Steps After Deployment

1. **Celebrate!** 🎉 You deployed a production AI system in 24 hours
2. **Gather feedback** from evaluators/stakeholders
3. **Monitor performance** for 24-48 hours
4. **Plan V1.5** with deferred features (SSL, monitoring, etc.)
5. **Document lessons learned** for future deployments

---

**Created:** 2025-10-03  
**Deployment Status:** IN PROGRESS  
**Next Action:** YOU provision VM (Task 1)
