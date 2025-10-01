# Smart Maintenance SaaS – System & Architecture (V1.0)

**Last Updated:** 2025-09-30  
**Status:** V1.0 Production Ready  
**Authoritative Source:** [v1_release_must_do.md](./v1_release_must_do.md) - V1.0 Deployment Playbook (replaces former readiness checklist and capability matrix)  
**Scope:** High-level architectural overview for engineers and auditors. Detailed capability status, task tracking, and deployment procedures are in the deployment playbook.  
**Document Philosophy:** Minimize duplication. Link to canonical artifacts instead of restating them.

## 1. Introduction

This document provides a comprehensive overview of the system architecture for the Smart Maintenance SaaS platform. The platform is a **cloud-native, event-driven system** with **S3 serverless model loading** that delivers scalable, resilient predictive maintenance solutions for industrial applications.

### 1.1. Architecture Overview (Concise)

Core properties:

- **Event-Driven Core:** Custom in-memory event bus (retry + DLQ) enabling asynchronous agent orchestration.
- **Multi-Agent Execution Model:** 12 specialized agents (ingestion, anomaly detection, validation, prediction, scheduling, reporting, learning, drift, retrain, notification, maintenance log, human decision) communicating via events.
- **Temporal & Analytical Storage:** PostgreSQL + TimescaleDB (hypertables, compression, continuous aggregates) with cloud deployment (Render) verified.
- **Model Lifecycle:** MLflow registry (17+ models) with S3 artifact storage + lightweight model cache for near-zero latency inference.
- **Resilience Patterns:** Correlation IDs, idempotency cache (Redis), retry with exponential backoff, health & metrics endpoints.
- **Performance Provenance:** Validated 103.8 RPS peak ([legacy performance reports](./legacy/DAY_17_LOAD_TEST_REPORT.md)) and ≥30% query acceleration via TimescaleDB optimizations.
- **Cloud Mode Toggle:** Environment-driven latency/caching policies; same container images usable locally & in cloud.
- **Offline ML Mode:** `DISABLE_MLFLOW_MODEL_LOADING` flag enables operation without MLflow registry access.

Out-of-scope in this file: detailed dataset performance tables, full agent message taxonomies, gap remediation phases. See [v1_release_must_do.md](./v1_release_must_do.md) for comprehensive capability matrix and deferred features.

### 1.2. V1.0 Status Snapshot

| Layer | Status | Notes |
|-------|--------|-------|
| API / Gateway | ✅ Ready | FastAPI + metrics + auth + rate limiting operational |
| Event Bus | ✅ Stable | In-memory with retry/DLQ; Kafka migration earmarked post-V1.0 |
| Multi-Agent System | ✅ Operational | All 12 agents functional; UI exposes ~70% intentionally (see playbook Section 2.2) |
| ML Registry | ✅ Stable | 17+ models with S3 backend; offline mode available |
| Database Layer | ✅ Optimized | Cloud TimescaleDB with continuous aggregates + composite indexes |
| Caching | ✅ Basic | Redis coordination active; advanced caching deferred |
| UI | ✅ Adequate | All golden-path workflows functional with error handling |

For detailed feature implementations, capability status, and deferred features: [v1_release_must_do.md Sections 2-3](./v1_release_must_do.md).

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

    classDef external fill:#0D47A1,color:#ffffff,stroke:#062a5e,stroke-width:3px
    classDef api fill:#4A148C,color:#ffffff,stroke:#1a0632,stroke-width:3px
    classDef core fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px
    classDef data fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef infra fill:#880E4F,color:#ffffff,stroke:#440727,stroke-width:3px

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
        NOTEBOOKS[Jupyter Notebooks<br/>Papermill Execution]
        DATASETS[Real-World Datasets<br/>AI4I, NASA, XJTU, MIMII]
        TRAINING[Model Training Pipeline<br/>Automated via Makefile]
    end

    subgraph "MLflow Registry"
        REGISTRY[Model Registry<br/>Version Control]
        ARTIFACTS[S3 Artifact Storage<br/>AWS S3 Backend]
        VERSIONING[Model Versioning<br/>Timestamp Tags]
        METADATA[Experiment Metadata<br/>SQLite Backend]
    end

    subgraph "Production Deployment"
        LOADER[Model Loader<br/>S3 Download]
        CACHE[Model Cache<br/>In-Memory]
        INFERENCE[Real-time Inference<br/>FastAPI Endpoints]
        MONITORING[Model Monitoring<br/>Drift Detection]
    end

    subgraph "Data Sources"
        AI4I[AI4I Industrial Dataset<br/>99.90% Accuracy]
        NASA[NASA Bearing Dataset<br/>72.8% Accuracy]
        XJTU[XJTU Bearing Dataset<br/>Vibration Analysis]
        MIMII[MIMII Audio Dataset<br/>93.3% Accuracy]
        KAGGLE[Kaggle Pump Dataset<br/>100% Accuracy]
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

    classDef training fill:#004D40,color:#ffffff,stroke:#00251a,stroke-width:3px
    classDef registry fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px
    classDef deployment fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef data fill:#4A148C,color:#ffffff,stroke:#1a0632,stroke-width:3px

    class NOTEBOOKS,DATASETS,TRAINING training
    class REGISTRY,ARTIFACTS,VERSIONING,METADATA registry
    class LOADER,CACHE,INFERENCE,MONITORING deployment
    class AI4I,NASA,XJTU,MIMII,KAGGLE data
```

### 2.4. TimescaleDB Performance Architecture

```mermaid
graph TD
    subgraph "Data Ingestion Layer"
        API_INGEST[API Ingestion Endpoint<br/>/api/v1/ingest]
        VALIDATION[Data Validation<br/>Pydantic Schema]
        TRANSFORM[Data Transformation<br/>Normalization]
    end

    subgraph "TimescaleDB Core"
        HYPERTABLE[sensor_readings Hypertable<br/>Time-based Partitioning]
        COMPRESSION[Automatic Compression<br/>30% Space Savings]
        PARTITIONING[Time-based Partitioning<br/>1-day Chunks]
    end

    subgraph "Performance Optimization"
        CONT_AGG[Continuous Aggregates<br/>Hourly Summaries]
        INDEXES[Optimized Indexes<br/>Composite Keys]
        RETENTION[Retention Policies<br/>Automated Cleanup]
    end

    subgraph "Query Performance"
        HOURLY_VIEW[Hourly Summary Views<br/>37% Faster Queries]
        SENSOR_INDEX[Sensor-Time Index<br/>idx_sensor_timestamp]
        TIME_INDEX[Time Range Index<br/>idx_timestamp]
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

    classDef ingestion fill:#0D47A1,color:#ffffff,stroke:#062a5e,stroke-width:3px
    classDef core fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px
    classDef optimization fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef performance fill:#4A148C,color:#ffffff,stroke:#1a0632,stroke-width:3px

    class API_INGEST,VALIDATION,TRANSFORM ingestion
    class HYPERTABLE,COMPRESSION,PARTITIONING core
    class CONT_AGG,INDEXES,RETENTION optimization
    class HOURLY_VIEW,SENSOR_INDEX,TIME_INDEX performance
```

### 2.5. Production Performance Metrics Flow (Summary Only)

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

    classDef testing fill:#004D40,color:#ffffff,stroke:#00251a,stroke-width:2px
    classDef results fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:2px
    classDef monitoring fill:#4A148C,color:#ffffff,stroke:#1a0632,stroke-width:2px
    classDef infrastructure fill:#880E4F,color:#ffffff,stroke:#440727,stroke-width:2px

    class LOCUST,CONCURRENT,DURATION testing
    class THROUGHPUT,LATENCY,STABILITY,RESOURCE results
    class PROMETHEUS,HEALTH,LOGS,ALERTS monitoring
    class API_CONTAINER,DB_CONTAINER,REDIS_CONTAINER,MEMORY infrastructure
```

### 2.6. Docker Services Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Streamlit UI<br/>Port 8501<br/>User Interface]
    end

    subgraph "API Layer"
        API[FastAPI Service<br/>Port 8000<br/>Main Backend]
    end

    subgraph "Agent Services"
        DRIFT[Drift Detection Agent<br/>Monitors Model Performance<br/>Every 6 hours]
        RETRAIN[Retrain Agent<br/>Auto Model Updates<br/>Event-Driven]
    end

    subgraph "Data Layer"
        DB[(TimescaleDB<br/>Port 5433<br/>Time-Series Storage)]
        REDIS[(Redis<br/>Port 6379<br/>Cache & Events)]
        MLFLOW[MLflow Registry<br/>Port 5000<br/>Model Storage]
    end

    subgraph "ML Execution"
        NOTEBOOK[Notebook Runner<br/>Papermill Execution<br/>Training Pipelines]
        ML[ML Utility<br/>Ad-hoc Operations<br/>Locust Testing]
    end

    subgraph "Infrastructure"
        TOXIPROXY[Toxiproxy<br/>Port 8474<br/>Chaos Engineering]
        TOXINIT[Toxiproxy Init<br/>One-time Setup]
    end

    UI --> API
    API --> DB
    API --> REDIS
    API --> MLFLOW
    
    DRIFT --> DB
    DRIFT --> REDIS
    DRIFT --> MLFLOW
    
    RETRAIN --> REDIS
    RETRAIN --> MLFLOW
    
    NOTEBOOK --> MLFLOW
    ML --> MLFLOW
    
    API --> TOXIPROXY
    TOXIPROXY --> DB
    TOXIPROXY --> REDIS
    TOXINIT --> TOXIPROXY

    classDef frontend fill:#1A237E,color:#ffffff,stroke:#0d1642,stroke-width:3px
    classDef api fill:#004D40,color:#ffffff,stroke:#00251a,stroke-width:3px
    classDef agent fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px
    classDef data fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef ml fill:#4A148C,color:#ffffff,stroke:#1a0632,stroke-width:3px
    classDef infra fill:#880E4F,color:#ffffff,stroke:#440727,stroke-width:3px

    class UI frontend
    class API api
    class DRIFT,RETRAIN agent
    class DB,REDIS,MLFLOW data
    class NOTEBOOK,ML ml
    class TOXIPROXY,TOXINIT infra
```

### 2.7. Complete Multi-Agent System Architecture

```mermaid
graph TB
    subgraph "Core Agents"
        DAA[Data Acquisition Agent<br/>Ingestion & Validation]
        ADA[Anomaly Detection Agent<br/>ML-based Analysis]
        VA[Validation Agent<br/>False Positive Reduction]
        ORCH[Orchestrator Agent<br/>Workflow Coordination]
    end

    subgraph "Decision Agents"
        PA[Prediction Agent<br/>Prophet Forecasting]
        SA[Scheduling Agent<br/>Task Optimization]
        NA[Notification Agent<br/>Multi-channel Alerts]
        RA[Reporting Agent<br/>Analytics & Insights]
    end

    subgraph "Interface & Learning"
        HIA[Human Interface Agent<br/>Human-in-the-Loop]
        LA[Learning Agent<br/>RAG with ChromaDB]
        MLA[Maintenance Log Agent<br/>History Tracking]
    end

    subgraph "MLOps Agents"
        DCA[Drift Check Agent<br/>Performance Monitoring]
        RTR[Retrain Agent<br/>Auto Retraining]
        MSA[Model Selection Agent<br/>Intelligent Routing]
        CEA[Chaos Engineering Agent<br/>Resilience Testing]
    end

    subgraph "Event Infrastructure"
        EB[Redis Event Bus<br/>Pub/Sub + DLQ<br/>Retry Logic]
    end

    DAA --> EB
    EB --> ADA
    ADA --> EB
    EB --> VA
    VA --> EB
    EB --> ORCH
    ORCH --> EB
    EB --> PA
    PA --> EB
    EB --> SA
    SA --> EB
    EB --> NA
    EB --> RA
    EB --> HIA
    EB --> LA
    EB --> MLA
    
    DCA --> EB
    EB --> RTR
    RTR --> EB
    EB --> MSA
    EB --> CEA

    classDef core fill:#004D40,color:#ffffff,stroke:#00251a,stroke-width:3px
    classDef decision fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px
    classDef interface fill:#1A237E,color:#ffffff,stroke:#0d1642,stroke-width:3px
    classDef mlops fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef eventbus fill:#880E4F,color:#ffffff,stroke:#440727,stroke-width:3px

    class DAA,ADA,VA,ORCH core
    class PA,SA,NA,RA decision
    class HIA,LA,MLA interface
    class DCA,RTR,MSA,CEA mlops
    class EB eventbus
```

### 2.8. MLOps Automation: Drift Detection to Retraining

```mermaid
flowchart LR
    subgraph "Monitoring"
        SENSOR[Sensor Data Stream]
        DCA[Drift Check Agent<br/>Every 6 Hours<br/>KS Test + PSI]
        METRICS[Performance Metrics<br/>Accuracy Tracking]
    end

    subgraph "Event Bus"
        REDIS[Redis Event Bus<br/>drift_events Channel]
        DLQ[Dead Letter Queue<br/>Failed Events]
    end

    subgraph "Automated Retraining"
        RTR[Retrain Agent<br/>Event Consumer]
        POLICY[Retraining Policy<br/>24h Cooldown<br/>Max 1 Concurrent]
        TRAIN[Training Execution<br/>make train-anomaly<br/>make train-forecast]
    end

    subgraph "Model Registry"
        MLR[MLflow Registry<br/>S3 Artifacts]
        VERSION[Model Versioning<br/>Timestamp Tags]
        CACHE[Model Cache<br/>Production Ready]
    end

    subgraph "Notifications"
        SLACK[Slack Webhook<br/>Drift Alerts]
        EMAIL[Email Service<br/>Training Status]
    end

    SENSOR --> DCA
    DCA --> METRICS
    DCA -->|DriftDetectedEvent| REDIS
    REDIS --> RTR
    REDIS --> DLQ
    RTR --> POLICY
    POLICY -->|Approved| TRAIN
    TRAIN --> MLR
    MLR --> VERSION
    VERSION --> CACHE
    
    DCA --> SLACK
    RTR --> EMAIL
    TRAIN -->|RetrainCompleted| REDIS
    TRAIN -->|RetrainFailed| DLQ

    classDef monitoring fill:#004D40,color:#ffffff,stroke:#00251a,stroke-width:3px
    classDef eventbus fill:#880E4F,color:#ffffff,stroke:#440727,stroke-width:3px
    classDef retraining fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef registry fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px
    classDef notifications fill:#4A148C,color:#ffffff,stroke:#1a0632,stroke-width:3px

    class SENSOR,DCA,METRICS monitoring
    class REDIS,DLQ eventbus
    class RTR,POLICY,TRAIN retraining
    class MLR,VERSION,CACHE registry
    class SLACK,EMAIL notifications
```

### 2.9. Data Ingestion and Processing Pipeline

```mermaid
flowchart TB
    subgraph "Data Sources"
        IOT[IoT Sensors<br/>Real-time Streams]
        BATCH[Batch Uploads<br/>CSV/JSON Files]
        API_EXT[External APIs<br/>Third-party Data]
    end

    subgraph "Ingestion Layer"
        API_IN[FastAPI Endpoint<br/>/api/v1/ingest]
        VALIDATE[Schema Validation<br/>Pydantic Models]
        ENRICH[Data Enrichment<br/>Metadata Addition]
        IDEMPOTENCY[Idempotency Check<br/>Redis Dedup<br/>10min TTL]
    end

    subgraph "Event Processing"
        EVENT[DataIngestionEvent<br/>Correlation ID]
        DAA[Data Acquisition Agent<br/>Business Logic]
        PROCESS[DataProcessedEvent<br/>Ready for ML]
    end

    subgraph "Storage Layer"
        TS[(TimescaleDB<br/>Hypertable Storage<br/>Auto Compression)]
        REDIS_CACHE[(Redis Cache<br/>Recent Results)]
        AUDIT[Audit Trail<br/>Event Log)]
    end

    subgraph "ML Pipeline"
        ADA[Anomaly Detection<br/>Isolation Forest]
        VA[Validation Agent<br/>Rule Engine]
        PA[Prediction Agent<br/>Prophet Model]
    end

    IOT --> API_IN
    BATCH --> API_IN
    API_EXT --> API_IN
    
    API_IN --> VALIDATE
    VALIDATE --> IDEMPOTENCY
    IDEMPOTENCY -->|New| ENRICH
    IDEMPOTENCY -->|Duplicate| REDIS_CACHE
    ENRICH --> EVENT
    
    EVENT --> DAA
    DAA --> TS
    DAA --> PROCESS
    
    PROCESS --> ADA
    ADA --> VA
    VA --> PA
    
    TS --> AUDIT
    REDIS_CACHE --> AUDIT

    classDef sources fill:#1A237E,color:#ffffff,stroke:#0d1642,stroke-width:3px
    classDef ingestion fill:#004D40,color:#ffffff,stroke:#00251a,stroke-width:3px
    classDef processing fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef storage fill:#880E4F,color:#ffffff,stroke:#440727,stroke-width:3px
    classDef ml fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px

    class IOT,BATCH,API_EXT sources
    class API_IN,VALIDATE,ENRICH,IDEMPOTENCY ingestion
    class EVENT,DAA,PROCESS processing
    class TS,REDIS_CACHE,AUDIT storage
    class ADA,VA,PA ml
```

### 2.10. Redis Event Bus Architecture

```mermaid
graph TB
    subgraph "Event Publishers"
        API[FastAPI Endpoints]
        AGENTS[Agent System]
        SCHEDULER[Cron Schedulers]
    end

    subgraph "Redis Event Bus Core"
        PUBSUB[Redis Pub/Sub<br/>Event Channels]
        STREAM[Event Stream<br/>Ordered Log]
        RETRY[Retry Queue<br/>Exponential Backoff]
        DLQ[Dead Letter Queue<br/>Failed Events]
    end

    subgraph "Event Subscribers"
        DAA_SUB[Data Acquisition<br/>Subscriber]
        ADA_SUB[Anomaly Detection<br/>Subscriber]
        RTR_SUB[Retrain Agent<br/>Subscriber]
        DRIFT_SUB[Drift Monitor<br/>Subscriber]
    end

    subgraph "Event Types"
        DATA_EVENT[DataIngestionEvent<br/>DataProcessedEvent]
        ANOMALY_EVENT[AnomalyDetectedEvent<br/>AnomalyValidatedEvent]
        ML_EVENT[DriftDetectedEvent<br/>RetrainCompletedEvent]
        MAINT_EVENT[MaintenanceScheduledEvent<br/>MaintenanceCompletedEvent]
    end

    subgraph "Monitoring"
        METRICS[Event Metrics<br/>Throughput & Latency]
        AUDIT[Audit Trail<br/>Event History]
        CORRELATION[Correlation IDs<br/>Request Tracing]
    end

    API --> PUBSUB
    AGENTS --> PUBSUB
    SCHEDULER --> PUBSUB
    
    PUBSUB --> STREAM
    STREAM --> DAA_SUB
    STREAM --> ADA_SUB
    STREAM --> RTR_SUB
    STREAM --> DRIFT_SUB
    
    STREAM -->|Failed| RETRY
    RETRY -->|Max Retries| DLQ
    RETRY -->|Success| STREAM
    
    DATA_EVENT --> PUBSUB
    ANOMALY_EVENT --> PUBSUB
    ML_EVENT --> PUBSUB
    MAINT_EVENT --> PUBSUB
    
    STREAM --> METRICS
    STREAM --> AUDIT
    PUBSUB --> CORRELATION

    classDef publishers fill:#1A237E,color:#ffffff,stroke:#0d1642,stroke-width:3px
    classDef bus fill:#880E4F,color:#ffffff,stroke:#440727,stroke-width:3px
    classDef subscribers fill:#004D40,color:#ffffff,stroke:#00251a,stroke-width:3px
    classDef events fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef monitoring fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px

    class API,AGENTS,SCHEDULER publishers
    class PUBSUB,STREAM,RETRY,DLQ bus
    class DAA_SUB,ADA_SUB,RTR_SUB,DRIFT_SUB subscribers
    class DATA_EVENT,ANOMALY_EVENT,ML_EVENT,MAINT_EVENT events
    class METRICS,AUDIT,CORRELATION monitoring
```

### 2.11. Security and Authentication Flow

```mermaid
sequenceDiagram
    participant CLIENT as Client/IoT Device
    participant LB as Load Balancer<br/>Rate Limiting
    participant API as FastAPI Gateway
    participant AUTH as Auth Middleware
    participant RATE as Rate Limiter<br/>10/min ML Endpoints
    participant IDEMPOTENCY as Idempotency Cache
    participant AGENT as Agent System
    participant DB as Database

    CLIENT->>+LB: HTTP Request
    LB->>LB: Initial Rate Check
    LB->>+API: Forward Request
    API->>API: Generate Correlation ID
    API->>+AUTH: X-API-Key Header
    
    alt Invalid API Key
        AUTH->>CLIENT: 401 Unauthorized
    end
    
    AUTH->>AUTH: Validate API Key
    AUTH->>+RATE: Check Rate Limit
    
    alt Rate Limit Exceeded
        RATE->>CLIENT: 429 Too Many Requests
    end
    
    RATE->>+IDEMPOTENCY: Check Request ID
    
    alt Duplicate Request
        IDEMPOTENCY->>CLIENT: 200 OK (Cached)
    end
    
    IDEMPOTENCY->>+AGENT: Process Request
    AGENT->>+DB: Store Data
    DB-->>-AGENT: Confirmation
    AGENT-->>-IDEMPOTENCY: Result
    IDEMPOTENCY->>IDEMPOTENCY: Cache Result (10min TTL)
    IDEMPOTENCY-->>-RATE: Success
    RATE-->>-AUTH: Success
    AUTH-->>-API: Response
    API-->>-LB: JSON Response + Correlation ID
    LB-->>-CLIENT: 200 OK

    Note over CLIENT,DB: All requests include correlation IDs<br/>for distributed tracing
```

### 2.12. Chaos Engineering and Resilience Testing

```mermaid
graph TB
    subgraph "Test Orchestration"
        CHAOS[Chaos Engineering Agent<br/>Automated Testing]
        SCENARIOS[Test Scenarios<br/>Network Failures<br/>Latency Injection<br/>Service Crashes]
    end

    subgraph "Toxiproxy Layer"
        TOXIAPI[Toxiproxy API<br/>Port 8474<br/>Control Plane]
        TOXIDB[DB Proxy<br/>Port 5434<br/>PostgreSQL]
        TOXIREDIS[Redis Proxy<br/>Port 6380<br/>Redis]
    end

    subgraph "Services Under Test"
        API[FastAPI Service]
        AGENTS[Agent System]
        DRIFT[Drift Agent]
        RETRAIN[Retrain Agent]
    end

    subgraph "Actual Data Stores"
        DB[(TimescaleDB<br/>Port 5432)]
        REDIS[(Redis<br/>Port 6379)]
    end

    subgraph "Validation & Monitoring"
        HEALTH[Health Checks<br/>Service Status]
        METRICS[Performance Metrics<br/>Response Times]
        RECOVERY[Recovery Tests<br/>Automatic Healing]
    end

    CHAOS --> SCENARIOS
    SCENARIOS --> TOXIAPI
    
    TOXIAPI -->|Configure Toxics| TOXIDB
    TOXIAPI -->|Configure Toxics| TOXIREDIS
    
    API --> TOXIDB
    API --> TOXIREDIS
    AGENTS --> TOXIDB
    AGENTS --> TOXIREDIS
    DRIFT --> TOXIDB
    RETRAIN --> TOXIREDIS
    
    TOXIDB --> DB
    TOXIREDIS --> REDIS
    
    API --> HEALTH
    AGENTS --> METRICS
    DRIFT --> RECOVERY

    classDef orchestration fill:#880E4F,color:#ffffff,stroke:#440727,stroke-width:3px
    classDef toxiproxy fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef services fill:#004D40,color:#ffffff,stroke:#00251a,stroke-width:3px
    classDef datastores fill:#1A237E,color:#ffffff,stroke:#0d1642,stroke-width:3px
    classDef validation fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px

    class CHAOS,SCENARIOS orchestration
    class TOXIAPI,TOXIDB,TOXIREDIS toxiproxy
    class API,AGENTS,DRIFT,RETRAIN services
    class DB,REDIS datastores
    class HEALTH,METRICS,RECOVERY validation
```

### 2.13. Notebook Training Pipeline and Makefile Automation

```mermaid
flowchart TB
    subgraph "Training Orchestration"
        MAKEFILE[Makefile Targets<br/>train-anomaly<br/>train-forecast<br/>classification-gauntlet]
        DOCKER_COMPOSE[Docker Compose<br/>notebook_runner Service<br/>Papermill Execution]
    end

    subgraph "Jupyter Notebooks"
        NB00[00_synthetic_data_validation<br/>Data Quality Checks]
        NB01[01_synthetic_data_exploration<br/>EDA & Visualization]
        NB02[02_anomaly_isolation_forest<br/>Anomaly Detection Training]
        NB03[03_forecast_prophet<br/>Time Series Forecasting]
        NB04[04_forecasting_tuning<br/>Hyperparameter Optimization]
        NB05[05_classification_benchmark<br/>AI4I Dataset - 99.90%]
        NB06[06_vibration_benchmark<br/>NASA Bearing - 72.8%]
        NB07[07_audio_benchmark<br/>MIMII Sound - 93.3%]
        NB08[08_pump_classification<br/>Kaggle Pump - 100%]
        NB09[09_xjtu_vibration<br/>XJTU Bearing Analysis]
    end

    subgraph "Data Sources"
        SYNTHETIC[Synthetic Data<br/>Generated Sensor Data]
        REALWORLD[Real-World Datasets<br/>5 Industrial Sources]
    end

    subgraph "MLflow Integration"
        TRACKING[Experiment Tracking<br/>Metrics & Parameters]
        ARTIFACTS[Model Artifacts<br/>S3 Storage]
        REGISTRY[Model Registry<br/>Version Control]
    end

    subgraph "Output & Results"
        MODELS[Trained Models<br/>17+ Production Models]
        PLOTS[Visualizations<br/>Performance Plots]
        DOCS[Documentation<br/>Training Reports]
    end

    MAKEFILE --> DOCKER_COMPOSE
    DOCKER_COMPOSE --> NB00
    DOCKER_COMPOSE --> NB02
    DOCKER_COMPOSE --> NB03
    DOCKER_COMPOSE --> NB05
    DOCKER_COMPOSE --> NB06
    DOCKER_COMPOSE --> NB07
    
    NB00 --> SYNTHETIC
    NB01 --> SYNTHETIC
    NB02 --> SYNTHETIC
    NB03 --> SYNTHETIC
    
    NB05 --> REALWORLD
    NB06 --> REALWORLD
    NB07 --> REALWORLD
    NB08 --> REALWORLD
    NB09 --> REALWORLD
    
    NB02 --> TRACKING
    NB03 --> TRACKING
    NB05 --> TRACKING
    NB06 --> TRACKING
    NB07 --> TRACKING
    
    TRACKING --> ARTIFACTS
    ARTIFACTS --> REGISTRY
    
    REGISTRY --> MODELS
    NB01 --> PLOTS
    NB04 --> DOCS

    classDef orchestration fill:#880E4F,color:#ffffff,stroke:#440727,stroke-width:3px
    classDef notebooks fill:#004D40,color:#ffffff,stroke:#00251a,stroke-width:3px
    classDef data fill:#1A237E,color:#ffffff,stroke:#0d1642,stroke-width:3px
    classDef mlflow fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px
    classDef output fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px

    class MAKEFILE,DOCKER_COMPOSE orchestration
    class NB00,NB01,NB02,NB03,NB04,NB05,NB06,NB07,NB08,NB09 notebooks
    class SYNTHETIC,REALWORLD data
    class TRACKING,ARTIFACTS,REGISTRY mlflow
    class MODELS,PLOTS,DOCS output
```

### 2.14. API Endpoints Architecture

```mermaid
graph TB
    subgraph "Public API Gateway"
        MAIN[FastAPI Main<br/>Port 8000<br/>apps/api/main.py]
    end

    subgraph "Data Ingestion Routes"
        INGEST[/api/v1/ingest<br/>POST - Sensor Data]
        READINGS[/api/v1/sensor-readings<br/>GET - Query Data]
    end

    subgraph "ML Endpoints"
        PREDICT[/api/v1/ml/predict<br/>POST - Model Inference]
        DRIFT[/api/v1/ml/check_drift<br/>POST - Drift Detection]
        MODELS[/api/v1/ml/models<br/>GET - Model List]
    end

    subgraph "Decision & Workflow"
        DECISIONS[/api/v1/decisions<br/>GET/POST - Decisions]
        HUMAN[/api/v1/human-decisions<br/>POST - Human Review]
        MAINTENANCE[/api/v1/maintenance<br/>GET/POST - Tasks]
    end

    subgraph "Reporting & Analytics"
        REPORT[/api/v1/reports<br/>GET - Analytics]
        SIMULATE[/api/v1/simulate<br/>POST - Test Scenarios]
        DEMO[/api/v1/demo<br/>POST - Demo Workflows]
    end

    subgraph "System Monitoring"
        HEALTH[/health<br/>GET - Service Health]
        HEALTHDB[/health/db<br/>GET - Database Health]
        METRICS[/metrics<br/>GET - Prometheus]
    end

    MAIN --> INGEST
    MAIN --> READINGS
    MAIN --> PREDICT
    MAIN --> DRIFT
    MAIN --> MODELS
    MAIN --> DECISIONS
    MAIN --> HUMAN
    MAIN --> MAINTENANCE
    MAIN --> REPORT
    MAIN --> SIMULATE
    MAIN --> DEMO
    MAIN --> HEALTH
    MAIN --> HEALTHDB
    MAIN --> METRICS

    classDef gateway fill:#1A237E,color:#ffffff,stroke:#0d1642,stroke-width:3px
    classDef ingestion fill:#004D40,color:#ffffff,stroke:#00251a,stroke-width:3px
    classDef ml fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef workflow fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px
    classDef reporting fill:#4A148C,color:#ffffff,stroke:#1a0632,stroke-width:3px
    classDef monitoring fill:#880E4F,color:#ffffff,stroke:#440727,stroke-width:3px

    class MAIN gateway
    class INGEST,READINGS ingestion
    class PREDICT,DRIFT,MODELS ml
    class DECISIONS,HUMAN,MAINTENANCE workflow
    class REPORT,SIMULATE,DEMO reporting
    class HEALTH,HEALTHDB,METRICS monitoring
```

---

## 3. Core Technology Stack

### API Layer

- **FastAPI 0.104.1** with Starlette-compatible dependencies
- **Prometheus metrics integration** via `prometheus-fastapi-instrumentator`
- **API rate limiting** (10 requests/minute for ML endpoints)
- **Request correlation IDs** for distributed tracing
- **Idempotency support** with TTL-based deduplication (10-minute cache)
- **Structured JSON logging** with correlation ID propagation
- **Health endpoints** (`/health`, `/health/db`, `/metrics`)

### Data Layer

- **PostgreSQL with TimescaleDB 2.11+** optimized for time-series data
- **Redis 7.0+** for caching and session management
- **MLflow Model Registry** with SQLite backend and artifact storage
- **Continuous aggregates** for real-time analytics performance
- **Automatic data compression** and retention policies

### Event Processing

- **Custom Event Bus** with exponential backoff retry logic
- **Dead Letter Queue (DLQ)** for failed event handling
- **Asynchronous processing** with correlation ID propagation
- **Event persistence** with comprehensive audit trails

### 3.2. Performance (Pointer)

To avoid duplication, authoritative performance datasets live in: `PERFORMANCE_BASELINE.md`, `DAY_17_LOAD_TEST_REPORT.md`, `DAY_18_PERFORMANCE_RESULTS.md`.

Snapshot:

- Peak RPS: 103.8 (validated)
- Latency: P95 2ms / P99 3ms
- DB Query Speedups: 30–37% via continuous aggregates & indexes
- Headroom: <6% CPU under validated load

### 3.3. Multi-Agent System (Summary)

The platform implements a sophisticated multi-agent architecture for specialized task handling:

#### Core Agents

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

#### Agent Communication Pattern

```mermaid
graph LR
    DA[Data Acquisition Agent<br/>Ingestion] --> EB[Event Bus<br/>Redis Pub/Sub]
    EB --> AD[Anomaly Detection Agent<br/>ML Analysis]
    AD --> EB
    EB --> VA[Validation Agent<br/>Rule Engine]
    VA --> EB
    EB --> OA[Orchestrator Agent<br/>Coordinator]
    OA --> EB
    EB --> PA[Prediction Agent<br/>Prophet]
    PA --> EB
    EB --> SA[Scheduling Agent<br/>Optimization]
    SA --> EB
    EB --> NA[Notification Agent<br/>Alerts]
    NA --> EB
    EB --> RA[Reporting Agent<br/>Analytics]
    RA --> EB
    EB --> HIA[Human Interface Agent<br/>HITL]
    HIA --> EB
    EB --> LA[Learning Agent<br/>RAG/ChromaDB]
    LA --> EB
    EB --> MLA[Maintenance Log Agent<br/>History]
    EB --> DCA[Drift Check Agent<br/>Monitoring]
    DCA --> EB
    EB --> RTR[Retrain Agent<br/>Auto Update]
    RTR --> EB

    classDef agent fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px
    classDef eventbus fill:#880E4F,color:#ffffff,stroke:#440727,stroke-width:3px

    class DA,AD,VA,OA,PA,SA,NA,RA,HIA,LA,MLA,DCA,RTR agent
    class EB eventbus
```

### 3.4. Machine Learning Pipeline (Condensed)

#### Model Registry Status

- **Total Models:** 17+ production-ready models
- **Classification Models:** AI4I (99.90% accuracy), Kaggle Pump (100% accuracy)
- **Anomaly Detection:** NASA Bearing (72.8% accuracy), XJTU Bearing
- **Audio Processing:** MIMII Sound (93.3% accuracy)
- **Forecasting Models:** Prophet-based time-series prediction
- **Drift Monitoring:** Real-time model performance tracking and automated alerts
- **Intelligent Model Selection:** Context-aware model routing with performance optimization
- **Automated Retraining:** Event-driven pipeline for model updates based on drift detection

#### Model Categories

```mermaid
graph TD
    subgraph "Classification Models"
        AI4I[AI4I Industrial Failure<br/>99.90% Accuracy<br/>RandomForest]
        PUMP[Kaggle Pump Maintenance<br/>100% Accuracy<br/>XGBoost]
        MULTI[Multi-class Variants<br/>Ensemble Methods]
    end

    subgraph "Anomaly Detection"
        NASA[NASA Bearing Vibration<br/>72.8% Accuracy<br/>Isolation Forest]
        XJTU[XJTU Bearing Analysis<br/>Run-to-Failure<br/>Statistical]
        ISOLATION[Isolation Forest Ensemble<br/>Unsupervised Learning]
    end

    subgraph "Signal Processing"
        VIBRATION[Vibration Signal Analysis<br/>FFT Features]
        AUDIO[MIMII Audio<br/>93.3% Accuracy<br/>MFCC]
        FFT[FFT Feature Extraction<br/>Frequency Domain]
    end

    subgraph "Forecasting"
        PROPHET[Prophet Time Series<br/>Seasonal Decomposition]
        SEASONAL[Seasonal Decomposition<br/>Trend Analysis]
        TREND[Trend Analysis<br/>Maintenance Scheduling]
    end

    classDef classification fill:#0D47A1,color:#ffffff,stroke:#062a5e,stroke-width:3px
    classDef anomaly fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px
    classDef signal fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef forecast fill:#4A148C,color:#ffffff,stroke:#1a0632,stroke-width:3px

    class AI4I,PUMP,MULTI classification
    class NASA,XJTU,ISOLATION anomaly
    class VIBRATION,AUDIO,FFT signal
    class PROPHET,SEASONAL,TREND forecast
```

#### Drift Monitoring System

The system implements comprehensive model drift detection and automated response:

```mermaid
graph TD
    subgraph "Drift Detection Pipeline"
        DCA[Drift Check Agent<br/>Scheduled Monitoring]
        DETECT[Statistical Drift Detection<br/>KS Test + PSI]
        ALERT[Alert Generation<br/>Slack + Redis]
        RTR[Retrain Agent<br/>Auto Retraining]
    end

    subgraph "Intelligent Model Selection"
        ROUTER[Model Router<br/>Context-Aware]
        PERF[Performance Tracker<br/>Real-time Metrics]
        SELECT[Context-Aware Selection<br/>Best Model Choice]
    end

    DCA --> DETECT
    DETECT --> ALERT
    ALERT --> RTR
    ROUTER --> PERF
    PERF --> SELECT
    SELECT --> DCA

    classDef detection fill:#880E4F,color:#ffffff,stroke:#440727,stroke-width:3px
    classDef selection fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px

    class DCA,DETECT,ALERT,RTR detection
    class ROUTER,PERF,SELECT selection
```

**Key Features:**

- **Real-time Performance Tracking:** Continuous monitoring of model accuracy and prediction quality
- **Statistical Drift Detection:** Automated detection of data distribution changes
- **Event-driven Retraining:** Automatic model updates triggered by drift alerts
- **Model Performance Comparison:** Intelligent routing based on real-time performance metrics
- **Notification System:** Integration with system event bus for drift alerts

### 3.5. Event-Driven MLOps Automation (Overview)

Day 23 added a fully automated MLOps loop powered by the Redis-backed event bus, a Drift Check Agent, and a Retrain Agent.

```mermaid
flowchart LR
    subgraph Monitoring
        DCA[Drift Check Agent<br/>Every 6h]
        METRICS[(Performance Metrics<br/>Drift Tracking)]
    end
    subgraph Control
        EB[Redis Event Bus<br/>Pub/Sub]
        DLQ[Dead Letter Queue<br/>Failed Events]
    end
    subgraph Retraining
        RTR[Retrain Agent<br/>Event Consumer]
        JOB[Training Job<br/>Makefile]
        MLR[MLflow Registry<br/>S3 Artifacts]
    end
    subgraph Serving
        CACHE[(Model Cache<br/>In-Memory)]
        API[FastAPI Inference<br/>Endpoints]
    end
    subgraph Ops
        EMAIL[Email Notification<br/>Service]
        SLACK[Slack Webhook<br/>Alerts]
    end

    DCA --> METRICS
    DCA -->|DriftDetected| EB
    EB --> RTR
    RTR -->|start| JOB
    JOB -->|artifacts| MLR
    JOB -->|RetrainCompleted/Failed| EB
    EB --> EMAIL
    EB --> SLACK
    MLR -->|promote| CACHE
    CACHE --> API
    EB --> DLQ

    classDef mon fill:#004D40,color:#ffffff,stroke:#00251a,stroke-width:3px
    classDef bus fill:#880E4F,color:#ffffff,stroke:#440727,stroke-width:3px
    classDef rt fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef serve fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px
    classDef ops fill:#4A148C,color:#ffffff,stroke:#1a0632,stroke-width:3px

    class DCA,METRICS mon
    class EB,DLQ bus
    class RTR,JOB,MLR rt
    class CACHE,API serve
    class EMAIL,SLACK ops
```

Operational notes:

- Drift Check Agent publishes `DriftDetected` when monitored metrics breach thresholds.
- Retrain Agent executes training scripts, logs to MLflow, and emits `RetrainCompleted/Failed` events.
- Successful models are promoted in MLflow and pre-warmed into the model cache for safe rollout.
- Email Notification Service (`core/notifications/email_service.py`) dispatches drift and retraining notifications.

---

## 4. Security & Operational Excellence

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

### 4.3. Deployment & Environments

#### Microservice Migration Strategy

The system implements a comprehensive microservice scaffolding strategy for modular deployment:

**Service Decomposition Pattern:**

- **API Gateway:** Central routing and authentication service
- **ML Service:** Dedicated model inference and training service
- **Data Service:** Sensor data ingestion and processing
- **Agent Service:** Multi-agent workflow orchestration
- **Notification Service:** Event-driven notification management

**Implementation Benefits:**

- **Independent Scaling:** Each service can scale based on specific load patterns
- **Technology Diversity:** Services can use optimal technology stacks
- **Fault Isolation:** Service failures don't cascade across the system
- **Team Autonomy:** Different teams can own and deploy services independently

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

## 5. Scaling & Optimization

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

### 5.2. Scalability Analysis (Excerpt)

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

### 5.3. CI/CD Pipeline Hardening

#### Automated Testing Infrastructure

- **Unit Testing:** Comprehensive test coverage with pytest framework
- **Integration Testing:** End-to-end API testing with FastAPI TestClient
- **Load Testing:** Locust-based performance validation (103.8 RPS peak)
- **Security Testing:** Automated vulnerability scanning with Snyk integration
- **Chaos Engineering:** Resilience testing with failure injection and recovery validation

#### Pipeline Security

- **Dependency Scanning:** Automated vulnerability detection in CI/CD
- **Code Quality Gates:** Automated quality checks with linting and formatting
- **Environment Validation:** Script-based environment verification
- **Deployment Validation:** Automated health checks post-deployment

**CI Environment Features:**

- **Docker-based Testing:** Consistent testing environment across all stages
- **Parallel Test Execution:** Optimized test runtime with parallel processing
- **Automated Model Validation:** ML model performance regression testing
- **Deployment Rollback:** Automated rollback on failed deployments

---

## 6. Data Flow & Integration

### 6.1. Data Pipeline Architecture

```mermaid
flowchart LR
    subgraph "Data Sources"
        SENSORS[IoT Sensors<br/>Real-time]
        BATCH[Batch Imports<br/>CSV/JSON]
        EXTERNAL[External APIs<br/>Third-party]
    end

    subgraph "Ingestion Layer"
        VALIDATE[Schema Validation<br/>Pydantic]
        ENRICH[Data Enrichment<br/>Metadata]
        CORRELATION[ID Assignment<br/>Tracing]
    end

    subgraph "Processing Layer"
        EVENT_BUS[Event Bus<br/>Redis Pub/Sub]
        ML_PIPELINE[ML Processing<br/>Agents]
        BUSINESS_RULES[Business Logic<br/>Validation]
    end

    subgraph "Storage Layer"
        TIMESERIES[TimescaleDB<br/>Hypertables]
        CACHE[Redis Cache<br/>Hot Data]
        ARTIFACTS[MLflow Artifacts<br/>S3 Storage]
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

    classDef sources fill:#0D47A1,color:#ffffff,stroke:#062a5e,stroke-width:3px
    classDef ingestion fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px
    classDef processing fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef storage fill:#4A148C,color:#ffffff,stroke:#1a0632,stroke-width:3px

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

## 7. Architecture Decisions & Evolution

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

## 8. Conclusion (Lean)

The Smart Maintenance SaaS platform represents a production-ready, event-driven architecture optimized for industrial IoT applications. With proven performance characteristics exceeding SLO requirements by orders of magnitude and comprehensive ML capabilities validated against real-world datasets, the system demonstrates enterprise-grade reliability and scalability.

The platform's success in achieving 103.8 RPS throughput with sub-3ms response times, combined with its comprehensive security framework and operational excellence practices, positions it as a robust foundation for industrial predictive maintenance applications.

Key architectural strengths include the custom event bus design for low-latency processing, TimescaleDB optimization for time-series performance, comprehensive MLflow integration for model lifecycle management, and containerized deployment for operational simplicity.

### Appendix A: Agent Interaction Flow Diagram

```mermaid
sequenceDiagram
    participant API as API Gateway<br/>FastAPI
    participant DAA as Data Acquisition<br/>Agent
    participant EB as Event Bus<br/>Redis
    participant ADA as Anomaly Detection<br/>Agent
    participant VA as Validation Agent<br/>Rules
    participant OA as Orchestrator<br/>Coordinator
    participant PA as Prediction Agent<br/>Prophet
    participant SA as Scheduling Agent<br/>Optimizer
    participant NA as Notification Agent<br/>Alerts
    participant MLA as Maintenance Log<br/>History

    API->>+DAA: Sensor Data
    DAA->>DAA: Validate & Enrich
    DAA->>EB: DataProcessedEvent
    EB->>+ADA: Process Data
    ADA->>ADA: ML Analysis<br/>Isolation Forest
    ADA->>EB: AnomalyDetectedEvent
    EB->>+VA: Validate Anomaly
    VA->>VA: Apply Rules & Context<br/>False Positive Check
    VA->>EB: AnomalyValidatedEvent
    EB->>+OA: Orchestrate Decision
    OA->>OA: Decision Logic<br/>Routing
    OA->>EB: TriggerPredictionEvent
    EB->>+PA: Generate Prediction
    PA->>PA: Prophet Analysis<br/>Time-to-Failure
    PA->>EB: MaintenancePredictedEvent
    EB->>+SA: Schedule Maintenance
    SA->>SA: Optimize Schedule<br/>Resource Allocation
    SA->>EB: MaintenanceScheduledEvent
    EB->>+NA: Send Notifications
    NA->>NA: Multi-channel Notify<br/>Email/Slack
    EB->>+MLA: Log Maintenance
    MLA->>MLA: Record History<br/>Persistence
```

### Appendix B: Data Pipeline Architecture

```mermaid
flowchart LR
    subgraph "Data Ingestion"
        SENSORS[📡 IoT Sensors<br/>Real-time Streams]
        API_IN[🔌 API Endpoints<br/>REST/WebSocket]
        BATCH[📦 Batch Import<br/>CSV/JSON Files]
    end

    subgraph "Processing Pipeline"
        VALIDATE[✅ Data Validation<br/>Pydantic Schema]
        ENRICH[🔄 Data Enrichment<br/>Metadata Addition]
        NORMALIZE[⚖️ Normalization<br/>Standardization]
        ANOMALY[🔍 Anomaly Detection<br/>Isolation Forest]
    end

    subgraph "Storage & Analytics"
        TIMESERIES[(⏰ Time Series DB<br/>TimescaleDB)]
        VECTOR[(🧠 Vector DB<br/>ChromaDB)]
        WAREHOUSE[(🏢 Data Warehouse<br/>PostgreSQL)]
        CACHE[(⚡ Cache Layer<br/>Redis)]
    end

    subgraph "Machine Learning"
        TRAIN[🎓 Model Training<br/>Jupyter + MLflow]
        PREDICT[🔮 Predictions<br/>Real-time Inference]
        FEEDBACK[🔄 Feedback Loop<br/>Continuous Learning]
    end

    subgraph "Output Systems"
        DASHBOARD[📊 Dashboards<br/>Streamlit UI]
        ALERTS[🚨 Alerts<br/>Multi-channel]
        REPORTS[📈 Reports<br/>Analytics]
        API_OUT[📤 API Responses<br/>JSON/REST]
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

    classDef ingestion fill:#0D47A1,color:#ffffff,stroke:#062a5e,stroke-width:3px
    classDef processing fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px
    classDef storage fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef ml fill:#4A148C,color:#ffffff,stroke:#1a0632,stroke-width:3px
    classDef output fill:#880E4F,color:#ffffff,stroke:#440727,stroke-width:3px

    class SENSORS,API_IN,BATCH ingestion
    class VALIDATE,ENRICH,NORMALIZE,ANOMALY processing
    class TIMESERIES,VECTOR,WAREHOUSE,CACHE storage
    class TRAIN,PREDICT,FEEDBACK ml
    class DASHBOARD,ALERTS,REPORTS,API_OUT output
```

### Appendix C: Event-Driven Architecture Flow

```mermaid
graph TD
    subgraph "Event Sources"
        DATA_IN[📊 Data Ingestion<br/>Sensor Streams]
        USER_ACTION[👤 User Actions<br/>UI Interactions]
        SYSTEM_EVENT[⚙️ System Events<br/>Health/Status]
        TIMER[⏰ Scheduled Tasks<br/>Cron Jobs]
    end

    subgraph "Event Bus Core"
        ROUTER[📡 Event Router<br/>Topic-based]
        QUEUE[📬 Event Queue<br/>Redis Streams]
        DISPATCH[🚀 Event Dispatcher<br/>Pub/Sub]
    end

    subgraph "Event Processors"
        ANOMALY_PROC[🔍 Anomaly Processor<br/>ML Detection]
        VALIDATION_PROC[✅ Validation Processor<br/>Rule Engine]
        PREDICTION_PROC[🔮 Prediction Processor<br/>Prophet Model]
        SCHEDULE_PROC[📅 Schedule Processor<br/>Optimization]
        NOTIFY_PROC[📢 Notification Processor<br/>Multi-channel]
    end

    subgraph "Event Persistence"
        EVENT_LOG[(📜 Event Log<br/>Audit Trail)]
        METRICS[(📊 Event Metrics<br/>Performance)]
        AUDIT[(🔍 Audit Trail<br/>Compliance)]
    end

    subgraph "Event Consumers"
        DASHBOARD_SUB[📊 Dashboard Updates<br/>Real-time UI]
        ALERT_SUB[🚨 Alert System<br/>Notifications]
        REPORT_SUB[📈 Reporting<br/>Analytics]
        API_SUB[🔌 API Responses<br/>Client Apps]
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

    classDef source fill:#0D47A1,color:#ffffff,stroke:#062a5e,stroke-width:3px
    classDef core fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px
    classDef processor fill:#4A148C,color:#ffffff,stroke:#1a0632,stroke-width:3px
    classDef persistence fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef consumer fill:#880E4F,color:#ffffff,stroke:#440727,stroke-width:3px

    class DATA_IN,USER_ACTION,SYSTEM_EVENT,TIMER source
    class ROUTER,QUEUE,DISPATCH core
    class ANOMALY_PROC,VALIDATION_PROC,PREDICTION_PROC,SCHEDULE_PROC,NOTIFY_PROC processor
    class EVENT_LOG,METRICS,AUDIT persistence
    class DASHBOARD_SUB,ALERT_SUB,REPORT_SUB,API_SUB consumer
```

### Appendix D: Deployment Architecture (Future-Oriented Illustration)

```mermaid
graph TB
    subgraph "Load Balancer Layer"
        LB[⚖️ Load Balancer<br/>NGINX/HAProxy]
        SSL[🔒 SSL Termination<br/>TLS 1.3]
    end

    subgraph "Application Layer"
        subgraph "API Cluster"
            API1[🚀 FastAPI Instance 1<br/>Auto-scaling]
            API2[🚀 FastAPI Instance 2<br/>High Availability]
            API3[🚀 FastAPI Instance 3<br/>Load Distribution]
        end

        subgraph "Agent Cluster"
            AGENT1[🤖 Agent Pod 1<br/>Core Agents]
            AGENT2[🤖 Agent Pod 2<br/>MLOps Agents]
            AGENT3[🤖 Agent Pod 3<br/>Decision Agents]
        end

        subgraph "Worker Cluster"
            WORKER1[⚙️ Background Worker 1<br/>Async Tasks]
            WORKER2[⚙️ Background Worker 2<br/>Scheduled Jobs]
        end
    end

    subgraph "Data Layer"
        subgraph "Primary Database"
            DB_MASTER[(🗄️ PostgreSQL Master<br/>Write Operations)]
            DB_REPLICA[(📚 PostgreSQL Replica<br/>Read Operations)]
        end

        subgraph "Specialized Storage"
            TIMESCALE[(⏰ TimescaleDB<br/>Time-Series Data)]
            VECTOR[(🧠 ChromaDB<br/>Vector Embeddings)]
            REDIS[(⚡ Redis Cluster<br/>Cache & Events)]
        end
    end

    subgraph "Monitoring & Observability"
        METRICS[📊 Prometheus<br/>Metrics Collection]
        LOGS[📝 Elasticsearch<br/>Log Aggregation]
        GRAFANA[📈 Grafana<br/>Visualization]
        JAEGER[🔍 Jaeger Tracing<br/>Distributed Tracing]
    end

    subgraph "Infrastructure"
        DOCKER[🐳 Docker Swarm<br/>Container Orchestration]
        K8S[☸️ Kubernetes<br/>Production Workloads]
        STORAGE[💾 Persistent Volumes<br/>Data Persistence]
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

    classDef lb fill:#0D47A1,color:#ffffff,stroke:#062a5e,stroke-width:3px
    classDef app fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px
    classDef data fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef monitor fill:#4A148C,color:#ffffff,stroke:#1a0632,stroke-width:3px
    classDef infra fill:#880E4F,color:#ffffff,stroke:#440727,stroke-width:3px

    class LB,SSL lb
    class API1,API2,API3,AGENT1,AGENT2,AGENT3,WORKER1,WORKER2 app
    class DB_MASTER,DB_REPLICA,TIMESCALE,VECTOR,REDIS data
    class METRICS,LOGS,GRAFANA,JAEGER monitor
    class DOCKER,K8S,STORAGE infra
```

### Appendix E: Machine Learning Pipeline

```mermaid
flowchart TB
    subgraph "Data Collection"
        SENSORS[📡 Sensor Data<br/>IoT Streams]
        HISTORICAL[📚 Historical Data<br/>Archive Storage]
        FEEDBACK[🔄 Feedback Data<br/>User Input]
    end

    subgraph "Feature Engineering"
        EXTRACT[🔍 Feature Extraction<br/>FFT/MFCC/Statistical]
        TRANSFORM[🔄 Data Transformation<br/>Normalization]
        SELECT[✅ Feature Selection<br/>Importance Ranking]
    end

    subgraph "Model Training"
        ANOMALY_TRAIN[🎯 Anomaly Detection Training<br/>Isolation Forest]
        PROPHET_TRAIN[📈 Prophet Model Training<br/>Time-Series]
        VALIDATION_TRAIN[✅ Validation Model Training<br/>Rule-based]
    end

    subgraph "Model Deployment"
        ANOMALY_MODEL[🔍 Isolation Forest Model<br/>Unsupervised]
        PROPHET_MODEL[🔮 Prophet Predictor<br/>Forecasting]
        ENSEMBLE[🎭 Ensemble Decision<br/>Combined Confidence]
    end

    subgraph "Real-time Inference"
        STREAM_DATA[📊 Streaming Data<br/>Real-time Input]
        PREPROCESS[⚙️ Preprocessing<br/>Feature Extraction]
        INFERENCE[🧠 Model Inference<br/>Prediction]
        POSTPROCESS[🔧 Postprocessing<br/>Result Formatting]
    end

    subgraph "Model Management"
        MONITOR[📊 Model Monitoring<br/>Drift Detection]
        RETRAIN[🔄 Retraining Pipeline<br/>Auto-update]
        VERSIONING[📦 Model Versioning<br/>MLflow Registry]
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

    classDef collection fill:#0D47A1,color:#ffffff,stroke:#062a5e,stroke-width:3px
    classDef engineering fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px
    classDef training fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef deployment fill:#4A148C,color:#ffffff,stroke:#1a0632,stroke-width:3px
    classDef inference fill:#880E4F,color:#ffffff,stroke:#440727,stroke-width:3px
    classDef management fill:#37474F,color:#ffffff,stroke:#1b2529,stroke-width:3px

    class SENSORS,HISTORICAL,FEEDBACK collection
    class EXTRACT,TRANSFORM,SELECT engineering
    class ANOMALY_TRAIN,PROPHET_TRAIN,VALIDATION_TRAIN training
    class ANOMALY_MODEL,PROPHET_MODEL,ENSEMBLE deployment
    class STREAM_DATA,PREPROCESS,INFERENCE,POSTPROCESS inference
    class MONITOR,RETRAIN,VERSIONING management
```

---

## (Removed Redundant Legacy Section)

The previous duplicate "System Architecture" narrative has been superseded by Sections 1–3 above; retention here would create drift risk. See unified doc for deep agent taxonomy.

<!-- Legacy granular component descriptions removed to prevent duplication. Core components summarized earlier. -->

#### a. API Gateway (FastAPI)

The **API Gateway**, built with FastAPI, is the primary entry point for all external interactions. It handles API requests, authentication, rate limiting, and routes them to the appropriate services within the system.

#### b. Event Bus

The `EventBus` is a custom, in-memory, asynchronous messaging system that enables decoupled communication between agents. It allows agents to publish events and subscribe to events they are interested in, forming the backbone of the event-driven architecture. The event bus includes retry logic, dead letter queues, and correlation ID propagation.

#### c. Multi-Agent System

This is the core of the platform, consisting of eleven specialized agents that work together to perform complex tasks. Each agent is designed to be autonomous and responsible for a specific part of the workflow. All agents communicate through the central Event Bus.

#### d. Database Layer (PostgreSQL with TimescaleDB)

A **PostgreSQL** database with the **TimescaleDB** extension is used for data persistence. TimescaleDB is optimized for time-series data, making it ideal for storing sensor readings with continuous aggregates and automatic compression.

#### e. Vector Database (ChromaDB)

**ChromaDB** is used by the LearningAgent for implementing RAG (Retrieval-Augmented Generation) capabilities, enabling the system to learn from historical data and provide context-aware insights.

#### f. MLflow Model Registry

**MLflow** provides complete model lifecycle management with artifact storage, experiment tracking, and model versioning. Models are cached for high-performance inference in production.

<!-- Detailed agent description table consolidated in unified doc (single source). -->

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

<!-- High-level diagram earlier; avoiding repetition. -->

```mermaid
graph TD
    subgraph "External Interfaces"
        UI[User Interface / API Clients<br/>Web/Mobile Apps]
    end

    subgraph "Backend System"
        API[API Gateway - FastAPI<br/>Rate Limiting & Auth]
        EventBus[Event Bus<br/>Redis Pub/Sub + DLQ]

        subgraph "Agents"
            DAA[Data Acquisition Agent<br/>Ingestion]
            ADA[Anomaly Detection Agent<br/>ML Analysis]
            VA[Validation Agent<br/>Rule Engine]
            Orch[Orchestrator Agent<br/>Coordinator]
            PA[Prediction Agent<br/>Prophet]
            SA[Scheduling Agent<br/>Optimization]
            NA[Notification Agent<br/>Alerts]
            HIA[Human Interface Agent<br/>HITL]
            RA[Reporting Agent<br/>Analytics]
            LA[Learning Agent<br/>RAG/ChromaDB]
            MLA[Maintenance Log Agent<br/>History]
        end

        subgraph "Data Persistence"
            DB[(PostgreSQL with TimescaleDB<br/>Time-Series Storage)]
            VDB[(ChromaDB Vector DB<br/>RAG Embeddings)]
            MLF[(MLflow Model Registry<br/>S3 Artifacts)]
        end
    end

    UI --> API
    API --> EventBus

    EventBus --> DAA
    EventBus --> ADA
    EventBus --> VA
    EventBus --> Orch
    EventBus --> PA
    EventBus --> SA
    EventBus --> NA
    EventBus --> HIA
    EventBus --> RA
    EventBus --> LA
    EventBus --> MLA

    DAA --> EventBus
    ADA --> EventBus
    VA --> EventBus
    Orch --> EventBus
    PA --> EventBus
    SA --> EventBus
    NA --> EventBus
    HIA --> EventBus
    RA --> EventBus
    LA --> EventBus
    MLA --> EventBus

    DAA --> DB
    VA --> DB
    PA --> DB
    MLA --> DB
    RA --> DB
    LA --> VDB
    ADA --> MLF
    PA --> MLF

    classDef api fill:#4A148C,color:#ffffff,stroke:#1a0632,stroke-width:3px
    classDef agent fill:#1B5E20,color:#ffffff,stroke:#0d2f10,stroke-width:3px
    classDef eventbus fill:#E65100,color:#ffffff,stroke:#732800,stroke-width:3px
    classDef database fill:#0D47A1,color:#ffffff,stroke:#062a5e,stroke-width:3px

    class UI,API api
    class DAA,ADA,VA,Orch,PA,SA,NA,HIA,RA,LA,MLA agent
    class EventBus eventbus
    class DB,VDB,MLF database
```

<!-- Data flow covered in Section 6 + Appendix. -->

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

## 9. Architectural Decisions & Future Enhancements (Focused)

### 9.1. Plan vs Implementation Highlights

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



### 9.2. Machine Learning Notes (Pointer)

Deep dive moved to ML domain docs and unified document; this section retained only for orientation.

Our machine learning implementation is comprehensive and production-ready, fully aligned with the project's goals.

**Anomaly Detection:** We implemented a robust dual-approach system using `IsolationForest`, an unsupervised learning algorithm ideal for anomaly detection because it doesn't require pre-labeled data. This is combined with a `StatisticalAnomalyDetector` that uses Z-score analysis (based on historical mean and standard deviation) to catch numerical outliers. This hybrid, ensemble approach provides nuanced confidence scores for detected anomalies and is fully integrated with MLflow for model versioning and caching.

**Prediction:** The `PredictionAgent` is fully implemented using Facebook `Prophet`. Prophet excels at business forecasting tasks like predictive maintenance because it handles missing data gracefully, automatically manages trends and seasonality, and provides interpretable forecasts. The models are versioned and cached through MLflow for high-performance inference.

**Model Registry & MLflow Integration:** We successfully implemented a complete MLflow infrastructure with:

- **SQLite backend** for metadata persistence across container restarts
- **File-based artifact storage** with `/mlruns` volume mounting
- **Model versioning and tagging** for intelligent model selection
- **Comprehensive caching** for sub-millisecond model loading
- **Feature schema validation** with `feature_names.txt` artifacts
- **Production model registry** with 17+ trained models across multiple domains

**Real-World Dataset Validation:** The system has been thoroughly validated against five industrial datasets (AI4I, NASA, XJTU, MIMII, Kaggle) with documented performance metrics and automated drift monitoring.

### 9.3. Rationale for Multi-Agent Framework (Summary)

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

### Change Log (This Document)

| Date | Change | Author |
|------|--------|--------|
| 2025-09-25 | Refactored for V1.0: deduplicated content, added status snapshot, minimized performance + agent repetition, added appendices. | AI Assistant |

---
Document Classification: Stable Reference (update only when architecture materially changes). Performance numbers should not be edited here—update source performance docs instead.
