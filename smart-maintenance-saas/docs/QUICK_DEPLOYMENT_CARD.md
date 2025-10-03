# 🚀 Quick Deployment Reference Card

**Print this and keep it handy during deployment!**

---

## ✅ What's Ready

- ✅ `.env` file with production keys
- ✅ Code tested (ML fallback, Portuguese UI)
- ✅ Cloud services configured (TimescaleDB, Redis, S3)
- ✅ Documentation complete

## 🎯 Your Deployment Sequence (90 minutes)

### STEP 1: Get a VM (15 min)
**DO THIS FIRST**

Provision VM with:
- **Size:** 4 vCPU, 8GB RAM minimum
- **OS:** Ubuntu 22.04 LTS
- **Storage:** 30GB SSD
- **Open Ports:** 22, 8000, 8501, 5000

**Easiest options:**
- DigitalOcean: $12/mo droplet
- AWS EC2: t3.medium instance
- GCP: e2-standard-2 instance

---

### STEP 2: Install Docker (5 min)
**SSH into VM, then:**

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo apt-get install docker-compose-plugin -y
exit
# SSH back in
docker --version  # Should show v24+
```

---

### STEP 3: Deploy Backend (30 min)
**On VM:**

```bash
# Clone repo
cd /opt
sudo mkdir smart-maintenance-saas && sudo chown $USER:$USER smart-maintenance-saas
cd smart-maintenance-saas
git clone https://github.com/YanCotta/enterprise_challenge_sprint_1_hermes_reply.git .
cd smart-maintenance-saas
```

**On your LOCAL machine:**
```bash
# Copy .env to VM
scp /home/yan/Documents/Git/enterprise_challenge_sprint_1_hermes_reply/smart-maintenance-saas/.env ubuntu@YOUR_VM_IP:/opt/smart-maintenance-saas/.env
```

**Back on VM:**
```bash
# Build and start
docker compose build --no-cache  # Takes 5-10 min
docker compose up -d
sleep 30
docker compose ps  # All should be "Up (healthy)"
```

---

### STEP 4: Test Backend (10 min)
**On VM:**

```bash
export API_KEY="9K5jDmlKIag0ME7Io_nadv7tYrZtLxwpfyaxHYRFTIQ5Hc36LBJcjn4Nbxa6IO4T"

# Test health
curl http://localhost:8000/health

# Test ingestion
curl -X POST http://localhost:8000/api/v1/data/ingest \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"sensor_id":"DEPLOY_TEST","value":25.5,"sensor_type":"temperature","unit":"celsius"}'
```

**Both should return 200 OK ✅**

---

### STEP 5: Deploy UI (20 min)
**On your LOCAL machine:**

```bash
# Push to GitHub
cd /home/yan/Documents/Git/enterprise_challenge_sprint_1_hermes_reply
git add .
git commit -m "V1.0 production deployment"
git push origin main
```

**Then:**
1. Go to https://share.streamlit.io
2. Click "New app"
3. Select repo: `YanCotta/enterprise_challenge_sprint_1_hermes_reply`
4. Main file: `smart-maintenance-saas/ui/streamlit_app.py`
5. Add secrets:
   ```toml
   [default]
   API_BASE_URL = "http://YOUR_VM_IP:8000"
   API_KEY = "9K5jDmlKIag0ME7Io_nadv7tYrZtLxwpfyaxHYRFTIQ5Hc36LBJcjn4Nbxa6IO4T"
   CLOUD_MODE = "true"
   DEPLOYMENT_ENV = "production"
   ```
6. Click "Deploy"

**Wait 2-3 minutes → Note your URL: `https://your-app.streamlit.app`**

---

### STEP 6: Validate Everything (15 min)
**Open UI in browser, test these 5 journeys:**

| Journey | What to Test | Success Criteria |
|---------|--------------|------------------|
| 1. Manual Ingestion | Submit sensor reading | ✅ Success message + latency |
| 2. Data Explorer | View readings, use filters | ✅ Data appears, pagination works |
| 3. Prediction | Generate forecast + create order | ✅ Forecast in <3s, order created |
| 4. Golden Path Demo | Run with 10 events | ✅ Completes in <90s, 7 stages |
| 5. Decision Log | Create + export decision | ✅ Appears in list, CSV downloads |

**On EVERY page: Click "?" tooltips → Should show Portuguese text ✅**

---

## 🎉 Success!

If all 6 steps complete:
- **Backend:** `http://YOUR_VM_IP:8000`
- **UI:** `https://your-app.streamlit.app`
- **MLflow:** `http://YOUR_VM_IP:5000`
- **API Docs:** `http://YOUR_VM_IP:8000/docs`

---

## 🆘 Quick Troubleshooting

**Containers not healthy?**
```bash
docker compose logs api --tail=50
docker compose restart api
```

**UI can't reach API?**
- Verify port 8000 is open: `curl http://YOUR_VM_IP:8000/health` from local machine
- Check Streamlit secrets have correct VM IP

**MLflow issues?**
```bash
# Enable fallback mode:
echo "DISABLE_MLFLOW_MODEL_LOADING=true" >> .env
docker compose restart api
```

---

## 📞 Need Help?

See full guide: `docs/DEPLOYMENT_EXECUTION_GUIDE.md`

---

**Created:** 2025-10-03  
**Your API Key:** `9K5jDmlKIag0ME7Io_nadv7tYrZtLxwpfyaxHYRFTIQ5Hc36LBJcjn4Nbxa6IO4T`
