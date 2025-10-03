# S3 Artifact Storage Mapping

**Last Updated:** 2025-10-03  
**Status:** V1.0 Production (17+ models deployed)  
**Related:** 
- [V1_UNIFIED_DEPLOYMENT_CHECKLIST.md](./V1_UNIFIED_DEPLOYMENT_CHECKLIST.md) - Current deployment procedures
- [Sprint 4 Changelog](./legacy/sprint_4_changelog.md) - S3 integration achievements (archived)  

This document provides a comprehensive mapping between our S3 bucket structure (`s3://yan-smart-maintenance-artifacts/`) and the corresponding MLflow experiments, runs, and registered models.

## Quick Reference Table

| S3 Folder | Experiment Name | Purpose | Models Count | Key Models |
|-----------|----------------|---------|--------------|------------|
| 1/ | Synthetic_Data_Validation | MLflow validation | 2 | realistic_sensor_validation_isolation_forest |
| 2/ | Anomaly Detection | Enhanced anomaly detection | 1 | anomaly_detector_refined_v2 |
| 3/ | Forecasting Models | Time-series forecasting | 2 | prophet_forecaster_enhanced_sensor-001 |
| 4/ | Classification Gauntlet (AI4I) | Machine failure prediction | 6 | ai4i_classifier_* (baseline + engineered) |
| 5/ | Vibration Gauntlet (NASA) | NASA bearing analysis | 2 | vibration_anomaly_isolationforest |
| 6/ | Audio Gauntlet (MIMII) | Audio anomaly detection | 2 | RandomForest_MIMII_Audio_Benchmark |
| 7/ | Vibration Gauntlet (XJTU) | XJTU bearing analysis | 2 | xjtu_anomaly_isolation_forest |

## Overview

- **S3 Bucket:** `yan-smart-maintenance-artifacts`
- **Total Experiments:** 7 (folders 1/ through 7/)
- **Total Registered Models:** 17
- **Storage Pattern:** `{experiment_id}/{run_id}/artifacts/{artifact_path}`

## Experiment-to-S3 Folder Mapping

### Folder 1/ - Synthetic Data Validation
- **Experiment ID:** 1
- **Experiment Name:** "Synthetic_Data_Validation"
- **Purpose:** MLflow infrastructure validation with realistic sensor data
- **Sub-folders (Run IDs):**
  - `64535d709de2458396986ff9f939517a/` - **SUCCESSFUL RUN**
  - `e69dbc0ecfe84289a16b2ee3f0e2097f/` - **SUCCESSFUL RUN**
- **Registered Models:**
  - `realistic_sensor_validation_isolation_forest` (Run: 64535d709de2458396986ff9f939517a)
  - `synthetic_validation_isolation_forest` (Run: e69dbc0ecfe84289a16b2ee3f0e2097f)
- **Artifacts:** Model files, feature names, sensor configuration

### Folder 2/ - Anomaly Detection
- **Experiment ID:** 2
- **Experiment Name:** "Anomaly Detection"
- **Purpose:** Enhanced anomaly detection using real sensor data
- **Sub-folders (Run IDs):**
  - `b702f86472f44eefb1d24ec0b68361ad/`
- **Registered Models:**
  - `anomaly_detector_refined_v2`
- **Artifacts:** IsolationForest model, feature engineering pipeline, anomaly plots

### Folder 3/ - Forecasting Models
- **Experiment ID:** 3
- **Experiment Name:** "Forecasting Models"
- **Purpose:** Time-series forecasting with Prophet and LightGBM
- **Sub-folders (Run IDs):**
  - `bf65e69afa984d93a4c86693dbca461b/` - Prophet model
  - `95eebf78e6af44d4aa15bae87a7a89e8/` - LightGBM challenger
  - Additional tuning runs from synthetic forecasting
- **Registered Models:**
  - `prophet_forecaster_enhanced_sensor-001`
  - `lightgbm_forecaster_challenger`
- **Artifacts:** Prophet models, LightGBM models, forecast plots, residual analysis

### Folder 4/ - Classification Gauntlet (AI4I)
- **Experiment ID:** 4
- **Experiment Name:** "Classification Gauntlet (AI4I)"
- **Purpose:** Machine failure prediction using AI4I dataset
- **Sub-folders (Run IDs):**
  - `c795e657a4d147f1ac84ea0dc2bb68f1/` - RandomForest baseline
  - `b0fe71b9c0824657838fb4183e47adb2/` - SVC baseline
  - `551acd88dc614e3c8148f726d55e3edd/` - LightGBM baseline
  - `e351e96724684fe98e89d2df4aece3dd/` - RandomForest engineered
  - `ab5a084af93f4398af4b942f4cfb8c1b/` - SVC engineered
  - `027b7fe9d28443fdb51051ccfdbaeb52/` - LightGBM engineered
- **Registered Models:**
  - `ai4i_classifier_randomforest_baseline`
  - `ai4i_classifier_randomforest_engineered`
  - `ai4i_classifier_svc_baseline`
  - `ai4i_classifier_svc_engineered`
  - `ai4i_classifier_lightgbm_baseline`
  - `ai4i_classifier_lightgbm_engineered`
- **Artifacts:** 6 classification models, performance metrics, feature importance plots

### Folder 5/ - Vibration Gauntlet (NASA)
- **Experiment ID:** 5
- **Experiment Name:** "Vibration Gauntlet (NASA)"
- **Purpose:** Vibration-based anomaly detection using NASA bearing dataset
- **Sub-folders (Run IDs):**
  - `2ee0f69b335a42da9aabe2f1cf7668b0/` - IsolationForest
  - `fdd9bade7f144306923e01efe515e64b/` - OneClassSVM
- **Registered Models:**
  - `vibration_anomaly_isolationforest`
  - `vibration_anomaly_oneclasssvm`
- **Artifacts:** Vibration analysis models, feature extraction results, anomaly detection plots

### Folder 6/ - Audio Gauntlet (MIMII)
- **Experiment ID:** 6
- **Experiment Name:** "Audio Gauntlet (MIMII)"
- **Purpose:** Audio-based anomaly detection using MIMII sound dataset
- **Sub-folders (Run IDs):**
  - `7c0bd554459244d59c59c7690323cbc4/`
- **Registered Models:**
  - `RandomForest_MIMII_Audio_Benchmark`
  - `MIMII_Audio_Scaler`
- **Artifacts:** Audio classification model, feature scaler, audio analysis results

### Folder 7/ - Vibration Gauntlet (XJTU)
- **Experiment ID:** 7
- **Experiment Name:** "Vibration Gauntlet (XJTU)"
- **Purpose:** Advanced vibration analysis using XJTU bearing dataset
- **Sub-folders (Run IDs):**
  - `56453d8fa3af43b987c67553b0985872/`
- **Registered Models:**
  - `xjtu_anomaly_isolation_forest`
  - `xjtu_feature_scaler`
- **Artifacts:** XJTU vibration models, comprehensive feature extraction, bearing analysis

## Artifact Structure

Each run folder typically contains:
```
{run_id}/
├── artifacts/
│   ├── model/                    # Main model files
│   │   ├── model.pkl             # Serialized model
│   │   ├── conda.yaml            # Environment specification
│   │   ├── python_env.yaml       # Python environment
│   │   └── MLmodel               # MLflow model metadata
│   ├── plots/                    # Visualization artifacts
│   │   ├── *.png                 # Performance plots
│   │   └── *.pdf                 # Analysis charts
│   ├── feature_names.txt         # Feature specifications
│   ├── sensor_config.txt         # Sensor configuration
│   └── additional_artifacts/     # Domain-specific files
```

## Model Categories by Type

### Anomaly Detection Models
- `realistic_sensor_validation_isolation_forest` (S3: 1/)
- `synthetic_validation_isolation_forest` (S3: 1/)
- `anomaly_detector_refined_v2` (S3: 2/)
- `vibration_anomaly_isolationforest` (S3: 5/)
- `vibration_anomaly_oneclasssvm` (S3: 5/)
- `xjtu_anomaly_isolation_forest` (S3: 7/)

### Classification Models
- `ai4i_classifier_randomforest_baseline` (S3: 4/)
- `ai4i_classifier_randomforest_engineered` (S3: 4/)
- `ai4i_classifier_svc_baseline` (S3: 4/)
- `ai4i_classifier_svc_engineered` (S3: 4/)
- `ai4i_classifier_lightgbm_baseline` (S3: 4/)
- `ai4i_classifier_lightgbm_engineered` (S3: 4/)
- `RandomForest_MIMII_Audio_Benchmark` (S3: 6/)

### Forecasting Models
- `prophet_forecaster_enhanced_sensor-001` (S3: 3/)
- `lightgbm_forecaster_challenger` (S3: 3/)

### Preprocessing/Utility Models
- `MIMII_Audio_Scaler` (S3: 6/)
- `xjtu_feature_scaler` (S3: 7/)

## Usage Instructions

### Loading Models from S3
```python
import mlflow

# Load any registered model
model = mlflow.sklearn.load_model("models://{model_name}/latest")

# Or load directly from S3 path
model = mlflow.sklearn.load_model("s3://yan-smart-maintenance-artifacts/{exp_id}/{run_id}/artifacts/model")
```

### Accessing Artifacts
- **MLflow UI:** Navigate to experiments to browse artifacts
- **Direct S3 Access:** Use AWS CLI or boto3 to download specific artifacts
- **Programmatic Access:** Use MLflow API to list and download artifacts

## Quality Metrics Summary

### High-Performing Models (>90% Accuracy)
- All AI4I classification models (Folder 4/)
- Realistic sensor validation models (Folder 1/)

### Specialized Domain Models
- **Vibration Analysis:** Folders 5/ and 7/
- **Audio Analysis:** Folder 6/
- **Time-Series Forecasting:** Folder 3/

## Maintenance Notes

- **Last Updated:** September 16, 2025
- **Total Storage:** All artifacts stored in `s3://yan-smart-maintenance-artifacts/`
- **Backup Status:** All models registered in MLflow with metadata
- **Access Pattern:** Production models should be loaded via MLflow registry for version control