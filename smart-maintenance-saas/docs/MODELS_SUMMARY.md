# Smart Maintenance SaaS: ML Project Summary & Model Registry Guide (V1.0 Production)

**Last Updated:** 2025-09-30  
**Status:** V1.0 Production Ready  
**Model Count:** 17+ models in MLflow registry with S3 artifact storage  
**Related Documentation:**
- [v1_release_must_do.md Section 2.1](./v1_release_must_do.md) - ML registry in backend capability matrix
- [ml/README.md](./ml/README.md) - Training pipelines and feature engineering
- [Sprint 4 Changelog](./legacy/sprint_4_changelog.md) - S3 serverless model loading achievements

**Architecture Diagrams:**
- [MLflow Model Management Pipeline](./SYSTEM_AND_ARCHITECTURE.md#23-mlflow-model-management-pipeline) - Model registry and lifecycle
- [MLOps Automation](./SYSTEM_AND_ARCHITECTURE.md#28-mlops-automation-drift-detection-to-retraining) - Drift detection and retraining workflow
- [Notebook Training Pipeline](./SYSTEM_AND_ARCHITECTURE.md#213-notebook-training-pipeline-and-makefile-automation) - Training automation

---

## 1. Executive Summary (V1.0 Production Status)

This document details the production ML model registry with **S3 serverless model loading** achievements from Sprint 4:

1. **Revolutionary S3 Serverless Model Loading (Phase 2)**: Implemented dynamic model selection from MLflow/S3 registry with intelligent caching
2. **Cloud-Native Model Registry (Phase 1)**: All 17+ models now stored in cloud MLflow with S3 artifact storage  
3. **Enterprise-Grade Integration (Phase 2)**: Production-ready model loading in AnomalyDetectionAgent with graceful fallbacks
4. **Comprehensive Model Coverage (Phase 1)**: Extended portfolio across synthetic validation, anomaly detection, forecasting, and real-world datasets

### Sprint 4 Phase 1-2 Achievements:
- ✅ **17+ Models Registered** in cloud MLflow (exceeded original target)
- ✅ **S3 Artifact Storage** fully operational for all model artifacts  
- ✅ **Serverless Model Loading** implemented in `core/ml/model_loader.py`
- ✅ **Dynamic Model Selection** based on sensor type and metadata
- ✅ **Intelligent Caching** with 60-minute TTL for high performance
- ✅ **Multi-Domain Coverage** across 7 active experiments
- ✅ **Real-World Validation** with 5 industrial datasets (AI4I, NASA, XJTU, MIMII, Kaggle)

The platform now demonstrates **enterprise-grade ML operations** with cloud-native deployment, preparing for Phase 3 Golden Path validation and production deployment.

---

## 2. 🏆 Champion Model Portfolio (Sprint 4 Phase 1 Extended)

This section provides a comprehensive overview of all 17+ champion models registered in the **cloud MLflow Model Registry with S3 artifact storage**.

### 🚀 **Revolutionary S3 Serverless Model Loading**
- **Location**: `core/ml/model_loader.py`  
- **Capability**: Dynamic model selection from cloud MLflow based on sensor type
- **Features**: Intelligent caching (60min TTL), async-friendly design, graceful fallbacks
- **Integration**: Operational in AnomalyDetectionAgent with production-ready error handling

### 📊 **Cloud-Native Model Registry (17+ Models)**

| Model Task | Champion Model Name | Dataset Source | Key Performance Metric | S3 Storage |
| :--- | :--- | :--- | :--- | :--- |
| **Synthetic Validation** | `sensor_validation_models` | Synthetic Sensor Data | **Quality >95%** | ✅ |
| **Anomaly Detection** | `anomaly_detector_refined_v2` | Synthetic Sensor Data | **IsolationForest Ready** | ✅ |
| **Time-Series Forecasting** | `prophet_forecaster_enhanced_sensor-001` | Synthetic Sensor Data | **20.86% MAE Improvement** | ✅ |
| **Classification Baseline** | `ai4i_classifier_randomforest_baseline` | AI4I 2020 UCI | **99.9% Accuracy** | ✅ |
| **Classification Engineered** | `ai4i_classifier_engineered_features` | AI4I 2020 UCI | **Enhanced Features** | ✅ |
| **Vibration Anomaly** | `vibration_anomaly_isolationforest` | NASA IMS Bearing | **10.0% Anomaly Rate** | ✅ |
| **Vibration OneClass** | `vibration_anomaly_oneclasssvm` | NASA IMS Bearing | **SVM Alternative** | ✅ |
| **Audio Classification** | `RandomForest_MIMII_Audio_Benchmark` | MIMII Sound Dataset | **93.3% Accuracy** | ✅ |
| **Advanced Vibration** | `xjtu_bearing_models` | XJTU-SY Bearing | **Industrial Grade** | ✅ |
| **Pump Classification** | `pump_sensor_models` | Kaggle Pump Dataset | **Multi-Class** | ✅ |
| **Forecasting Tuned** | `prophet_tuned_hyperparameters` | Synthetic Time Series | **Optimized Params** | ✅ |
| **LightGBM Challenger** | `lightgbm_forecasting_model` | Synthetic Time Series | **Tree-Based** | ✅ |
| **Additional Models** | Various experiments | Multiple sources | **Coverage Expansion** | ✅ |

### 🎯 **Model Selection Intelligence**
The serverless model loader automatically selects optimal models based on:
- **Sensor Type**: Vibration, temperature, pressure, humidity, voltage
- **Model Performance**: Registered champion models prioritized  
- **Sensor ID Patterns**: Smart inference from sensor naming conventions
- **Metadata Tags**: MLflow registry tags for model organization
| **Classification** | *`pump_randomforest_baseline`* | Kaggle Pump Sensor | **100% Accuracy** |
| **Vibration Anomaly**| `xjtu_anomaly_isolation_forest` | XJTU-SY Bearing | **10.0% Anomaly Rate** |

*Note: The Kaggle Pump model should be registered from its run artifacts to formalize its champion status.*

---

## 3. Detailed Model Analysis & Comparison

This section provides a deeper dive into the outcomes of each modeling initiative.

### 3.1. Foundational Models (Synthetic Data)

#### **Time-Series Forecasting: Prophet vs. LightGBM**
* **Objective**: Forecast future sensor readings based on historical patterns.
* **Dataset**: Synthetically generated time-series data mimicking industrial sensors.
* **Analysis**: A tuned **Prophet** model was benchmarked against a **LightGBM** model that used lag features. The Prophet model demonstrated superior performance, achieving a **20.86% improvement** in Mean Absolute Error (MAE) over a naive baseline, which was **9.68% better** than the LightGBM challenger.
* **Champion**: `prophet_forecaster_enhanced_sensor-001` was declared the winner due to its higher accuracy and specialized suitability for time-series decomposition.

#### **Anomaly Detection: IsolationForest**
* **Objective**: Detect unusual or anomalous readings in sensor data streams.
* **Dataset**: Synthetically generated sensor data with injected anomalies.
* **Analysis**: An `IsolationForest` model was trained to identify outliers. The development process focused heavily on hardening the MLOps pipeline, ensuring robust data preprocessing (intelligent forward/back-filling of missing values) and reliable, containerized training execution.
* **Champion**: `anomaly_detector_refined_v2` was registered as the foundational model for the platform's Anomaly Detection Agent.

### 3.2. Project Gauntlet (Real-World Datasets)

#### **Classification Gauntlet 1: AI4I Machine Failure**
* **Objective**: Predict machine failure from tabular process data.
* **Dataset**: [AI4I 2020 UCI Dataset](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset)
* **Analysis**: Six models were benchmarked. All models, including RandomForest, SVC, and LightGBM, achieved an exceptional **99.9% accuracy**. Critically, the 27 engineered features provided no measurable improvement, indicating a performance ceiling due to the high quality and clear separability of the dataset.
* **Champion**: `ai4i_classifier_randomforest_baseline` was selected for its simplicity and top-tier F1-score, proving that complex feature engineering is not always necessary.

#### **Classification Gauntlet 2: Kaggle Pump Maintenance**
* **Objective**: Test the generalizability of the classification pipeline on a new dataset.
* **Dataset**: [Kaggle Pump Sensor Data](https://www.kaggle.com/datasets/nphantawee/pump-sensor-data)
* **Analysis**: The pipeline was applied to a new pump sensor dataset, and all models achieved a **perfect 100% accuracy**. This outstanding result further confirmed the robustness of the training workflow and the high quality of the dataset.
* **Champion**: The `RandomForest_baseline` run is the champion, delivering perfect results with the simplest feature set.

#### **Vibration Gauntlet 1: NASA Bearing Anomaly Detection**
* **Objective**: Process raw vibration signals to detect bearing anomalies.
* **Dataset**: [NASA IMS Bearing Dataset](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/)
* **Analysis**: A sophisticated signal processing pipeline was developed to extract 10 key features from the time and frequency domains (RMS, Peak-to-Peak, Kurtosis, Skewness, Crest Factor, FFT analysis with dominant frequency, spectral centroid, and high-frequency energy). The pipeline processed 20 files from 8-channel accelerometer data (4 bearings × 2 sensors) with 20kHz sampling, generating 2,880 feature windows. The `IsolationForest` model successfully identified a clear 10.0% anomaly rate, aligning with industry standards for bearing health monitoring.
* **Champion**: `vibration_anomaly_isolationforest` is the production-ready model for this task.

#### **Vibration Gauntlet 2: XJTU Run-to-Failure Analysis**
* **Objective**: Stress-test the vibration pipeline on a more complex, hierarchical dataset.
* **Dataset**: [XJTU-SY Bearing Datasets](https://biaoming.xjtu.edu.cn/szdw/list.htm)
* **Analysis**: The pipeline was successfully adapted to handle the complex multi-condition structure (35Hz12kN, 37.5Hz11kN, 40Hz10kN) and dual-channel (Horizontal/Vertical) signals of the XJTU dataset. Advanced feature extraction generated 22 features (11 per channel) from 180 CSV files across 11 unique bearing IDs, including statistical domain features (RMS, kurtosis, skewness, crest factor) and frequency domain analysis (FFT, spectral centroid, high-frequency energy). The `IsolationForest` model again proved effective with 10.0% anomaly detection, demonstrating the generalizability of our approach across different bearing datasets and operating conditions.
* **Champion**: `xjtu_anomaly_isolation_forest` is the champion for this advanced use case.

#### **Audio Gauntlet: MIMII Sound Classification**
* **Objective**: Classify machine sounds as normal or abnormal using audio processing.
* **Dataset**: [MIMII Sound Dataset](https://zenodo.org/record/3384388)
* **Analysis**: This phase validated the platform's multi-modal capabilities and required significant infrastructure hardening, including Docker build optimization (reducing contexts from 23GB to ~5MB through enhanced `.dockerignore`), multi-stage Dockerfile implementation, and resolution of complex dependency conflicts with `librosa` and system-level audio libraries. A comprehensive pipeline using `librosa` was built to process over 8,300 `.wav` files and extract MFCC (Mel-Frequency Cepstral Coefficients) features representing the unique "fingerprint" of each sound. The `RandomForestClassifier` achieved a strong **93.3% accuracy** with promising F1-Score of 0.62 for abnormal sound detection.
* **Champion**: `RandomForest_MIMII_Audio_Benchmark` and its associated `MIMII_Audio_Scaler` are the champions.

---

## 4. How to Use the MLflow Environment

The MLflow instance at `http://localhost:5000` is the central hub for all project models and experiments.

### **Navigating Experiments**
The **Experiments** tab is organized to reflect the project's history. Each of the five "Gauntlet" experiments contains all the runs, parameters, and artifacts for that phase. The descriptions have been updated to provide clear context for each.

### **Using Registered Models**
The **Models** tab contains the curated list of production-ready "champion" models.
* **Descriptions**: Each champion model has a detailed description outlining its purpose, dataset, and key performance metrics.
* **Tags**: Models are tagged for easy filtering by `Project`, `Phase`, `Task`, `Status`, and `Dataset`.
* **Deployment**: To use a model, load it from the registry by its name (e.g., `mlflow.pyfunc.load_model("models:/vibration_anomaly_isolationforest/1")`). Remember to also load any associated preprocessing artifacts, such as scalers.

---

### Intelligent, Dynamic Model Selection (Live System)

While this document summarizes the foundational models as of 2025-08-19, the live system (added on Day 21.5) selects models dynamically based on sensor type using tags read from MLflow.

- What it does: Recommends the best-suited registered models for a chosen `sensor_type` (e.g., `bearing`, `pump`, `audio`, `vibration`, `temperature`). General-purpose models can be included as fallback.
- Where it lives:
	- Logic: `apps/ml/model_utils.py`
		- `get_all_registered_models()` — lists registered models with model- and version-level tags
		- `get_models_by_sensor_type()` — groups models by `sensor_type` tag (checks version tags first, then model tags; untagged models go to `general`)
		- `get_model_recommendations(sensor_type, include_general=True)` — returns an ordered, de-duplicated recommendation list
		- `suggest_sensor_types()` — returns available types (union of tagged types plus helpful defaults)
		- `add_sensor_type_tag(model_name, version, sensor_type)` — helper to tag versions programmatically
	- UI: `ui/streamlit_app.py` under the "Intelligent Model Selection" section. Users pick a sensor type, the UI calls the utilities above to show recommendations, and then pipes the selection into the prediction interface. It also supports manual selection and sensible fallbacks if MLflow is unavailable.
- How it works: The utilities query the MLflow Model Registry and read the `sensor_type` tag from model version tags first (most specific) and then model-level tags. Recommendations include specific matches first and optionally add `general` models.
- Configuration: The MLflow tracking server is taken from `MLFLOW_TRACKING_URI` (default `http://mlflow:5000`). Ensure this environment variable points to your MLflow instance used by the UI/backend.
- Tagging models: Tag via the MLflow UI or programmatically, e.g.:

```python
from apps.ml.model_utils import add_sensor_type_tag
add_sensor_type_tag("vibration_anomaly_isolationforest", "1", "vibration")
```

This dynamic selection means the system’s “current best” models are sourced live from MLflow based on tags, while this document serves as a stable summary of the original champion portfolio.

---

## 5. Final Conclusion & Next Steps

This R&D sprint has been a resounding success. We have systematically proven the platform's ability to tackle a wide range of real-world predictive maintenance challenges across multiple data modalities (tabular, vibration signals, audio streams, and time-series). The infrastructure has been significantly hardened through comprehensive Docker optimization, dependency resolution, and multi-stage containerization. The MLOps workflow is robust with complete experiment tracking, model versioning, and artifact management through MLflow.

**Key Technical Achievements:**

- **Multi-Modal Processing**: Successful implementation of tabular classification, signal processing (time/frequency domain features), audio analysis (MFCC extraction), and time-series forecasting
- **Production-Ready Pipeline**: Docker-based training with papermill execution, MLflow integration, and automated artifact generation
- **Infrastructure Hardening**: Build optimization reducing contexts by 99.9%, dependency conflict resolution, and containerized reproducibility
- **Industrial Validation**: Models align with bearing fault detection physics, audio anomaly patterns, and maintenance decision-making processes

The project is now officially ready to move forward with the original 30-day plan, beginning with the **Day 11 tasks: MLflow Registry Integration and Loader implementation**. The `PROJECT_GAUNTLET_PLAN.md` file can now be safely deleted as all objectives have been successfully completed and documented.
