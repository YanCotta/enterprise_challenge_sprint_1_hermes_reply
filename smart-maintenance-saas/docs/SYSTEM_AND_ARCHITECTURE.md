# Smart Maintenance SaaS - System and Architecture

# Smart Maintenance SaaS - Complete Documentation Index

## Core Documentation

### Getting Started

- **[Main README](../../README.md)** - Project overview, quick start, and repository structure
- **[Backend README](../README.md)** - Docker deployment and getting started guide
- **[Development Orientation](../../DEVELOPMENT_ORIENTATION.md)** - Development guidelines and best practices

### Project History & Changelog

- **[30-Day Sprint Changelog](../../30-day-sprint-changelog.md)** - Complete development history and daily progress
- **[Final Sprint Summary](../../final_30_day_sprint.md)** - Executive summary of sprint achievements

## System Architecture & Design

### Architecture Documentation

- **[System and Architecture](./SYSTEM_AND_ARCHITECTURE.md)** - Comprehensive system architecture and design patterns
- **[System Screenshots](./SYSTEM_SCREENSHOTS.md)** - Visual documentation of system interfaces
- **[Comprehensive System Analysis](./COMPREHENSIVE_SYSTEM_ANALYSIS_REPORT.md)** - Detailed technical analysis report
- **[Microservice Migration Strategy](./MICROSERVICE_MIGRATION_STRATEGY.md)** - Future architecture evolution plans

### Database Design

- **[Database Documentation](./db/README.md)** - Database schema and design documentation
- **[Database ERD](./db/erd.dbml)** - Entity Relationship Diagram source
- **[Database Schema](./db/schema.sql)** - Complete SQL schema definition

## API & Integration

### API Documentation

- **[API Reference](./api.md)** - Complete REST API documentation and examples
- **[Configuration Management](../core/config/README.md)** - Centralized configuration system
- **[Logging Configuration](../core/logging_config.md)** - Structured JSON logging setup

## Performance & Testing

### Performance Documentation

- **[Performance Baseline](./PERFORMANCE_BASELINE.md)** - Performance metrics and SLO targets
- **[Day 17 Load Test Report](./DAY_17_LOAD_TEST_REPORT.md)** - Comprehensive load testing results (103.8 RPS)
- **[Day 18 Performance Results](./DAY_18_PERFORMANCE_RESULTS.md)** - TimescaleDB optimization results
- **[Load Testing Instructions](./LOAD_TESTING_INSTRUCTIONS.md)** - Guide for running performance tests

### Testing Documentation

- **[Test Documentation](../tests/README.md)** - Test organization and execution guide
- **[Coverage Improvement Plan](./COVERAGE_IMPROVEMENT_PLAN.md)** - Test coverage strategy and current status

## Machine Learning & Data Science

### ML Documentation

- **[ML Documentation](./ml/README.md)** - Machine learning models and pipelines
- **[Models Summary](./MODELS_SUMMARY.md)** - Overview of all 17+ production models
- **[Project Gauntlet Plan](./PROJECT_GAUNTLET_PLAN.md)** - Real-world dataset integration execution

## Security & Operations

### Security Documentation

- **[Security Documentation](./SECURITY.md)** - Security architecture and implementation
- **[Security Audit Checklist](./SECURITY_AUDIT_CHECKLIST.md)** - Comprehensive security audit framework

---

*This index is automatically maintained and appears at the top of all documentation files for easy navigation.*

---

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

## 2. System Architecture Visualizations

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
    DA->>EB: DataProcessedEvent
    EB->>+AD: Process with IsolationForest
    AD->>ML: Load Model from Registry
    ML->>AD: Model Artifacts
    AD->>REDIS: Cache Results
    AD->>EB: AnomalyDetectedEvent
    EB->>TS: Store Analysis Results
    EB->>API: Response with Correlation ID
    API->>-AUTH: JSON Response
    AUTH->>-API: Rate Limited Response
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

## 3. Production System Architecture

The architecture is implemented as a containerized, event-driven system optimized for high-performance industrial IoT data processing.

### 3.1. Core Technology Stack

#### API Layer
- **FastAPI 0.104.1** with Starlette-compatible dependencies
- **Prometheus metrics integration** via `prometheus-fastapi-instrumentator`
- **API rate limiting** (10 requests/minute for ML endpoints)
- **Request correlation IDs** for distributed tracing
- **Idempotency support** with TTL-based deduplication

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

### 3.2. Performance Characteristics

#### Load Testing Results (Day 17)
- **Peak Throughput:** 103.8 RPS with 50 concurrent users
- **Response Times:** P50: 1ms, P95: 2ms, P99: 3ms
- **Resource Efficiency:** <6% CPU usage across all containers
- **Memory Usage:** <1GB total across entire stack
- **Stability:** 100% uptime during 3-minute sustained load tests

#### Database Performance
- **TimescaleDB Optimization:** 37.3% performance improvement via indexing
- **Continuous Aggregates:** Real-time hourly summaries for ML queries
- **Query Optimization:** Composite indexes for sensor-time range queries
- **Compression:** Automatic compression for data older than 7 days

### 3.3. Multi-Agent System

The platform implements a sophisticated multi-agent architecture for specialized task handling:

#### Core Agents

| Agent | Function | Implementation Status |
|-------|----------|----------------------|
| **DataAcquisitionAgent** | Sensor data ingestion, validation, and enrichment | Production Ready |
| **AnomalyDetectionAgent** | ML-based anomaly detection using IsolationForest | Production Ready |
| **ValidationAgent** | Rule-based anomaly validation and false positive reduction | Production Ready |
| **OrchestratorAgent** | Workflow coordination and decision routing | Production Ready |
| **PredictionAgent** | Prophet-based time-series forecasting | Production Ready |
| **SchedulingAgent** | Maintenance task scheduling optimization | Core Implementation |
| **NotificationAgent** | Multi-channel notification dispatch | Core Implementation |
| **ReportingAgent** | Analytics and insights generation | Core Implementation |
| **LearningAgent** | RAG-based system improvement | Core Implementation |
| **MaintenanceLogAgent** | Maintenance history tracking | Core Implementation |

#### Agent Communication Pattern

```mermaid
graph LR
    DA[Data Acquisition] --> EB[Event Bus]
    EB --> AD[Anomaly Detection]
    AD --> EB
    EB --> VA[Validation Agent]
    VA --> EB
    EB --> OA[Orchestrator]
    OA --> EB
    EB --> PA[Prediction Agent]
    PA --> EB
    EB --> SA[Scheduling Agent]

    classDef agent fill:#e8f5e8
    classDef eventbus fill:#f3e5f5

    class DA,AD,VA,OA,PA,SA agent
    class EB eventbus
```

### 3.4. Machine Learning Pipeline

#### Model Registry Status
- **Total Models:** 17+ production-ready models
- **Classification Models:** AI4I (99.90% accuracy), Kaggle Pump (100% accuracy)
- **Anomaly Detection:** NASA Bearing (72.8% accuracy), XJTU Bearing
- **Audio Processing:** MIMII Sound (93.3% accuracy)
- **Forecasting Models:** Prophet-based time-series prediction

#### Model Categories

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

---

## 4. Security and Operational Excellence

### 4.1. Security Implementation

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

### 4.2. Monitoring and Observability

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

### 4.3. Deployment Architecture

#### Container Architecture
```yaml
services:
  api:          # FastAPI application server
  db:           # PostgreSQL with TimescaleDB
  redis:        # Cache and session storage
  mlflow:       # Model registry and tracking
  ui:           # Web interface (if applicable)
  notebook_runner: # Jupyter execution environment
```

#### Resource Allocation
- **API Container:** 300MB memory limit, optimized for request handling
- **Database Container:** 1GB memory, SSD storage for time-series data
- **Redis Container:** 100MB memory, in-memory caching optimization
- **MLflow Container:** 500MB memory, artifact storage management

---

## 5. Performance Benchmarks and Scaling

### 5.1. Current Performance Baseline

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

### 5.2. Scalability Analysis

#### Horizontal Scaling Potential
- **CPU Utilization:** Current 6% usage indicates 16x scaling potential
- **Memory Efficiency:** <1GB total usage allows for significant scaling
- **Database Performance:** TimescaleDB optimized for multi-tenant scaling
- **Event Bus Capacity:** Custom implementation designed for high throughput

#### Performance Optimization Opportunities
- **Connection Pooling:** Database connection optimization
- **Caching Strategies:** Redis-based model and result caching
- **Async Processing:** Event-driven asynchronous workload distribution
- **Load Balancing:** Multi-replica deployment with load distribution

---

## 6. Data Flow and Integration

### 6.1. Data Pipeline Architecture

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

### 6.2. Real-World Dataset Integration

The system has been validated against diverse industrial datasets:

#### Dataset Portfolio
- **AI4I 2020 UCI Dataset:** Industrial machine failure classification
- **NASA IMS Bearing Dataset:** Vibration signal anomaly detection  
- **XJTU-SY Bearing Dataset:** Advanced run-to-failure analysis
- **MIMII Sound Dataset:** Audio-based anomaly detection
- **Kaggle Pump Sensor Data:** Maintenance prediction classification

#### Processing Capabilities
- **Tabular Data:** High-performance classification with 99%+ accuracy
- **Vibration Signals:** FFT analysis with statistical feature engineering
- **Audio Processing:** MFCC feature extraction for machine sound analysis
- **Time Series:** Prophet-based forecasting with seasonal decomposition

---

## 7. System Evolution and Architecture Decisions

### 7.1. Architectural Trade-offs Made

#### Event Bus Implementation
**Decision:** Custom in-memory event bus instead of Apache Kafka
**Rationale:** Reduced operational complexity while maintaining event-driven benefits
**Result:** High-performance, low-latency event processing with retry logic

#### MLflow Integration
**Decision:** File-based artifact storage with SQLite registry
**Rationale:** Simplified deployment without requiring external object storage
**Result:** Complete model lifecycle management with container-native storage

#### Database Choice
**Decision:** PostgreSQL with TimescaleDB extension
**Rationale:** Combines relational capabilities with time-series optimization
**Result:** 37.3% performance improvement through continuous aggregates

### 7.2. Future Architecture Considerations

#### Scaling Enhancements
- **Redis Cluster:** Multi-node caching for horizontal scaling
- **Database Sharding:** Multi-tenant data partitioning strategies  
- **Event Bus Evolution:** Migration to Apache Kafka for massive scale
- **Microservice Decomposition:** Agent-based service extraction

#### Advanced Features
- **Real-time Streaming:** Apache Kafka or Redis Streams integration
- **Advanced Analytics:** Apache Spark for large-scale data processing
- **Edge Computing:** Agent deployment on edge devices
- **Multi-region Deployment:** Geographic distribution for latency optimization

---

## 8. Conclusion

The Smart Maintenance SaaS platform represents a production-ready, event-driven architecture optimized for industrial IoT applications. With proven performance characteristics exceeding SLO requirements by orders of magnitude and comprehensive ML capabilities validated against real-world datasets, the system demonstrates enterprise-grade reliability and scalability.

The platform's success in achieving 103.8 RPS throughput with sub-3ms response times, combined with its comprehensive security framework and operational excellence practices, positions it as a robust foundation for industrial predictive maintenance applications.

Key architectural strengths include the custom event bus design for low-latency processing, TimescaleDB optimization for time-series performance, comprehensive MLflow integration for model lifecycle management, and containerized deployment for operational simplicity.

### 🔄 2.2. Agent Interaction Flow Diagram

```mermaid
sequenceDiagram
    participant API as API Gateway
    participant DAA as Data Acquisition
    participant EB as Event Bus
    participant ADA as Anomaly Detection
    participant VA as Validation Agent
    participant OA as Orchestrator
    participant PA as Prediction Agent
    participant SA as Scheduling Agent
    participant NA as Notification Agent
    participant MLA as Maintenance Log

    API->>+DAA: Sensor Data
    DAA->>DAA: Validate & Enrich
    DAA->>EB: DataProcessedEvent
    EB->>+ADA: Process Data
    ADA->>ADA: ML Analysis
    ADA->>EB: AnomalyDetectedEvent
    EB->>+VA: Validate Anomaly
    VA->>VA: Apply Rules & Context
    VA->>EB: AnomalyValidatedEvent
    EB->>+OA: Orchestrate Decision
    OA->>OA: Decision Logic
    OA->>EB: TriggerPredictionEvent
    EB->>+PA: Generate Prediction
    PA->>PA: Prophet Analysis
    PA->>EB: MaintenancePredictedEvent
    EB->>+SA: Schedule Maintenance
    SA->>SA: Optimize Schedule
    SA->>EB: MaintenanceScheduledEvent
    EB->>+NA: Send Notifications
    NA->>NA: Multi-channel Notify
    EB->>+MLA: Log Maintenance
    MLA->>MLA: Record History
```

### 🌊 2.3. Data Pipeline Architecture

```mermaid
flowchart LR
    subgraph "Data Ingestion"
        SENSORS[📡 IoT Sensors]
        API_IN[🔌 API Endpoints]
        BATCH[📦 Batch Import]
    end

    subgraph "Processing Pipeline"
        VALIDATE[✅ Data Validation]
        ENRICH[🔄 Data Enrichment]
        NORMALIZE[⚖️ Normalization]
        ANOMALY[🔍 Anomaly Detection]
    end

    subgraph "Storage & Analytics"
        TIMESERIES[(⏰ Time Series DB)]
        VECTOR[(🧠 Vector DB)]
        WAREHOUSE[(🏢 Data Warehouse)]
        CACHE[(⚡ Cache Layer)]
    end

    subgraph "Machine Learning"
        TRAIN[🎓 Model Training]
        PREDICT[🔮 Predictions]
        FEEDBACK[🔄 Feedback Loop]
    end

    subgraph "Output Systems"
        DASHBOARD[📊 Dashboards]
        ALERTS[🚨 Alerts]
        REPORTS[📈 Reports]
        API_OUT[📤 API Responses]
    end

    SENSORS --> VALIDATE
    API_IN --> VALIDATE
    BATCH --> VALIDATE
    
    VALIDATE --> ENRICH
    ENRICH --> NORMALIZE
    NORMALIZE --> ANOMALY
    
    ANOMALY --> TIMESERIES
    ANOMALY --> VECTOR
    NORMALIZE --> WAREHOUSE
    ENRICH --> CACHE
    
    TIMESERIES --> TRAIN
    VECTOR --> PREDICT
    WAREHOUSE --> FEEDBACK
    
    TRAIN --> DASHBOARD
    PREDICT --> ALERTS
    FEEDBACK --> REPORTS
    CACHE --> API_OUT

    classDef ingestion fill:#e3f2fd
    classDef processing fill:#e8f5e8
    classDef storage fill:#fff3e0
    classDef ml fill:#f3e5f5
    classDef output fill:#fce4ec

    class SENSORS,API_IN,BATCH ingestion
    class VALIDATE,ENRICH,NORMALIZE,ANOMALY processing
    class TIMESERIES,VECTOR,WAREHOUSE,CACHE storage
    class TRAIN,PREDICT,FEEDBACK ml
    class DASHBOARD,ALERTS,REPORTS,API_OUT output
```

### ⚡ 2.4. Event-Driven Architecture Flow

```mermaid
graph TD
    subgraph "Event Sources"
        DATA_IN[📊 Data Ingestion]
        USER_ACTION[👤 User Actions]
        SYSTEM_EVENT[⚙️ System Events]
        TIMER[⏰ Scheduled Tasks]
    end

    subgraph "Event Bus Core"
        ROUTER[📡 Event Router]
        QUEUE[📬 Event Queue]
        DISPATCH[🚀 Event Dispatcher]
    end

    subgraph "Event Processors"
        ANOMALY_PROC[🔍 Anomaly Processor]
        VALIDATION_PROC[✅ Validation Processor]
        PREDICTION_PROC[🔮 Prediction Processor]
        SCHEDULE_PROC[📅 Schedule Processor]
        NOTIFY_PROC[📢 Notification Processor]
    end

    subgraph "Event Persistence"
        EVENT_LOG[(📜 Event Log)]
        METRICS[(📊 Event Metrics)]
        AUDIT[(🔍 Audit Trail)]
    end

    subgraph "Event Consumers"
        DASHBOARD_SUB[📊 Dashboard Updates]
        ALERT_SUB[🚨 Alert System]
        REPORT_SUB[📈 Reporting]
        API_SUB[🔌 API Responses]
    end

    DATA_IN --> ROUTER
    USER_ACTION --> ROUTER
    SYSTEM_EVENT --> ROUTER
    TIMER --> ROUTER

    ROUTER --> QUEUE
    QUEUE --> DISPATCH

    DISPATCH --> ANOMALY_PROC
    DISPATCH --> VALIDATION_PROC
    DISPATCH --> PREDICTION_PROC
    DISPATCH --> SCHEDULE_PROC
    DISPATCH --> NOTIFY_PROC

    ANOMALY_PROC --> EVENT_LOG
    VALIDATION_PROC --> METRICS
    PREDICTION_PROC --> AUDIT
    SCHEDULE_PROC --> EVENT_LOG
    NOTIFY_PROC --> METRICS

    DISPATCH --> DASHBOARD_SUB
    DISPATCH --> ALERT_SUB
    DISPATCH --> REPORT_SUB
    DISPATCH --> API_SUB

    classDef source fill:#e1f5fe
    classDef core fill:#e8f5e8
    classDef processor fill:#f3e5f5
    classDef persistence fill:#fff3e0
    classDef consumer fill:#fce4ec

    class DATA_IN,USER_ACTION,SYSTEM_EVENT,TIMER source
    class ROUTER,QUEUE,DISPATCH core
    class ANOMALY_PROC,VALIDATION_PROC,PREDICTION_PROC,SCHEDULE_PROC,NOTIFY_PROC processor
    class EVENT_LOG,METRICS,AUDIT persistence
    class DASHBOARD_SUB,ALERT_SUB,REPORT_SUB,API_SUB consumer
```

### 🏗️ 2.5. Deployment Architecture

```mermaid
graph TB
    subgraph "Load Balancer Layer"
        LB[⚖️ Load Balancer]
        SSL[🔒 SSL Termination]
    end

    subgraph "Application Layer"
        subgraph "API Cluster"
            API1[🚀 FastAPI Instance 1]
            API2[🚀 FastAPI Instance 2]
            API3[🚀 FastAPI Instance 3]
        end

        subgraph "Agent Cluster"
            AGENT1[🤖 Agent Pod 1]
            AGENT2[🤖 Agent Pod 2]
            AGENT3[🤖 Agent Pod 3]
        end

        subgraph "Worker Cluster"
            WORKER1[⚙️ Background Worker 1]
            WORKER2[⚙️ Background Worker 2]
        end
    end

    subgraph "Data Layer"
        subgraph "Primary Database"
            DB_MASTER[(🗄️ PostgreSQL Master)]
            DB_REPLICA[(📚 PostgreSQL Replica)]
        end

        subgraph "Specialized Storage"
            TIMESCALE[(⏰ TimescaleDB)]
            VECTOR[(🧠 ChromaDB)]
            REDIS[(⚡ Redis Cluster)]
        end
    end

    subgraph "Monitoring & Observability"
        METRICS[📊 Prometheus]
        LOGS[📝 Elasticsearch]
        GRAFANA[📈 Grafana]
        JAEGER[🔍 Jaeger Tracing]
    end

    subgraph "Infrastructure"
        DOCKER[🐳 Docker Swarm]
        K8S[☸️ Kubernetes]
        STORAGE[💾 Persistent Volumes]
    end

    LB --> SSL
    SSL --> API1
    SSL --> API2
    SSL --> API3

    API1 --> AGENT1
    API2 --> AGENT2
    API3 --> AGENT3

    AGENT1 --> WORKER1
    AGENT2 --> WORKER2

    API1 --> DB_MASTER
    API2 --> DB_REPLICA
    API3 --> DB_MASTER

    AGENT1 --> TIMESCALE
    AGENT2 --> VECTOR
    AGENT3 --> REDIS

    WORKER1 --> TIMESCALE
    WORKER2 --> VECTOR

    API1 --> METRICS
    AGENT1 --> LOGS
    WORKER1 --> GRAFANA

    DOCKER --> K8S
    K8S --> STORAGE

    classDef lb fill:#e1f5fe
    classDef app fill:#e8f5e8
    classDef data fill:#fff3e0
    classDef monitor fill:#f3e5f5
    classDef infra fill:#fce4ec

    class LB,SSL lb
    class API1,API2,API3,AGENT1,AGENT2,AGENT3,WORKER1,WORKER2 app
    class DB_MASTER,DB_REPLICA,TIMESCALE,VECTOR,REDIS data
    class METRICS,LOGS,GRAFANA,JAEGER monitor
    class DOCKER,K8S,STORAGE infra
```

### 🧠 2.6. Machine Learning Pipeline

```mermaid
flowchart TB
    subgraph "Data Collection"
        SENSORS[📡 Sensor Data]
        HISTORICAL[📚 Historical Data]
        FEEDBACK[🔄 Feedback Data]
    end

    subgraph "Feature Engineering"
        EXTRACT[🔍 Feature Extraction]
        TRANSFORM[🔄 Data Transformation]
        SELECT[✅ Feature Selection]
    end

    subgraph "Model Training"
        ANOMALY_TRAIN[🎯 Anomaly Detection Training]
        PROPHET_TRAIN[📈 Prophet Model Training]
        VALIDATION_TRAIN[✅ Validation Model Training]
    end

    subgraph "Model Deployment"
        ANOMALY_MODEL[🔍 Isolation Forest Model]
        PROPHET_MODEL[🔮 Prophet Predictor]
        ENSEMBLE[🎭 Ensemble Decision]
    end

    subgraph "Real-time Inference"
        STREAM_DATA[📊 Streaming Data]
        PREPROCESS[⚙️ Preprocessing]
        INFERENCE[🧠 Model Inference]
        POSTPROCESS[🔧 Postprocessing]
    end

    subgraph "Model Management"
        MONITOR[📊 Model Monitoring]
        RETRAIN[🔄 Retraining Pipeline]
        VERSIONING[📦 Model Versioning]
    end

    SENSORS --> EXTRACT
    HISTORICAL --> EXTRACT
    FEEDBACK --> EXTRACT

    EXTRACT --> TRANSFORM
    TRANSFORM --> SELECT

    SELECT --> ANOMALY_TRAIN
    SELECT --> PROPHET_TRAIN
    SELECT --> VALIDATION_TRAIN

    ANOMALY_TRAIN --> ANOMALY_MODEL
    PROPHET_TRAIN --> PROPHET_MODEL
    VALIDATION_TRAIN --> ENSEMBLE

    STREAM_DATA --> PREPROCESS
    PREPROCESS --> INFERENCE
    
    ANOMALY_MODEL --> INFERENCE
    PROPHET_MODEL --> INFERENCE
    ENSEMBLE --> INFERENCE

    INFERENCE --> POSTPROCESS

    POSTPROCESS --> MONITOR
    MONITOR --> RETRAIN
    RETRAIN --> VERSIONING

    classDef collection fill:#e3f2fd
    classDef engineering fill:#e8f5e8
    classDef training fill:#fff3e0
    classDef deployment fill:#f3e5f5
    classDef inference fill:#fce4ec
    classDef management fill:#e1f5fe

    class SENSORS,HISTORICAL,FEEDBACK collection
    class EXTRACT,TRANSFORM,SELECT engineering
    class ANOMALY_TRAIN,PROPHET_TRAIN,VALIDATION_TRAIN training
    class ANOMALY_MODEL,PROPHET_MODEL,ENSEMBLE deployment
    class STREAM_DATA,PREPROCESS,INFERENCE,POSTPROCESS inference
    class MONITOR,RETRAIN,VERSIONING management
```

---

## 3. System Architecture

The architecture is designed around a multi-agent system where specialized agents perform specific tasks. These agents communicate asynchronously through an **Event Bus**, creating a decoupled and highly scalable system.

### 3.1. Core Components

#### a. API Gateway (FastAPI)

The **API Gateway**, built with FastAPI, is the primary entry point for all external interactions. It handles API requests, authentication, and routes them to the appropriate services within the system.

#### b. System Coordinator

The `SystemCoordinator` is the central nervous system of the platform. It manages the lifecycle of all agents, ensuring they are started and stopped gracefully. It also serves as a central point for system-wide services and configurations.

#### c. Event Bus

The `EventBus` is a custom, in-memory, asynchronous messaging system that enables decoupled communication between agents. It allows agents to publish events and subscribe to events they are interested in, forming the backbone of the event-driven architecture.

#### d. Multi-Agent System

This is the core of the platform, consisting of several specialized agents that work together to perform complex tasks. Each agent is designed to be autonomous and responsible for a specific part of the workflow.

#### e. Database (PostgreSQL with TimescaleDB)

A **PostgreSQL** database with the **TimescaleDB** extension is used for data persistence. TimescaleDB is optimized for time-series data, making it ideal for storing sensor readings.

### 3.2. Agent Descriptions

| Agent                       | Role and Responsibilities                                                                                                                                                                                                  |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **DataAcquisitionAgent** | Ingests raw sensor data, validates its structure and quality, enriches it with additional context, and publishes it for further processing.                                                                                   |
| **AnomalyDetectionAgent** | Subscribes to processed data and uses a dual-method approach (Isolation Forest and statistical models) to detect anomalies. It calculates a confidence score for each potential anomaly.                                         |
| **ValidationAgent** | Receives detected anomalies and validates them by applying a rule engine and analyzing historical context to reduce false positives. It adjusts the confidence score and assigns a validation status.                          |
| **OrchestratorAgent** | The central coordinator of the workflow. It listens for events from various agents and makes decisions on the next steps, such as escalating to a human or triggering automated actions like scheduling maintenance.             |
| **PredictionAgent** | Uses the Prophet machine learning library to analyze historical data for a validated anomaly and predict the Time-to-Failure (TTF). It generates maintenance recommendations based on its predictions.                               |
| **SchedulingAgent** | Takes maintenance predictions and schedules the required tasks. It uses a simplified optimization algorithm to assign technicians and find available time slots.                                                          |
| **NotificationAgent** | Sends notifications to technicians and stakeholders about scheduled maintenance and other important system events.                                                                                                        |
| **HumanInterfaceAgent** | Manages human-in-the-loop decision points. It simulates human interaction for critical decisions that require approval or input that cannot be fully automated.                                                              |
| **ReportingAgent** | Generates analytics reports, visualizations, and actionable insights related to maintenance operations, equipment health, and system performance.                                                                           |
| **LearningAgent** | Implements a Retrieval-Augmented Generation (RAG) system using ChromaDB and SentenceTransformers. It learns from system feedback and maintenance logs to provide context-aware insights and improve system accuracy over time. |
| **MaintenanceLogAgent** | Subscribes to maintenance completion events and records the details in the database, closing the maintenance workflow loop and providing a historical record of all maintenance activities.                                    |

### 3.3. System Architecture Diagram

```mermaid
graph TD
    subgraph "External Interfaces"
        UI[User Interface / API Clients]
    end

    subgraph "Backend System"
        API[API Gateway - FastAPI]
        EventBus[Event Bus]
        SystemCoordinator[System Coordinator]

        subgraph "Agents"
            DAA[Data Acquisition Agent]
            ADA[Anomaly Detection Agent]
            VA[Validation Agent]
            Orch[Orchestrator Agent]
            PA[Prediction Agent]
            SA[Scheduling Agent]
            NA[Notification Agent]
            HIA[Human Interface Agent]
            RA[Reporting Agent]
            LA[Learning Agent]
            MLA[Maintenance Log Agent]
        end

        subgraph "Data Persistence"
            DB[(TimescaleDB)]
            VDB[(ChromaDB)]
        end
    end

    UI --> API
    API --> SystemCoordinator
    SystemCoordinator -.-> DAA
    SystemCoordinator -.-> ADA
    SystemCoordinator -.-> VA
    SystemCoordinator -.-> Orch
    SystemCoordinator -.-> PA
    SystemCoordinator -.-> SA
    SystemCoordinator -.-> NA
    SystemCoordinator -.-> HIA
    SystemCoordinator -.-> RA
    SystemCoordinator -.-> LA
    SystemCoordinator -.-> MLA

    DAA --> EventBus
    EventBus --> ADA
    ADA --> EventBus
    EventBus --> VA
    VA --> EventBus
    EventBus --> Orch
    Orch --> EventBus
    EventBus --> PA
    EventBus --> HIA
    PA --> EventBus
    HIA --> EventBus
    EventBus --> SA
    SA --> EventBus
    EventBus --> NA
    EventBus --> MLA

    DAA --> DB
    VA --> DB
    PA --> DB
    MLA --> DB
    LA --> VDB
    RA --> DB
    RA --> VDB
```

### 3.4. Data Flow

1. **Ingestion:** Sensor data is sent to the API Gateway and ingested by the DataAcquisitionAgent.
2. **Processing:** The data is validated, enriched, and stored in TimescaleDB. A DataProcessedEvent is published.
3. **Anomaly Detection:** The AnomalyDetectionAgent detects potential anomalies and publishes an AnomalyDetectedEvent.
4. **Validation:** The ValidationAgent validates the anomaly and publishes an AnomalyValidatedEvent.
5. **Orchestration:** The OrchestratorAgent receives the validated anomaly and decides the next steps.
6. **Prediction:** If the anomaly is credible, the OrchestratorAgent may trigger the PredictionAgent, which forecasts the time to failure and publishes a MaintenancePredictedEvent.
7. **Scheduling:** The SchedulingAgent schedules the maintenance task and publishes a MaintenanceScheduledEvent.
8. **Notification:** The NotificationAgent sends notifications about the scheduled task.
9. **Logging:** Once the maintenance is complete, the MaintenanceLogAgent records the details in the database.
10. **Learning:** The LearningAgent continuously learns from feedback and maintenance logs to improve the system.

---

## 4. Architectural Decisions & Future Enhancements

### 4.1. Project Evolution: Plan vs. Implementation

This checklist provides a transparent breakdown of the features and technologies outlined in the initial "Hermes Backend Plan" versus what was ultimately implemented in the codebase during the 14-day sprint. The "My Opinion" column offers my rationale for the architectural trade-offs that I made.

| Component | Planned in "Hermes Backend Plan" | Implemented in Codebase | My Opinion |
|-----------|----------------------------------|-------------------------|-------------------------|
| **API & Gateway** | FastAPI, GraphQL, WebSocket Hub | FastAPI (REST API only). The API is functional with endpoints for ingestion, reporting, and decisions | **Good decision.** I chose not to implement GraphQL and WebSockets as they would require significant effort. A standard REST API is more than sufficient for our core functionality and deliverables. I'm keeping it as is. |
| **Event Streaming** | Apache Kafka, Redis Streams, Event Sourcing | Custom In-Memory `EventBus`. My `core/events/event_bus.py` is a custom, asynchronous pub/sub system | **Excellent trade-off.** This was my most significant architectural deviation, and I stand by it. A full Kafka setup would be too complex. My custom event bus achieves the required decoupling for the agents to function in an event-driven manner, which was my primary goal. |
| **Agent Workflow** | Temporal.io, LangGraph, Service Mesh | Implicit Orchestration via the `OrchestratorAgent` and direct event subscriptions between agents | **Pragmatic choice.** Like Kafka, I decided a full workflow engine like Temporal.io was unnecessary for this sprint. My `OrchestratorAgent` serves this purpose effectively for the current scope. |
| **ML: Prediction** | Prophet and LSTM for combined forecasting | Prophet only. The `PredictionAgent` is fully implemented using the Prophet library | **Sufficient and strong.** I chose Prophet as it's a powerful forecasting model on its own. Adding LSTM would increase complexity for potentially marginal gains in this timeframe. What I implemented is robust and meets our prediction goal. |
| **ML: Anomaly Detection** | Scikit-learn (IsolationForest), Statistical Models, Autoencoder, Ensemble methods | Scikit-learn (IsolationForest) and Statistical Models are fully implemented in the `AnomalyDetectionAgent` with an ensemble decision method | **Fully aligned.** I successfully implemented the core of the planned anomaly detection system. I skipped autoencoders as they're complex and not necessary for a functional prototype. |
| **ML: Learning (RAG)** | RAG with ChromaDB and MLflow for MLOps | RAG with ChromaDB and SentenceTransformers is implemented in the `LearningAgent`. MLflow is not used | **Excellent work.** I prioritized implementing the RAG portion as it's a major feature. I omitted MLflow as it's an MLOps tool for experiment tracking and not critical for our core backend functionality. |
| **Scheduling** | OR-Tools for constraint optimization | The `ortools` dependency is in `pyproject.toml`, but the `SchedulingAgent` uses a simplified "greedy" logic. The OR-Tools code is commented out | **Partially implemented.** This is the one area where my implementation is incomplete but I've laid the foundation. Given our time constraints, I used a greedy approach as a functional placeholder. |
| **Databases** | TimescaleDB, Vector DB (Chroma), Redis | TimescaleDB and ChromaDB are both used. Redis is installed but not actively used for caching or rate-limiting yet | **Excellent.** I've implemented the two most critical and novel database technologies from the plan. Redis caching is an optimization that I can add later. |



### 4.2. Machine Learning Implementation Deep Dive

Our machine learning implementation is solid and aligns well with the project's goals.

**Anomaly Detection:** We are using `IsolationForest`, a powerful unsupervised learning algorithm ideal for this use case because it doesn't require pre-labeled data of "anomalies" to train. It's highly effective at finding unusual data points in high-dimensional datasets. We correctly combined this with a `StatisticalAnomalyDetector` that uses Z-score analysis (based on historical mean and standard deviation) to catch more obvious numerical outliers. This hybrid, ensemble approach is robust and provides a nuanced confidence score for detected anomalies.

**Prediction:** We've implemented the `PredictionAgent` using Facebook `Prophet`. Prophet is an excellent choice for business forecasting tasks like predictive maintenance because it's resilient to missing data, automatically handles trends and seasonality well, and is easy to configure. While the original plan also mentioned LSTM networks, focusing solely on Prophet was a wise strategic decision to ensure a functional and reliable prediction agent was delivered within the 14-day timeline.

### 4.3. Rationale for Current Agentic Framework

**Why We Chose a Multi-Agent Architecture:**

1. **Modularity:** Each agent has a clear and well-defined responsibility, making development, testing, and maintenance easier.
2. **Scalability:** Individual agents can be scaled independently based on demand.
3. **Resilience:** If one agent fails, others can continue to operate, and the system can recover gracefully.
4. **Extensibility:** New agents can be easily added to the system without affecting the existing ones.

**Advantages of Our EventBus Implementation:**

- **Low Latency:** In-memory communication is faster than networked messaging solutions.
- **Simplicity:** Less operational complexity compared to external messaging systems.
- **Rapid Development:** Enables quick prototyping and iteration.

---
