# DVC Setup Guide - Data Version Control with Google Drive

**Last Updated:** 2025-09-30  
**Status:** Optional setup for local development  
**Note:** V1.0 production uses cloud TimescaleDB and S3 artifact storage directly; DVC provides alternative for local dataset management

## 🎯 Overview

This project uses DVC (Data Version Control) to manage large datasets and ML artifacts. All data is stored in a shared Google Drive folder, allowing complete reproducibility of the development environment.

## 📁 Google Drive Storage

**Shared Folder**: [Smart Maintenance SaaS - DVC Data](https://drive.google.com/drive/folders/1cJvSRaBG0Fzs4D_wlUeVPM9l47RP_k3G?usp=sharing)

This folder contains:
- **Real-world Datasets**: AI4I_2020, MIMII_sound, NASA_bearing, XJTU_bearing, Kaggle_pump (19,855+ files)
- **Synthetic Data**: 9,000 sensor readings for development/testing
- **ML Artifacts**: Complete MLflow experiment tracking and model registry data

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd smart-maintenance-saas
pip install dvc[gdrive]
```

### 2. Download All Data
```bash
dvc pull
```

This single command downloads all datasets, ML models, and artifacts from Google Drive to your local environment.

### 3. Verify Setup
```bash
ls data/                    # Should show all dataset directories
ls mlflow_data/ mlflow_db/  # Should show ML artifacts
```

## 🔧 Advanced Setup (Contributors Only)

If you need to push new data or modify the remote:

### Environment Variables
Create a `.env` file with:
```env
GDRIVE_CLIENT_ID=your_client_id
GDRIVE_CLIENT_SECRET=your_client_secret
```

### Google Drive OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project
3. Enable Google Drive API
4. Create OAuth 2.0 credentials
5. Download and save as `gdrive_credentials.json` (excluded from git)

## 📊 Dataset Overview

| Dataset | Type | Size | Description |
|---------|------|------|-------------|
| AI4I_2020_uci_dataset | Machine Failure | ~2MB | UCI predictive maintenance dataset |
| kaggle_pump_sensor_data | Pump Sensors | ~5MB | Industrial pump sensor readings |
| MIMII_sound_dataset | Audio Analysis | ~2GB | Machine sound anomaly detection |
| nasa_bearing_dataset | Bearing Analysis | ~100MB | NASA bearing degradation data |
| XJTU_SY_bearing_datasets | Bearing Lifecycle | ~500MB | Complete bearing lifecycle data |
| sensor_data.csv | Synthetic | 627KB | Generated sensor data (9,000 readings) |

## 🔒 Security Notes

- Google Drive credentials are **never committed** to git
- OAuth tokens are stored locally in `~/.cache/pydrive2fs/`
- The shared folder has public read access for easy collaboration
- Write access requires proper OAuth authentication

## 🛠 Commands Reference

```bash
# Check status
dvc status

# Pull all data
dvc pull

# Push changes (requires authentication)
dvc push

# Add new data
dvc add data/new_dataset/
git add data/new_dataset.dvc
git commit -m "Add new dataset"

# Check remote info
dvc remote list -v
```

## 🔄 Reproducibility

The complete development environment can be reproduced with:
1. `git clone` - Gets code and DVC configuration
2. `dvc pull` - Downloads all data from Google Drive
3. `docker-compose up` - Starts all services with identical data

This ensures 100% reproducibility across different machines and environments.