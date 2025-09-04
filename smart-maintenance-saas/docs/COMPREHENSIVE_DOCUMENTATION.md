# Comprehensive System Documentation

## 1. Introduction

This document provides a comprehensive overview of the production-ready system architecture for the Smart Maintenance SaaS platform. The platform is a cloud-native, event-driven system that delivers scalable, resilient predictive maintenance solutions for industrial applications.

### 1.1. Project Achievement Summary

The system has successfully completed a 30-day sprint (August 2025) delivering:

- **Production-Ready Performance:** 103.8 RPS peak throughput with sub-3ms response times
- **Comprehensive ML Pipeline:** 17+ production models across classification, anomaly detection, and forecasting
- **Real-World Dataset Validation:** 5 industrial datasets successfully integrated (AI4I, NASA, XJTU, MIMII, Kaggle)
- **Event-Driven Architecture:** Custom high-performance event bus with retry logic and dead letter queues
- **Time-Series Database:** Optimized TimescaleDB with continuous aggregates and indexing
- **MLflow Integration:** Complete model lifecycle management with artifact storage and registry
- **Security Hardening:** API rate limiting, vulnerability scanning, and comprehensive security audit framework

---

## 2. System Architecture

The architecture is designed around a multi-agent system where specialized agents perform specific tasks. These agents communicate asynchronously through an **Event Bus**, creating a decoupled and highly scalable system.

### 2.1. High-Level System Overview

```mermaid
graph TB
    subgraph "External Systems"
        IOT[Industrial IoT Sensors]
        USERS[Users/Dashboard]
        MOBILE[Mobile Applications]
    end

    subgraph "API Layer"
        LB[Load Balancer]
        API[FastAPI Gateway]
        AUTH[Authentication & Rate Limiting]
        METRICS[Prometheus Metrics]
    end

    subgraph "Core Processing"
        COORD[System Coordinator]
        EVENT[Event Bus with Retry Logic]
        AGENTS[Multi-Agent System]
    end

    subgraph "Data Layer"
        TS[(TimescaleDB with Continuous Aggregates)]
        REDIS[(Redis Cache & Sessions)]
        MLFLOW[(MLflow Model Registry)]
    end

    subgraph "Infrastructure"
        DOCKER[Docker Containerized Services]
        MONITOR[Health Monitoring]
        LOGS[Centralized Logging]
        SECURITY[Security Scanning]
    end

    IOT --> LB
    USERS --> LB
    MOBILE --> LB
    LB --> API
    API --> AUTH
    AUTH --> COORD
    COORD --> EVENT
    EVENT --> AGENTS
    AGENTS --> TS
    AGENTS --> REDIS
    AGENTS --> MLFLOW
    COORD --> DOCKER
    AGENTS --> MONITOR
    EVENT --> LOGS
    API --> METRICS
    API --> SECURITY

    classDef external fill:#e1f5fe
    classDef api fill:#f3e5f5
    classDef core fill:#e8f5e8
    classDef data fill:#fff3e0
    classDef infra fill:#fce4ec

    class IOT,USERS,MOBILE external
    class LB,API,AUTH,METRICS api
    class COORD,EVENT,AGENTS core
    class TS,REDIS,MLFLOW data
    class DOCKER,MONITOR,LOGS,SECURITY infra
```

### 2.2. Production Event-Driven Architecture Flow

```mermaid
sequenceDiagram
    participant API as FastAPI Gateway
    participant AUTH as Rate Limiter
    participant EB as Event Bus
    participant DA as Data Acquisition
    participant AD as Anomaly Detection
    participant ML as MLflow Models
    participant TS as TimescaleDB
    participant REDIS as Redis Cache

    API->>+AUTH: Request with API Key
    AUTH->>AUTH: Rate Limit Check (10/min for ML endpoints)
    AUTH->>+EB: Authenticated Event
    EB->>+DA: DataIngestionEvent
    DA->>TS: Store Sensor Data
    DA->>-EB: DataProcessedEvent
    EB->>+AD: Process with IsolationForest
    AD->>ML: Load Model from Registry
    ML->>AD: Model Artifacts
    AD->>REDIS: Cache Results
    AD->>-EB: AnomalyDetectedEvent
    EB->>TS: Store Analysis Results
    EB->>-API: Response with Correlation ID
    AUTH->>-API: JSON Response
```

### 2.3. MLflow Model Management Pipeline

```mermaid
flowchart LR
    subgraph "Model Training"
        NOTEBOOKS[Jupyter Notebooks]
        DATASETS[Real-World Datasets]
        TRAINING[Model Training Pipeline]
    end

    subgraph "MLflow Registry"
        REGISTRY[Model Registry]
        ARTIFACTS[Artifact Storage]
        VERSIONING[Model Versioning]
        METADATA[Experiment Metadata]
    end

    subgraph "Production Deployment"
        LOADER[Model Loader]
        CACHE[Model Cache]
        INFERENCE[Real-time Inference]
        MONITORING[Model Monitoring]
    end

    subgraph "Data Sources"
        AI4I[AI4I Industrial Dataset]
        NASA[NASA Bearing Dataset]
        XJTU[XJTU Bearing Dataset]
        MIMII[MIMII Audio Dataset]
        KAGGLE[Kaggle Pump Dataset]
    end

    AI4I --> DATASETS
    NASA --> DATASETS
    XJTU --> DATASETS
    MIMII --> DATASETS
    KAGGLE --> DATASETS

    DATASETS --> NOTEBOOKS
    NOTEBOOKS --> TRAINING
    TRAINING --> REGISTRY
    REGISTRY --> ARTIFACTS
    REGISTRY --> VERSIONING
    REGISTRY --> METADATA

    REGISTRY --> LOADER
    LOADER --> CACHE
    CACHE --> INFERENCE
    INFERENCE --> MONITORING

    classDef training fill:#e3f2fd
    classDef registry fill:#e8f5e8
    classDef deployment fill:#fff3e0
    classDef data fill:#f3e5f5

    class NOTEBOOKS,DATASETS,TRAINING training
    class REGISTRY,ARTIFACTS,VERSIONING,METADATA registry
    class LOADER,CACHE,INFERENCE,MONITORING deployment
    class AI4I,NASA,XJTU,MIMII,KAGGLE data
```

### 2.4. TimescaleDB Performance Architecture

```mermaid
graph TD
    subgraph "Data Ingestion Layer"
        API_INGEST[API Ingestion Endpoint]
        VALIDATION[Data Validation]
        TRANSFORM[Data Transformation]
    end

    subgraph "TimescaleDB Core"
        HYPERTABLE[sensor_readings Hypertable]
        COMPRESSION[Automatic Compression]
        PARTITIONING[Time-based Partitioning]
    end

    subgraph "Performance Optimization"
        CONT_AGG[Continuous Aggregates]
        INDEXES[Optimized Indexes]
        RETENTION[Retention Policies]
    end

    subgraph "Query Performance"
        HOURLY_VIEW[Hourly Summary Views]
        SENSOR_INDEX[Sensor-Time Index]
        TIME_INDEX[Time Range Index]
    end

    API_INGEST --> VALIDATION
    VALIDATION --> TRANSFORM
    TRANSFORM --> HYPERTABLE

    HYPERTABLE --> COMPRESSION
    HYPERTABLE --> PARTITIONING
    HYPERTABLE --> CONT_AGG

    CONT_AGG --> HOURLY_VIEW
    INDEXES --> SENSOR_INDEX
    INDEXES --> TIME_INDEX

    COMPRESSION --> RETENTION
    PARTITIONING --> INDEXES

    classDef ingestion fill:#e1f5fe
    classDef core fill:#e8f5e8
    classDef optimization fill:#fff3e0
    classDef performance fill:#f3e5f5

    class API_INGEST,VALIDATION,TRANSFORM ingestion
    class HYPERTABLE,COMPRESSION,PARTITIONING core
    class CONT_AGG,INDEXES,RETENTION optimization
    class HOURLY_VIEW,SENSOR_INDEX,TIME_INDEX performance
```

### 2.5. Production Performance Metrics Flow

```mermaid
flowchart TB
    subgraph "Load Testing"
        LOCUST[Locust Load Generator]
        CONCURRENT[50 Concurrent Users]
        DURATION[3 Minute Tests]
    end

    subgraph "Performance Results"
        THROUGHPUT[103.8 RPS Peak]
        LATENCY[P95: 2ms, P99: 3ms]
        STABILITY[100% Uptime]
        RESOURCE[6% CPU Usage]
    end

    subgraph "Monitoring Stack"
        PROMETHEUS[Prometheus Metrics]
        HEALTH[Health Endpoints]
        LOGS[Structured Logging]
        ALERTS[Performance Alerts]
    end

    subgraph "Infrastructure Stats"
        API_CONTAINER[API: 0.07% CPU]
        DB_CONTAINER[Database: 2.43% CPU]
        REDIS_CONTAINER[Redis: 5.61% CPU]
        MEMORY[Memory: <1GB Total]
    end

    LOCUST --> CONCURRENT
    CONCURRENT --> DURATION
    DURATION --> THROUGHPUT
    THROUGHPUT --> LATENCY
    LATENCY --> STABILITY
    STABILITY --> RESOURCE

    THROUGHPUT --> PROMETHEUS
    LATENCY --> HEALTH
    STABILITY --> LOGS
    RESOURCE --> ALERTS

    PROMETHEUS --> API_CONTAINER
    HEALTH --> DB_CONTAINER
    LOGS --> REDIS_CONTAINER
    ALERTS --> MEMORY

    classDef testing fill:#e3f2fd
    classDef results fill:#e8f5e8
    classDef monitoring fill:#fff3e0
    classDef infrastructure fill:#f3e5f5

    class LOCUST,CONCURRENT,DURATION testing
    class THROUGHPUT,LATENCY,STABILITY,RESOURCE results
    class PROMETHEUS,HEALTH,LOGS,ALERTS monitoring
    class API_CONTAINER,DB_CONTAINER,REDIS_CONTAINER,MEMORY infrastructure
```

---
## 3. Core Components

The architecture is implemented as a containerized, event-driven system optimized for high-performance industrial IoT data processing.

### 3.1. Core Technology Stack

#### API Layer
- **FastAPI 0.104.1** with Starlette-compatible dependencies
- **Prometheus metrics integration** via `prometheus-fastapi-instrumentator`
- **API rate limiting** (10 requests/minute for ML endpoints)
- **Request correlation IDs** for distributed tracing
- **Idempotency support** with TTL-based deduplication (10-minute cache)
- **Structured JSON logging** with correlation ID propagation
- **Health endpoints** (`/health`, `/health/db`, `/metrics`)

#### Data Layer
- **PostgreSQL with TimescaleDB 2.11+** optimized for time-series data
- **Redis 7.0+** for caching and session management
- **MLflow Model Registry** with SQLite backend and artifact storage
- **Continuous aggregates** for real-time analytics performance
- **Automatic data compression** and retention policies

#### Event Processing
- **Custom Event Bus** with exponential backoff retry logic
- **Dead Letter Queue (DLQ)** for failed event handling
- **Asynchronous processing** with correlation ID propagation
- **Event persistence** with comprehensive audit trails

---
## 4. Multi-Agent System

The platform implements a sophisticated multi-agent architecture for specialized task handling:

### 4.1. Core Agents

| Agent | Function | Implementation Status |
|-------|----------|----------------------|
| **DataAcquisitionAgent** | Sensor data ingestion, validation, and enrichment | ✅ Production Ready |
| **AnomalyDetectionAgent** | ML-based anomaly detection using IsolationForest | ✅ Production Ready |
| **ValidationAgent** | Rule-based anomaly validation and false positive reduction | ✅ Production Ready |
| **OrchestratorAgent** | Workflow coordination and decision routing | ✅ Production Ready |
| **PredictionAgent** | Prophet-based time-series forecasting | ✅ Production Ready |
| **SchedulingAgent** | Maintenance task scheduling optimization | ✅ Production Ready |
| **NotificationAgent** | Multi-channel notification dispatch | ✅ Production Ready |
| **ReportingAgent** | Analytics and insights generation | ✅ Production Ready |
| **HumanInterfaceAgent** | Human-in-the-loop decision management | ✅ Production Ready |
| **LearningAgent** | RAG-based system improvement with ChromaDB | ✅ Production Ready |
| **MaintenanceLogAgent** | Maintenance history tracking and persistence | ✅ Production Ready |
| **DriftMonitoringAgent** | Real-time model performance tracking and drift detection | ✅ Production Ready |
| **ChaosEngineeringAgent** | System resilience testing and failure simulation | ✅ Production Ready |
| **ModelSelectionAgent** | Intelligent model routing and performance optimization | ✅ Production Ready |

### 4.2. Agent Communication Pattern

```mermaid
graph LR
    DA[Data Acquisition Agent] --> EB[Event Bus]
    EB --> AD[Anomaly Detection Agent]
    AD --> EB
    EB --> VA[Validation Agent]
    VA --> EB
    EB --> OA[Orchestrator Agent]
    OA --> EB
    EB --> PA[Prediction Agent]
    PA --> EB
    EB --> SA[Scheduling Agent]
    SA --> EB
    EB --> NA[Notification Agent]
    NA --> EB
    EB --> RA[Reporting Agent]
    RA --> EB
    EB --> HIA[Human Interface Agent]
    HIA --> EB
    EB --> LA[Learning Agent]
    LA --> EB
    EB --> MLA[Maintenance Log Agent]

    classDef agent fill:#e8f5e8
    classDef eventbus fill:#f3e5f5

    class DA,AD,VA,OA,PA,SA,NA,RA,HIA,LA,MLA agent
    class EB eventbus
```

---
## 5. Machine Learning Pipeline

### 5.1. Model Registry Status
- **Total Models:** 17+ production-ready models
- **Classification Models:** AI4I (99.90% accuracy), Kaggle Pump (100% accuracy)
- **Anomaly Detection:** NASA Bearing (72.8% accuracy), XJTU Bearing
- **Audio Processing:** MIMII Sound (93.3% accuracy)
- **Forecasting Models:** Prophet-based time-series prediction
- **Drift Monitoring:** Real-time model performance tracking and automated alerts
- **Intelligent Model Selection:** Context-aware model routing with performance optimization
- **Automated Retraining:** Event-driven pipeline for model updates based on drift detection

### 5.2. Model Categories

```mermaid
graph TD
    subgraph "Classification Models"
        AI4I[AI4I Industrial Failure - 99.90%]
        PUMP[Kaggle Pump Maintenance - 100%]
        MULTI[Multi-class Variants]
    end

    subgraph "Anomaly Detection"
        NASA[NASA Bearing Vibration - 72.8%]
        XJTU[XJTU Bearing Analysis]
        ISOLATION[Isolation Forest Ensemble]
    end

    subgraph "Signal Processing"
        VIBRATION[Vibration Signal Analysis]
        AUDIO[MIMII Audio - 93.3%]
        FFT[FFT Feature Extraction]
    end

    subgraph "Forecasting"
        PROPHET[Prophet Time Series]
        SEASONAL[Seasonal Decomposition]
        TREND[Trend Analysis]
    end

    classDef classification fill:#e3f2fd
    classDef anomaly fill:#e8f5e8
    classDef signal fill:#fff3e0
    classDef forecast fill:#f3e5f5

    class AI4I,PUMP,MULTI classification
    class NASA,XJTU,ISOLATION anomaly
    class VIBRATION,AUDIO,FFT signal
    class PROPHET,SEASONAL,TREND forecast
```

### 5.3. Drift Monitoring System

The system implements comprehensive model drift detection and automated response:

```mermaid
graph TD
    subgraph "Drift Detection Pipeline"
        MONITOR[Drift Monitoring Agent]
        DETECT[Statistical Drift Detection]
        ALERT[Alert Generation]
        RETRAIN[Automated Retraining]
    end

    subgraph "Intelligent Model Selection"
        ROUTER[Model Router]
        PERF[Performance Tracker]
        SELECT[Context-Aware Selection]
    end

    MONITOR --> DETECT
    DETECT --> ALERT
    ALERT --> RETRAIN
    ROUTER --> PERF
    PERF --> SELECT
    SELECT --> MONITOR
```

**Key Features:**
- **Real-time Performance Tracking:** Continuous monitoring of model accuracy and prediction quality
- **Statistical Drift Detection:** Automated detection of data distribution changes
- **Event-driven Retraining:** Automatic model updates triggered by drift alerts
- **Model Performance Comparison:** Intelligent routing based on real-time performance metrics
- **Notification System:** Integration with system event bus for drift alerts

---
## 6. Security and Operational Excellence

### 6.1. Security Implementation

#### API Security
- **Rate Limiting:** 10 requests/minute for compute-intensive ML endpoints
- **Authentication:** API key validation with secure header handling
- **DoS Protection:** Computational resource limiting for expensive operations
- **Input Validation:** Comprehensive request validation and sanitization

#### Infrastructure Security
- **Container Isolation:** Docker-based service separation
- **Dependency Scanning:** Snyk integration for vulnerability detection
- **Security Auditing:** Comprehensive security audit checklist framework
- **Automated Scanning:** CI/CD pipeline security integration

### 6.2. Monitoring and Observability

#### Metrics Collection
- **Prometheus Integration:** HTTP request metrics, latency distributions
- **Health Endpoints:** `/health`, `/health/db`, `/metrics` endpoints
- **Process Metrics:** Memory usage, file descriptors, CPU utilization
- **Custom Metrics:** ML model load times, prediction latencies

#### Logging Architecture
- **Structured JSON Logging:** Centralized log aggregation
- **Correlation IDs:** Request tracing across service boundaries
- **Event Audit Trails:** Complete event processing history
- **Error Tracking:** Comprehensive error logging with stack traces

---
## 7. Performance Benchmarks and Scaling

### 7.1. Current Performance Baseline

#### Response Time Performance
- **P50 Response Time:** 1ms (50th percentile)
- **P95 Response Time:** 2ms (95th percentile)
- **P99 Response Time:** 3ms (99th percentile)
- **Maximum Response Time:** 124ms (well below 200ms SLO)

#### Throughput Capabilities
- **Peak Throughput:** 103.8 RPS sustained
- **Average Throughput:** 88.83 RPS over 3-minute test
- **Event Processing:** >100 events/second capability validated
- **Database Throughput:** Optimized for high-frequency time-series ingestion

### 7.2. Scalability Analysis

#### Horizontal Scaling Potential
- **CPU Utilization:** Current 6% usage indicates 16x scaling potential
- **Memory Efficiency:** <1GB total usage allows for significant scaling
- **Database Performance:** TimescaleDB optimized for multi-tenant scaling
- **Event Bus Capacity:** Custom implementation designed for high throughput

---
## 8. Data Flow and Integration

### 8.1. Data Pipeline Architecture

```mermaid
flowchart LR
    subgraph "Data Sources"
        SENSORS[IoT Sensors]
        BATCH[Batch Imports]
        EXTERNAL[External APIs]
    end

    subgraph "Ingestion Layer"
        VALIDATE[Schema Validation]
        ENRICH[Data Enrichment]
        CORRELATION[ID Assignment]
    end

    subgraph "Processing Layer"
        EVENT_BUS[Event Bus]
        ML_PIPELINE[ML Processing]
        BUSINESS_RULES[Business Logic]
    end

    subgraph "Storage Layer"
        TIMESERIES[TimescaleDB]
        CACHE[Redis Cache]
        ARTIFACTS[MLflow Artifacts]
    end

    SENSORS --> VALIDATE
    BATCH --> VALIDATE
    EXTERNAL --> VALIDATE

    VALIDATE --> ENRICH
    ENRICH --> CORRELATION
    CORRELATION --> EVENT_BUS

    EVENT_BUS --> ML_PIPELINE
    EVENT_BUS --> BUSINESS_RULES

    ML_PIPELINE --> TIMESERIES
    ML_PIPELINE --> CACHE
    ML_PIPELINE --> ARTIFACTS

    BUSINESS_RULES --> TIMESERIES
    BUSINESS_RULES --> CACHE

    classDef sources fill:#e1f5fe
    classDef ingestion fill:#e8f5e8
    classDef processing fill:#fff3e0
    classDef storage fill:#f3e5f5

    class SENSORS,BATCH,EXTERNAL sources
    class VALIDATE,ENRICH,CORRELATION ingestion
    class EVENT_BUS,ML_PIPELINE,BUSINESS_RULES processing
    class TIMESERIES,CACHE,ARTIFACTS storage
```

### 8.2. Real-World Dataset Integration

The system has been validated against diverse industrial datasets:

#### Dataset Portfolio
- **AI4I 2020 UCI Dataset:** Industrial machine failure classification
- **NASA IMS Bearing Dataset:** Vibration signal anomaly detection
- **XJTU-SY Bearing Dataset:** Advanced run-to-failure analysis
- **MIMII Sound Dataset:** Audio-based anomaly detection
- **Kaggle Pump Sensor Data:** Maintenance prediction classification

---
## 9. Getting Started

```bash
git clone <repo>
cd enterprise_challenge_sprint_1_hermes_reply
docker compose up -d --build
# API:        http://localhost:8000/docs
# UI:         http://localhost:8501
# MLflow:     http://localhost:5000
# Metrics:    http://localhost:8000/metrics
```

Stop (preserve volumes):
```bash
docker compose down
```

Run migrations manually (intentional design – see Migration Strategy):
```bash
docker compose exec api alembic upgrade heads
```

---
## 10. API Reference

For detailed API documentation, please see the [API Reference](./api.md).
