# Smart Maintenance SaaS - Unified Cloud Deployment Guide

**Version:** 1.0  
**Last Updated:** 2025-10-03  
**Status:** Production Ready ✅  
**Deployment Time:** 90-120 minutes

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Pre-Deployment Setup](#pre-deployment-setup)
4. [Quick Reference Card](#quick-reference-card)
5. [Step-by-Step Deployment](#step-by-step-deployment)
6. [Common Errors & Solutions](#common-errors--solutions)
7. [Post-Deployment Validation](#post-deployment-validation)
8. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Overview

This guide provides a complete, battle-tested process for deploying Smart Maintenance SaaS to production cloud infrastructure. It consolidates all deployment documentation and includes solutions for real-world issues encountered during deployment.

**Architecture:**
- **Backend:** FastAPI + Docker on cloud VM (AWS EC2, DigitalOcean, GCP, Azure)
- **Database:** TimescaleDB Cloud (managed PostgreSQL with time-series extension)
- **Cache:** Redis Cloud (Render managed Redis with SSL)
- **ML Storage:** MLflow with TimescaleDB backend + S3 artifacts
- **Frontend:** Streamlit on Streamlit Cloud (free tier)

**Key Features:**
- ✅ Cloud-native architecture (no local volumes)
- ✅ Secure credential management
- ✅ Health checks and dependency management
- ✅ Brazilian Portuguese UI support
- ✅ ML anomaly detection fallback mode

---

## Prerequisites

### Required Accounts & Services

1. **Cloud VM Provider** (choose one):
   - AWS EC2 (recommended)
   - DigitalOcean
   - Google Cloud Platform
   - Microsoft Azure

2. **Database:** TimescaleDB Cloud account with service provisioned
3. **Cache:** Render Redis instance (free tier available)
4. **Storage:** AWS S3 bucket for MLflow artifacts
5. **Frontend:** GitHub account + Streamlit Cloud (free tier)

### Required Credentials

Prepare these credentials before starting:

```bash
# Database (TimescaleDB Cloud)
DATABASE_URL=postgresql+asyncpg://tsdbadmin:PASSWORD@HOST:PORT/tsdb?ssl=require

# Cache (Render Redis)
REDIS_URL=rediss://USERNAME:PASSWORD@HOST:PORT

# MLflow Backend (TimescaleDB Cloud - synchronous driver)
MLFLOW_BACKEND_STORE_URI=postgresql://tsdbadmin:PASSWORD@HOST:PORT/tsdb?sslmode=require

# S3 Artifacts
MLFLOW_ARTIFACT_ROOT=s3://your-bucket-name
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
AWS_DEFAULT_REGION=us-east-2

# API Security (generate secure keys)
API_KEY=<64-char-secure-token>
SECRET_KEY=<64-char-secure-token>
JWT_SECRET=<64-char-secure-token>
```

### Required Tools

On your **local machine**:
- Git
- SSH client
- Text editor (for `.env` configuration)

On your **VM** (will install during deployment):
- Docker Engine v24+
- Docker Compose v2+

---

## Pre-Deployment Setup

**⚠️ CRITICAL:** These steps must be completed BEFORE deploying to your VM. Skipping these will result in a non-functional system.

### Setup 1: Prepare ML Training Datasets (30-60 minutes)

The system requires trained ML models stored in S3. You have two options:


#### Option A: Use Pre-Trained Models (Recommended - 5 minutes)

**Access via DVC (Google Drive):**

1. **Access the shared Google Drive folder**: [Smart Maintenance SaaS - DVC Data](https://drive.google.com/drive/folders/1cJvSRaBG0Fzs4D_wlUeVPM9l47RP_k3G?usp=sharing) (public read access)
2. **Download DVC-tracked artifacts:**
   ```bash
   cd /path/to/your/repo/smart-maintenance-saas
   
   # Install DVC
   pip install dvc[gdrive]
   
   # DVC remote is already configured in .dvc/config
   # Just pull the data
   dvc pull
   
   # If you need to reconfigure the remote:
   # dvc remote add -d myremote gdrive://1cJvSRaBG0Fzs4D_wlUeVPM9l47RP_k3G
   ```

3. **Verify models downloaded:**
   ```bash
   ls mlflow_data/
   # Should see numbered experiment folders with model files
   ```

4. **Upload to your S3 bucket:**
   ```bash
   # Install AWS CLI
   pip install awscli
   
   # Configure AWS credentials
   aws configure
   # Enter: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, region
   
   # Sync MLflow data to S3
   aws s3 sync mlflow_data/ s3://your-bucket-name/mlflow_data/
   ```

#### Option B: Train Models from Scratch (60-120 minutes)

**Step 1: Download Training Datasets**

Datasets are documented in `data/README.md`. Download from these sources:

```bash
cd smart-maintenance-saas/data

# 1. AI4I 2020 Predictive Maintenance Dataset (Primary)
# Source: https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset
wget https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip
unzip ai4i+2020+predictive+maintenance+dataset.zip -d AI4I_2020_uci_dataset/

# 2. Kaggle Pump Sensor Data (Optional - requires Kaggle API)
# Source: https://www.kaggle.com/datasets/nphantawee/pump-sensor-data
kaggle datasets download -d nphantawee/pump-sensor-data
unzip pump-sensor-data.zip -d kaggle_pump_sensor_data/

# 3. NASA Bearing Dataset (Optional)
# Source: https://www.kaggle.com/datasets/vinayak123tyagi/bearing-dataset
kaggle datasets download -d vinayak123tyagi/bearing-dataset
unzip bearing-dataset.zip -d nasa_bearing_dataset/

# 4. MIMII Sound Dataset (Optional - for vibration/sound analysis)
# Source: https://zenodo.org/records/3384388
# Download manually from Zenodo and extract to MIMII_sound_dataset/
```

**Step 2: Train ML Models**

```bash
cd smart-maintenance-saas

# Install dependencies
pip install poetry
poetry install

# Build ML Docker image first
make build-ml

# Option A: Run training notebooks via Make commands (Recommended)
# These run in Docker containers for reproducibility

# Synthetic data models (foundational)
make synthetic-validation    # Data quality validation
make synthetic-anomaly       # Anomaly detection (IsolationForest)
make synthetic-forecast      # Time-series forecasting (Prophet)
make synthetic-tune-forecast # Forecasting optimization

# Real-world dataset models (gauntlets)
make classification-gauntlet # AI4I dataset (99.9% accuracy)
make pump-gauntlet          # Kaggle Pump dataset (100% accuracy)
make vibration-gauntlet     # NASA bearing dataset
make xjtu-gauntlet          # XJTU bearing dataset
make audio-gauntlet         # MIMII sound dataset (requires 2GB+ RAM)

# Option B: Run notebooks manually via Jupyter
poetry run jupyter notebook

# Execute these notebooks in order:
# Synthetic models:
# 1. notebooks/00_synthetic_data_validation.ipynb
# 2. notebooks/01_synthetic_data_exploration.ipynb
# 3. notebooks/02_synthetic_anomaly_isolation_forest.ipynb
# 4. notebooks/03_synthetic_forecast_prophet.ipynb
# 5. notebooks/04_synthetic_forecasting_tuning_and_challenger_models.ipynb

# Real-world models:
# 6. notebooks/05_classification_benchmark.ipynb (AI4I)
# 7. notebooks/08_pump_classification.ipynb (Kaggle Pump)
# 8. notebooks/06_vibration_benchmark.ipynb (NASA - optional)
# 9. notebooks/09_xjtu_vibration.ipynb (XJTU - optional)
# 10. notebooks/07_audio_benchmark.ipynb (MIMII - optional, heavy)

# Expected training time:
# - Synthetic models: 15-30 minutes total
# - Classification gauntlets: 10-20 minutes each
# - Vibration gauntlets: 20-40 minutes each
# - Audio gauntlet: 60-90 minutes (large dataset)
```

**Step 3: Register Models in MLflow**

**Step 3: Verify Models in MLflow**

After training completes, models are automatically logged to MLflow during notebook execution. You need to verify they're accessible:

```bash
# Start local MLflow server to view models
poetry run mlflow server \
   --backend-store-uri sqlite:///mlflow_db/mlflow.db \
   --default-artifact-root ./mlflow_data \
   --host 0.0.0.0 \
   --port 5000

# Open browser to view MLflow UI
# Visit: http://localhost:5000

# Verify registered models exist:
# - Navigate to "Models" tab
# - Should see models like:
#   * ai4i_classifier_randomforest_baseline
#   * anomaly_detector_refined_v2
#   * prophet_forecaster_enhanced_sensor-001
#   * vibration_anomaly_isolationforest
#   * RandomForest_MIMII_Audio_Benchmark
#   * pump_sensor_models
#   * xjtu_bearing_models

# If models are missing, re-run the training notebooks
# The notebooks automatically register champion models to MLflow
```

**Step 4: Upload to S3**

```bash
# Sync local MLflow data to S3
aws s3 sync mlflow_data/ s3://your-bucket-name/
aws s3 sync mlflow_db/ s3://your-bucket-name/mlflow_db/

# Verify upload
aws s3 ls s3://your-bucket-name/ --recursive | grep model
```

---

### Setup 2: Initialize Database Schema (10 minutes)

The TimescaleDB database needs schema initialization via Alembic migrations.

#### Step 1: Install Dependencies Locally

```bash
cd smart-maintenance-saas

# Install Python dependencies
pip install poetry
poetry install

# Verify Alembic is installed
poetry run alembic --version
```

#### Step 2: Configure Database Connection

```bash
# Edit alembic.ini to use your cloud database
nano alembic.ini

# Update this line:
# sqlalchemy.url = driver://user:pass@localhost/dbname

# To your TimescaleDB Cloud URL (synchronous driver):
sqlalchemy.url = postgresql://tsdbadmin:PASSWORD@HOST:PORT/tsdb
```

#### Step 3: Run Migrations

```bash
# Check current database version
poetry run alembic current

# Run all migrations
poetry run alembic upgrade head

# Verify tables created
poetry run python -c "
from core.database.session import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f'Tables created: {tables}')
"
# Should output: ['sensor_readings', 'ml_predictions', 'maintenance_orders', ...]
```

#### Step 4: Seed Initial Data (Optional)

```bash
# Create test sensors and initial data
poetry run python scripts/seed_database.py

# Verify seeding
poetry run python scripts/check_db.py
# Should show: X sensors, Y readings
```

**Expected Tables:**
- `sensor_readings` - Time-series sensor data
- `ml_predictions` - Model inference results
- `maintenance_orders` - Scheduled maintenance tasks
- `decision_logs` - Audit trail of automated decisions
- `agent_events` - Multi-agent system events
- `alembic_version` - Migration tracking

---

### Setup 3: Configure MLflow Tracking (If Using Cloud MLflow)

If you're using MLflow with cloud backend, initialize the tracking database:

```bash
# Set environment variable
export MLFLOW_BACKEND_STORE_URI="postgresql://tsdbadmin:PASSWORD@HOST:PORT/tsdb"

# Initialize MLflow database tables
poetry run python -c "
import mlflow
from mlflow.store.tracking import SEARCH_MAX_RESULTS_DEFAULT
mlflow.set_tracking_uri('$MLFLOW_BACKEND_STORE_URI')
# This will create mlflow tables on first connection
"

# Verify MLflow tables exist
poetry run python -c "
from sqlalchemy import create_engine, inspect
engine = create_engine('$MLFLOW_BACKEND_STORE_URI')
inspector = inspect(engine)
mlflow_tables = [t for t in inspector.get_table_names() if 'mlflow' in t or t in ['experiments', 'runs', 'metrics', 'params', 'tags']]
print(f'MLflow tables: {mlflow_tables}')
"
```

---

### Setup 4: Verify S3 Bucket Access (5 minutes)

Ensure your AWS credentials can access the S3 bucket:

```bash
# Test S3 access
aws s3 ls s3://your-bucket-name/

# Test write permissions
echo "test" > test.txt
aws s3 cp test.txt s3://your-bucket-name/test.txt
aws s3 rm s3://your-bucket-name/test.txt
rm test.txt

# Configure bucket policy (if needed)
# Go to AWS Console → S3 → your-bucket → Permissions → Bucket Policy
# Add policy allowing your IAM user/role to read/write
```

**Recommended S3 bucket structure:**
```
s3://your-bucket-name/
├── mlflow_data/
│   ├── 0/              # Experiment 0
│   │   └── <run_id>/
│   │       └── artifacts/
│   │           └── model/
│   ├── 1/              # Experiment 1
│   └── ...
└── mlflow_db/          # Optional: SQLite backup
```

---

### Setup 5: Test Local Stack (Optional but Recommended - 15 minutes)

Before deploying to cloud, verify everything works locally:

```bash
cd smart-maintenance-saas

# Start local stack
docker compose up -d

# Wait for containers to be healthy
sleep 60
docker compose ps

# Run smoke tests
poetry run pytest tests/integration/ -v

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl http://localhost:8000/health/redis

# Stop local stack
docker compose down
```

---

### Pre-Deployment Checklist

Before proceeding to VM deployment, verify:

- [ ] **ML Models:** Trained models uploaded to S3 bucket (`aws s3 ls s3://your-bucket/`)
- [ ] **Database Schema:** Alembic migrations run (`alembic current` shows latest version)
- [ ] **Database Seeded:** Test data populated (optional but recommended)
- [ ] **S3 Access:** AWS credentials tested (`aws s3 ls` works)
- [ ] **MLflow Tables:** MLflow database tables created (if using cloud backend)
- [ ] **Local Test:** Local docker-compose stack runs successfully
- [ ] **Credentials:** All `.env` variables collected and secured
- [ ] **GitHub:** Latest code pushed to `main` branch

**If all items checked → You're ready to deploy to production! ✅**

---

## Quick Reference Card

**Print this section for quick access during deployment!**

### VM Specifications

- **Size:** 4 vCPU, 8GB RAM minimum
- **Storage:** **60GB SSD** (30GB insufficient for ML containers)
- **OS:** Ubuntu 22.04 LTS
- **Open Ports:** 22 (SSH), 8000 (API), 8501 (UI optional), 5000 (MLflow)

### Essential Commands

```bash
# Connect to VM
ssh -i your-key.pem ubuntu@VM_IP

# Check container status
docker compose ps

# View logs
docker compose logs api --tail=50

# Restart services
docker compose down && docker compose up -d

# Health check
curl http://localhost:8000/health
```

### Deployment Checklist

- [ ] VM provisioned with correct specs
- [ ] Firewall rules configured (ports 22, 8000, 8501, 5000)
- [ ] Database firewall allows VM IP
- [ ] Redis firewall allows VM IP
- [ ] `.env` file copied to VM
- [ ] Containers built and healthy
- [ ] Health endpoints return 200 OK
- [ ] Streamlit Cloud secrets configured
- [ ] UI accessible via public URL
- [ ] Portuguese tooltips visible
- [ ] Golden Path Demo completes successfully

---

## Step-by-Step Deployment

### Step 1: Provision Cloud VM (15 minutes)

#### Option A: AWS EC2 (Recommended)

1. **Launch Instance:**
   - Go to AWS Console → EC2 → Launch Instance
   - **Name:** `smart-maintenance-vm`
   - **AMI:** Ubuntu Server 22.04 LTS
   - **Instance Type:** `t3.medium` (2 vCPU, 4GB RAM) or `t3.large` (2 vCPU, 8GB RAM)
   - **Storage:** **60 GB** gp3 SSD (critical - 30GB too small)
   - **Key Pair:** Create new or select existing (download `.pem` file)

2. **Configure Security Group:**
   ```
   Inbound Rules:
   - SSH (22): My IP (for security)
   - Custom TCP (8000): 0.0.0.0/0 (API)
   - Custom TCP (8501): 0.0.0.0/0 (UI - optional if using Streamlit Cloud)
   - Custom TCP (5000): 0.0.0.0/0 (MLflow)
   ```

3. **Launch and Note Public IP:**
   - Wait for instance state: "Running"
   - Note the **Public IPv4 address** (e.g., `18.117.235.91`)

#### Option B: DigitalOcean (Simplest)

1. Go to https://cloud.digitalocean.com
2. **Create Droplet:**
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** $24/mo (4 vCPU, 8GB RAM)
   - **Storage:** 60GB SSD
   - **Datacenter:** Closest to your location
   - **Authentication:** SSH Key (upload public key)
   - **Firewall:** Add rules for ports 22, 8000, 8501, 5000
3. Note the assigned public IP address

#### Option C: Google Cloud Platform

```bash
gcloud compute instances create smart-maintenance-vm \
  --machine-type=e2-standard-2 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=60GB \
  --boot-disk-type=pd-ssd \
  --tags=http-server,https-server

# Create firewall rules
gcloud compute firewall-rules create allow-smart-maintenance \
  --allow tcp:8000,tcp:8501,tcp:5000 \
  --target-tags=http-server
```

#### Option D: Microsoft Azure

```bash
az vm create \
  --resource-group smart-maintenance-rg \
  --name smart-maintenance-vm \
  --image Ubuntu2204 \
  --size Standard_B2s \
  --admin-username azureuser \
  --generate-ssh-keys

# Open ports
az vm open-port --port 8000 --resource-group smart-maintenance-rg --name smart-maintenance-vm --priority 1001
az vm open-port --port 8501 --resource-group smart-maintenance-rg --name smart-maintenance-vm --priority 1002
az vm open-port --port 5000 --resource-group smart-maintenance-rg --name smart-maintenance-vm --priority 1003
```

---

### Step 2: Configure Cloud Service Firewalls (10 minutes)

**Critical:** Your cloud database and cache services have their own firewalls. You must allowlist your VM's IP.

#### TimescaleDB Cloud

1. Log in to https://console.cloud.timescale.com
2. Navigate to your service
3. Go to **"Operations"** → **"Connection"** or **"Allowed IP Addresses"**
4. Click **"Add IP Address"**
5. Enter your VM's public IP (e.g., `18.117.235.91`)
6. Description: `Smart Maintenance Production VM`
7. Save changes

#### Render Redis

1. Log in to https://dashboard.render.com
2. Navigate to your Redis instance
3. Go to **"Access Control"** or **"IP Allow List"**
4. Click **"Add IP Address"**
5. Enter your VM's public IP
6. Save changes

**Test Connectivity (from VM later):**
```bash
# Test TimescaleDB
psql "postgresql://tsdbadmin:PASSWORD@HOST:PORT/tsdb?sslmode=require"

# Test Redis (requires redis-cli)
redis-cli -u "rediss://USERNAME:PASSWORD@HOST:PORT" ping
# Expected: PONG
```

---

### Step 3: Connect to VM and Install Docker (10 minutes)

#### 3.1: SSH Connection

On your **local machine**:

```bash
# Set correct permissions for SSH key
chmod 400 /path/to/your-key.pem

# Connect to VM
ssh -i /path/to/your-key.pem ubuntu@YOUR_VM_IP

# If AWS asks "Are you sure you want to continue connecting?", type: yes
```

**Expected output:**
```
Welcome to Ubuntu 22.04.x LTS (GNU/Linux ...)
ubuntu@ip-xxx-xxx-xxx-xxx:~$
```

#### 3.2: Install Docker

Run these commands on the **VM**:

```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add ubuntu user to docker group (avoid sudo for docker commands)
sudo usermod -aG docker ubuntu

# Install Docker Compose Plugin (v2)
sudo apt-get install -y docker-compose-plugin

# Install git (if not present)
sudo apt-get install -y git

# CRITICAL: Exit and reconnect for group changes to take effect
```bash

You have two options to configure the database for Alembic:

**Option A: Use Environment Variable (Recommended)**
```bash
# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql+asyncpg://tsdbadmin:PASSWORD@HOST:PORT/tsdb?ssl=require"

# Alembic will automatically convert asyncpg to psycopg2 driver
# The env.py script handles this conversion automatically
```

**Option B: Edit alembic.ini Directly**
```bash
# Edit alembic.ini to use your cloud database
nano alembic.ini

# Update this line:
# sqlalchemy.url = driver://user:pass@localhost/dbname

# To your TimescaleDB Cloud URL (synchronous driver):
docker compose version

# Note: Use 'sslmode=require' (not 'ssl=require') for psycopg2
```

```bash
# Create test sensors and initial data
poetry run python scripts/seed_data.py

# You can customize the amount of data:
poetry run python scripts/seed_data.py --sensors 10 --readings 1000

# Verify data was seeded:
poetry run python -c "
import asyncio
from core.database.session import async_session
from sqlalchemy import select, func
from data.models.sensor import SensorReading

async def check():
   async with async_session() as session:
      result = await session.execute(select(func.count(SensorReading.id)))
      count = result.scalar()
      print(f'✅ Database seeded: {count} sensor readings')

asyncio.run(check())
"
```

### Step 4: Prepare Production `.env` File (5 minutes)

On your **local machine**, prepare the production `.env` file:

#### 4.1: Generate Secure API Keys

```bash
cd /path/to/your/repo/smart-maintenance-saas

# Generate three secure keys
python3 -c "import secrets; print('API_KEY=' + secrets.token_urlsafe(48)); print('SECRET_KEY=' + secrets.token_urlsafe(48)); print('JWT_SECRET=' + secrets.token_urlsafe(48))"
```

Copy the output and update your `.env` file.

#### 4.2: Complete `.env` Template

Create or update `smart-maintenance-saas/.env`:

```bash
# Core
ENV=production
LOG_LEVEL=INFO

# API / Security
API_KEY=<YOUR_GENERATED_64_CHAR_KEY>
SECRET_KEY=<YOUR_GENERATED_64_CHAR_KEY>
JWT_SECRET=<YOUR_GENERATED_64_CHAR_KEY>

# Database (TimescaleDB Cloud - asyncpg driver for FastAPI)
DATABASE_URL=postgresql+asyncpg://tsdbadmin:PASSWORD@HOST:PORT/tsdb?ssl=require

# Redis (Render - rediss:// with SSL)
REDIS_URL=rediss://red-xxxxx:PASSWORD@HOST:6379

# MLflow Backend (TimescaleDB Cloud - synchronous driver for MLflow)
MLFLOW_TRACKING_URI=http://mlflow:5000
MLFLOW_BACKEND_STORE_URI=postgresql://tsdbadmin:PASSWORD@HOST:PORT/tsdb?sslmode=require

# MLflow Artifacts (S3)
MLFLOW_ARTIFACT_ROOT=s3://your-bucket-name
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
AWS_DEFAULT_REGION=us-east-2

# UI Configuration
API_BASE_URL=http://api:8000
CLOUD_MODE=true
DEPLOYMENT_ENV=production

# Notifications (optional - can leave disabled)
EMAIL_SMTP_HOST=smtp.example.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_TLS=true
EMAIL_SMTP_USER=disabled
EMAIL_SMTP_PASS=disabled
EMAIL_TO=disabled@example.com
```

**Security Note:** Never commit this file to Git. Keep it encrypted locally.

---

### Step 5: Deploy Backend to VM (30-40 minutes)

#### 5.1: Clone Repository on VM

On the **VM**:

```bash
# Navigate to /opt and create project directory
cd /opt
sudo mkdir -p smart-maintenance-saas
sudo chown ubuntu:ubuntu smart-maintenance-saas
cd smart-maintenance-saas

# Clone repository
git clone https://github.com/YourUsername/enterprise_challenge_sprint_1_hermes_reply.git .

# Navigate to app directory
cd smart-maintenance-saas

# Verify files present
ls -la
# Should see: docker-compose.yml, Dockerfile, .env (after next step)
```

#### 5.2: Copy `.env` to VM

On your **local machine**, in a **new terminal window**:

```bash
# Copy .env file to VM
scp -i /path/to/your-key.pem \
    /path/to/your/repo/smart-maintenance-saas/.env \
    ubuntu@YOUR_VM_IP:/opt/smart-maintenance-saas/smart-maintenance-saas/

# Verify transfer
```

Back on the **VM**, verify:

```bash
cd /opt/smart-maintenance-saas/smart-maintenance-saas
ls -la .env

# Check contents (verify API_KEY is present)
cat .env | grep API_KEY
# Should output: API_KEY=<your-64-char-key>
```

#### 5.3: Build and Start Containers

On the **VM**:

```bash
# Build all containers (takes 5-15 minutes depending on VM specs)
docker compose build --no-cache

# Start services in detached mode
docker compose up -d

# Wait for initialization (60-90 seconds)
sleep 60

# Check container status
docker compose ps
```

**Expected output:**
```
NAME                          STATUS                   PORTS
smart_maintenance_api         Up (healthy)             0.0.0.0:8000->8000/tcp
smart_maintenance_mlflow      Up (healthy)             0.0.0.0:5000->5000/tcp
smart_maintenance_ui          Up (healthy)             0.0.0.0:8501->8501/tcp
smart_maintenance_db          Up (healthy)             5432/tcp
smart_maintenance_redis       Up (healthy)             6379/tcp
smart_maintenance_toxiproxy   Up                       8474/tcp
```

**All containers must show `(healthy)` status before proceeding.**

#### 5.4: Troubleshoot Unhealthy Containers

If any container shows `(unhealthy)` or `Restarting`:

```bash
# Check logs for specific container
docker compose logs api --tail=100
docker compose logs mlflow --tail=100

# Common issues and fixes:

# 1. MLflow unhealthy (can't connect to TimescaleDB)
# - Verify DATABASE_URL in .env
# - Check TimescaleDB firewall allows VM IP
# - Check MLFLOW_BACKEND_STORE_URI uses postgresql:// (not postgresql+asyncpg://)

# 2. API unhealthy (waiting for MLflow)
# - API waits for MLflow to be healthy (this is expected)
# - Fix MLflow first, API will start automatically

# 3. Permission denied on logs
# - Rebuild with: docker compose down && docker compose up -d --build

# 4. Connection refused errors
# - Check firewall rules on cloud services
# - Verify .env credentials are correct
```

---

### Step 6: Validate Backend (15 minutes)

Once all containers are healthy, test the API endpoints.

#### 6.1: Health Checks

On the **VM**:

```bash
# Export API key for convenience
export API_KEY="<your-api-key-from-env>"

# Test 1: General health
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"1.0.0",...}

# Test 2: Database connectivity
curl http://localhost:8000/health/db
# Expected: {"status":"healthy","database":"connected",...}

# Test 3: Redis connectivity
curl http://localhost:8000/health/redis
# Expected: {"status":"healthy","redis":"connected",...}
```

#### 6.2: Data Ingestion Test

```bash
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

# Expected: {"message":"Data ingested successfully","sensor_id":"DEPLOY_TEST_001",...}
```

#### 6.3: ML Prediction Test

```bash
# Test 5: ML prediction (verifies MLflow connectivity)
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

# Expected: {"prediction":[0],...} or {"prediction":[1],...}
```

**If all 5 tests pass → Backend is PRODUCTION READY ✅**

---

### Step 7: Deploy UI to Streamlit Cloud (20 minutes)

#### 7.1: Push Latest Code to GitHub

On your **local machine**:

```bash
cd /path/to/your/repo

# Ensure all changes are committed
git add .
git commit -m "Production deployment - V1.0"
git push origin main
```

#### 7.2: Configure Streamlit Cloud

1. **Go to Streamlit Cloud:** https://share.streamlit.io
2. **Sign in** with your GitHub account
3. **Click "New app"**
4. **Configure deployment:**
   - **Repository:** `YourUsername/enterprise_challenge_sprint_1_hermes_reply`
   - **Branch:** `main`
   - **Main file path:** `smart-maintenance-saas/ui/streamlit_app.py`
   - **App URL:** Choose a custom subdomain (e.g., `smart-maintenance`)

5. **Click "Advanced settings..."**
6. **Python version:** Select `3.11`

7. **Add Secrets:** Paste the following TOML configuration:

```toml
[default]
API_BASE_URL = "http://YOUR_VM_IP:8000"
API_KEY = "your-production-api-key"
CLOUD_MODE = "true"
DEPLOYMENT_ENV = "production"
```

**Replace:**
- `YOUR_VM_IP` with your EC2/VM public IP (e.g., `18.117.235.91`)
- `your-production-api-key` with the API_KEY from your `.env`

8. **Click "Deploy!"**

#### 7.3: Monitor Deployment

- Streamlit will build your app (2-3 minutes)
- Watch the logs for any errors
- Once complete, you'll get a public URL: `https://your-app.streamlit.app`

#### 7.4: Verify UI Loads

1. Open the Streamlit URL in your browser
2. Homepage should load with the Smart Maintenance logo
3. Sidebar should show all menu options
4. Click "?" tooltips → should display Portuguese descriptions ✅

**If UI loads successfully → Frontend is DEPLOYED ✅**

---

## Post-Deployment Validation

### End-to-End Testing (20 minutes)

Test these 5 critical user journeys to confirm full system functionality:

#### Journey 1: Manual Data Ingestion (3 min)

1. Navigate to **"Simulation Console"** or **"Manual Sensor Ingestion"**
2. Click **"?"** tooltip → Verify Portuguese description ✅
3. Fill form:
   - Sensor ID: `E2E_TEST_001`
   - Value: `25.0`
   - Sensor Type: `temperature`
   - Unit: `celsius`
4. Click **"Ingest Reading"**
5. **Verify:** Success message with latency metrics (e.g., "Ingested in 150ms") ✅

#### Journey 2: Data Explorer (3 min)

1. Navigate to **"Data Explorer"**
2. **Verify:** Table shows pagination and total record count ✅
3. **Verify:** `E2E_TEST_001` reading appears in the table ✅
4. Test **sensor filter dropdown** → select a sensor ID
5. Click **"?"** tooltips → Verify Portuguese translations ✅

#### Journey 3: Prediction Workflow (4 min)

1. Navigate to **"Prediction"** page
2. Click **"?"** tooltips → Verify Portuguese help text ✅
3. Select model: `ai4i_classifier_randomforest_baseline`
4. Click **"Generate Forecast"**
5. **Verify:** Forecast appears in ~2 seconds ✅
6. Click **"Create Maintenance Order"**
7. **Verify:** Maintenance schedule displayed with technician assignment ✅

#### Journey 4: Golden Path Demo (5 min)

**This is the most important test!**

1. Navigate to **"Golden Path Demo"**
2. Click **"?"** tooltip → Verify Portuguese description + timeout warning ✅
3. Set **Number of sensor events:** `10`
4. Click **"Start Golden Path Demo"**
5. **Verify:** Progress bar shows 7 stages:
   - Stage 1: Sensor Data Ingestion
   - Stage 2: Anomaly Detection
   - Stage 3: Data Validation
   - Stage 4: ML Prediction
   - Stage 5: Maintenance Scheduling
   - Stage 6: Agent Workflow
   - Stage 7: Reporting
6. **Verify:** Demo completes in 30-90 seconds ✅
7. **Verify:** Success summary appears with all stages completed ✅

#### Journey 5: Decision Log & Reporting (5 min)

1. Navigate to **"Decision Log"**
2. **Verify:** Automated decisions from Golden Path appear in list ✅
3. Submit a manual decision:
   - Request ID: `REQ_E2E_001`
   - Operator: `OP_TEST`
   - Decision: `Approved`
4. Click **"?"** tooltips → Verify Portuguese scope note ✅
5. **Verify:** Decision appears in list below ✅
6. Click **"Export to CSV"**
7. **Verify:** CSV file downloads successfully ✅

### Final Validation Checklist

- [ ] All 5 journeys completed without errors
- [ ] Portuguese tooltips (?) visible on all pages
- [ ] Data flows correctly: Ingest → Store → Retrieve
- [ ] ML predictions return in <3 seconds
- [ ] Golden Path completes in <90 seconds
- [ ] No 500 errors in browser console (check F12 DevTools)
- [ ] No timeout errors in Streamlit UI
- [ ] Backend containers remain healthy (check VM)

**If all checks pass → V1.0 IS FULLY DEPLOYED! 🎉**

---

## Common Errors & Solutions

### Error 1: Permission Denied on Script Files

**Symptom:**
```
Error response from daemon: failed to create shim task: OCI runtime create failed: 
runc create failed: unable to start container process: exec: "./scripts/toxiproxy_init.sh": 
permission denied: unknown
```

**Cause:** Script file is not marked as executable in Git repository.

**Solution:**

On your **local machine**:
```bash
cd /path/to/your/repo/smart-maintenance-saas

# Fix file permissions in Git
git update-index --chmod=+x scripts/toxiproxy_init.sh

# Commit and push
git commit -m "fix: Add execute permission to toxiproxy_init.sh"
git push origin main
```

On the **VM**:
```bash
cd /opt/smart-maintenance-saas/smart-maintenance-saas

# Pull latest changes
git pull origin main

# Rebuild
docker compose down
docker compose up -d --build
```

### Error 2: Permission Denied on Log Files

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: '/app/logs/dlq_events.log'
```

**Cause:** Application's non-root user doesn't have write permission to `/app/logs` directory.

**Solution:**

This was fixed in `Dockerfile` (already in your repo):
```dockerfile
# Copy application code
COPY --chown=appuser:appuser . .

# Create log directory and set ownership BEFORE switching users
RUN mkdir -p /app/logs && chown -R appuser:appuser /app/logs

# NOW switch to non-root user
USER appuser
```

If you still see this error:
```bash
# On VM, rebuild containers
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Error 3: MLflow Container Unhealthy

**Symptom:**
```
dependency failed to start: container smart_maintenance_mlflow is unhealthy
```

**Cause:** MLflow can't connect to TimescaleDB backend.

**Solution:**

1. **Check TimescaleDB firewall allows VM IP:**
   ```bash
   # On VM, test connection
   sudo apt-get install -y postgresql-client
   psql "postgresql://tsdbadmin:PASSWORD@HOST:PORT/tsdb?sslmode=require"
   # Should connect successfully
   ```

2. **Verify `.env` has correct backend URI:**
   ```bash
   # On VM
   cat .env | grep MLFLOW_BACKEND_STORE_URI
   # Should be: postgresql://... (NOT postgresql+asyncpg://)
   ```

3. **Check MLflow logs:**
   ```bash
   docker compose logs mlflow --tail=100
   # Look for connection errors
   ```

4. **Restart MLflow:**
   ```bash
   docker compose restart mlflow
   # Wait 60 seconds
   docker compose ps
   ```

### Error 4: UI Shows "Connection Refused"

**Symptom:**
Streamlit UI displays: `Error: Connection refused when calling API`

**Cause 1:** API container is not running on VM.

**Solution:**
```bash
# On VM, check container status
docker compose ps

# If API is unhealthy, check logs
docker compose logs api --tail=100

# Restart if needed
docker compose restart api
```

**Cause 2:** Firewall blocking connection.

**Solution:**
- Verify AWS Security Group allows port 8000 from `0.0.0.0/0`
- Test from local machine: `curl http://YOUR_VM_IP:8000/health`
- If timeout, fix firewall rules

**Cause 3:** Incorrect `API_BASE_URL` in Streamlit secrets.

**Solution:**
- Go to Streamlit Cloud → App settings → Secrets
- Verify: `API_BASE_URL = "http://YOUR_VM_IP:8000"` (use public IP, not localhost)
- Save and redeploy

### Error 5: ModuleNotFoundError in UI

**Symptom:**
```
ModuleNotFoundError: No module named 'ui.lib.api_client'
```

**Cause:** Python import paths incorrect for Streamlit Cloud environment.

**Solution:**

This was fixed (already in your repo). If you see it:

On **local machine**:
```bash
cd /path/to/your/repo/smart-maintenance-saas

# Fix imports in all UI files
find ui -name "*.py" -exec sed -i 's/from ui\.lib/from lib/g' {} +

# Commit and push
git add ui/
git commit -m "fix(ui): Correct import paths for Streamlit Cloud"
git push origin main

# Streamlit Cloud will auto-redeploy
```

### Error 6: Insufficient Disk Space

**Symptom:**
```
no space left on device
```

**Cause:** 30GB storage too small for ML containers.

**Solution:**

1. **Stop and remove containers:**
   ```bash
   docker compose down
   docker system prune -af --volumes
   ```

2. **Resize VM disk to 60GB:**
   - AWS: Modify volume in EC2 console, then resize filesystem
   - DigitalOcean: Resize droplet
   - GCP: Resize persistent disk

3. **Rebuild:**
   ```bash
   docker compose up -d --build
   ```

### Error 7: Database Connection Timeout

**Symptom:**
```
asyncpg.exceptions.ConnectionTimeoutError: connection timeout
```

**Cause:** TimescaleDB firewall doesn't allow VM IP.

**Solution:**

1. **Add VM IP to TimescaleDB allowlist** (see Step 2)
2. **Test connection:**
   ```bash
   # On VM
   psql "postgresql://tsdbadmin:PASSWORD@HOST:PORT/tsdb?sslmode=require"
   ```
3. **Restart API:**
   ```bash
   docker compose restart api
   ```

### Error 8: Poetry "Could not parse version constraint: <empty>"

**Symptom:**
```
Building notebook_runner container fails with:
poetry lock && poetry install --with dev --no-root
Could not parse version constraint: <empty>
exit code: 1
```

**Cause:** This is a known bug in Poetry 1.8.x where the dependency resolver encounters malformed version metadata from PyPI packages, resulting in an empty version constraint during installation.

**Solution:**

**Option A: Downgrade Poetry (Recommended)** 

The project has been updated to use Poetry 1.7.1 which doesn't have this bug:

```bash
# On local machine
cd /path/to/your/repo/smart-maintenance-saas

# Verify Dockerfile.ml uses Poetry 1.7.1
grep "poetry==" Dockerfile.ml
# Should show: RUN pip install --no-cache-dir poetry==1.7.1

# If it shows 1.8.3, update it:
sed -i 's/poetry==1.8.3/poetry==1.7.1/g' Dockerfile.ml

# Rebuild without cache
docker compose build --no-cache
```

**Option B: Clean Local Poetry Cache**

If you're still encountering issues after downgrading:

```bash
# Remove local poetry.lock and virtual environment
rm -f poetry.lock
sudo rm -rf .venv

# Clear Poetry cache
poetry cache clear pypi --all

# Regenerate lock file
poetry lock

# Rebuild Docker images
docker compose build --no-cache
```

**Option C: Use Pre-Generated Lock File**

If Option A and B fail, the repository includes a working `poetry.lock` file. Ensure it's not in `.gitignore` and commit it:

```bash
# Check if poetry.lock exists and is tracked
git ls-files | grep poetry.lock

# If missing, regenerate and commit
poetry lock
git add poetry.lock
git commit -m "chore: Add working poetry.lock file"
git push origin main
```

**Prevention:**
- Pin Poetry version in Dockerfiles to avoid automatic upgrades
- Commit `poetry.lock` to version control for reproducible builds
- Use `poetry lock --no-update` when adding dependencies to avoid unnecessary resolution

---

## Monitoring & Maintenance

### Daily Monitoring

```bash
# SSH into VM
ssh -i your-key.pem ubuntu@YOUR_VM_IP

# Check container health
docker compose ps

# Check disk usage
df -h

# Check memory usage
free -h

# View recent logs
docker compose logs --tail=100 --timestamps
```

### Weekly Maintenance

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Pull latest code changes
cd /opt/smart-maintenance-saas/smart-maintenance-saas
git pull origin main

# Rebuild if needed
docker compose up -d --build

# Clean up unused Docker resources
docker system prune -f
```

### Performance Monitoring

```bash
# Real-time container stats
docker stats

# API response time
time curl http://localhost:8000/health

# Database connection count
docker compose exec api python3 -c "
from core.database.session import engine
print(f'Pool size: {engine.pool.size()}')
"
```

### Backup Procedures

```bash
# Backup .env file (run locally)
scp -i your-key.pem ubuntu@YOUR_VM_IP:/opt/.../smart-maintenance-saas/.env \
    ./backups/.env.$(date +%Y%m%d)

# Backup database (TimescaleDB Cloud has automated backups)
# Check your TimescaleDB dashboard for backup status

# Backup code (Git)
git tag v1.0-prod-$(date +%Y%m%d)
git push --tags
```

### Security Updates

- **Rotate API keys every 90 days**
- **Update dependencies monthly**
- **Monitor AWS Security Advisories**
- **Review TimescaleDB access logs**
- **Enable 2FA on all cloud accounts**

---

## Deployment URLs Reference

After successful deployment, document these URLs:

```
Production Environment
├── Backend API: http://YOUR_VM_IP:8000
│   └── API Docs: http://YOUR_VM_IP:8000/docs
├── MLflow Tracking: http://YOUR_VM_IP:5000
├── Streamlit UI: https://your-app.streamlit.app
├── TimescaleDB: (managed service - no direct URL)
└── Redis: (managed service - no direct URL)
```

Share the **Streamlit UI URL** with stakeholders for testing.

---

## Support & Troubleshooting

### Getting Help

1. **Check logs first:**
   ```bash
   docker compose logs <service-name> --tail=200
   ```

2. **Search this guide** for error messages

3. **Review architecture docs:**
   - `docs/SYSTEM_AND_ARCHITECTURE.md`
   - `docs/COMPREHENSIVE_DOCUMENTATION.md`

4. **Test components individually:**
   ```bash
   # Test database
   curl http://localhost:8000/health/db

   # Test Redis
   curl http://localhost:8000/health/redis

   # Test MLflow
   curl http://localhost:5000/health
   ```

### Emergency Rollback

If deployment fails critically:

```bash
# On VM
cd /opt/smart-maintenance-saas/smart-maintenance-saas

# Stop all services
docker compose down

# Revert to previous version
git checkout tags/v1.0-prod-YYYYMMDD

# Rebuild
docker compose up -d --build
```

---

## Success Criteria

Your deployment is successful when:

- ✅ All 6 Docker containers show `(healthy)` status
- ✅ Health endpoints return 200 OK
- ✅ Data ingestion works (POST /api/v1/data/ingest)
- ✅ ML predictions work (POST /api/v1/ml/predict)
- ✅ Streamlit UI loads at public URL
- ✅ Portuguese tooltips visible on all pages
- ✅ Golden Path Demo completes in <90 seconds
- ✅ No errors in browser console
- ✅ No timeout errors in UI

**Congratulations! Your Smart Maintenance SaaS system is live in production! 🚀**

---

**Document Version:** 1.0  
**Last Tested:** 2025-10-03  
**Next Review:** 2025-11-03
