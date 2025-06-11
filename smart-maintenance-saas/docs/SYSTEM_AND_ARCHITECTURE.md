# Smart Maintenance SaaS - System and Architecture

🇧🇷 **[Clique aqui para ler em Português](#-smart-maintenance-saas---sistema-e-arquitetura-português)** | 🇺🇸 **English Version Below**

## 📚 Documentation Navigation

This document is part of the Smart Maintenance SaaS documentation suite. For complete system understanding, please also refer to:

- **[Backend README](../README.md)** - Docker deployment and getting started guide
- **[Deployment Status](./DEPLOYMENT_STATUS.md)** - Current deployment status and container information
- **[API Documentation](./api.md)** - Complete REST API reference and usage examples  
- **[Performance Baseline](./PERFORMANCE_BASELINE.md)** - Load testing results and performance metrics baseline
- **[Load Testing Instructions](./LOAD_TESTING_INSTRUCTIONS.md)** - Comprehensive guide for running performance tests
- **[System Screenshots](./SYSTEM_SCREENSHOTS.md)** - Complete system demonstration with visual documentation
- **[Future Roadmap](./FUTURE_ROADMAP.md)** - Planned enhancements and architectural evolution
- **[Test Documentation](../tests/README.md)** - Test organization and execution guide
- **[Logging Configuration](../core/logging_config.md)** - Structured JSON logging setup and configuration
- **[Configuration Management](../core/config/README.md)** - Centralized configuration system using Pydantic BaseSettings
- **[Original Architecture](./original_full_system_architecture.md)** - Complete Phase 1 documentation and initial system design
- **[Project Overview](../../README.md)** - High-level project description and objectives

---

## 1. Introduction

This document provides a comprehensive overview of the system architecture for the Smart Maintenance SaaS platform. The platform is designed as a cloud-native, multi-agent system that leverages an event-driven architecture to deliver a modular, scalable, and resilient solution for predictive maintenance in the industrial sector.

### 1.1. Project Objectives

The primary goal of this project is to create a sophisticated backend system that can:

- **Ingest and Process Real-Time IoT Data:** Handle high volumes of sensor data from industrial equipment.
- **Detect and Validate Anomalies:** Use a combination of machine learning and statistical models to identify potential issues and validate them to reduce false positives.
- **Predict Failures:** Forecast potential equipment failures and estimate the time to failure (TTF).
- **Automate Maintenance Workflows:** Orchestrate the entire maintenance lifecycle, from anomaly detection to scheduling and logging completed tasks.
- **Learn and Adapt:** Continuously improve its performance by learning from system feedback and historical data.

---

## 🎯 2. System Architecture Visualizations

This section provides multiple perspectives on the Smart Maintenance SaaS architecture through comprehensive diagrams. Each diagram focuses on different aspects of the system to provide a complete understanding.

### 📊 2.1. High-Level System Overview

```mermaid
graph TB
    subgraph "External Systems"
        IOT[🏭 IoT Sensors]
        USERS[👥 Users/Dashboard]
        MOBILE[📱 Mobile Apps]
    end

    subgraph "API Layer"
        LB[⚖️ Load Balancer]
        API[🚀 FastAPI Gateway]
        AUTH[🔐 Authentication]
    end

    subgraph "Core Processing"
        COORD[🎯 System Coordinator]
        EVENT[📡 Event Bus]
        AGENTS[🤖 Multi-Agent System]
    end

    subgraph "Data Layer"
        TS[(⏰ TimescaleDB)]
        VEC[(🧠 ChromaDB)]
        CACHE[(⚡ Redis Cache)]
    end

    subgraph "Infrastructure"
        DOCKER[🐳 Docker Containers]
        MONITOR[📊 Monitoring]
        LOGS[📝 Centralized Logging]
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
    AGENTS --> VEC
    AGENTS --> CACHE
    COORD --> DOCKER
    AGENTS --> MONITOR
    EVENT --> LOGS

    classDef external fill:#e1f5fe
    classDef api fill:#f3e5f5
    classDef core fill:#e8f5e8
    classDef data fill:#fff3e0
    classDef infra fill:#fce4ec

    class IOT,USERS,MOBILE external
    class LB,API,AUTH api
    class COORD,EVENT,AGENTS core
    class TS,VEC,CACHE data
    class DOCKER,MONITOR,LOGS infra
```

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

## Smart Maintenance SaaS - Sistema e Arquitetura (Português)

## 📚 Navegação da Documentação

Este documento faz parte da suíte de documentação do Smart Maintenance SaaS. Para um entendimento completo do sistema, consulte também:

- **[README do Backend](../README.md)** - Guia de implantação Docker e introdução
- **[Status de Implantação](./DEPLOYMENT_STATUS.md)** - Status atual de implantação e informações do container
- **[Documentação da API](./api.md)** - Referência completa da API REST e exemplos de uso
- **[Baseline de Performance](./PERFORMANCE_BASELINE.md)** - Resultados de testes de carga e baseline de métricas de performance
- **[Instruções de Teste de Carga](./LOAD_TESTING_INSTRUCTIONS.md)** - Guia abrangente para executar testes de performance
- **[Capturas de Tela do Sistema](./SYSTEM_SCREENSHOTS.md)** - Demonstração completa do sistema com documentação visual
- **[Roadmap Futuro](./FUTURE_ROADMAP.md)** - Melhorias planejadas e evolução arquitetural
- **[Documentação de Testes](../tests/README.md)** - Organização de testes e guia de execução
- **[Configuração de Logging](../core/logging_config.md)** - Configuração de logging JSON estruturado
- **[Gerenciamento de Configuração](../core/config/README.md)** - Sistema de configuração centralizado usando Pydantic BaseSettings
- **[Arquitetura Original](./original_full_system_architecture.md)** - Documentação completa da Fase 1 e design inicial do sistema
- **[Visão Geral do Projeto](../../README.md)** - Descrição de alto nível e objetivos do projeto

---

## 1. Introdução

Este documento fornece uma visão geral abrangente da arquitetura de sistema para a plataforma Smart Maintenance SaaS. A plataforma foi projetada como um sistema multi-agente nativo da nuvem, que utiliza uma arquitetura orientada a eventos para fornecer uma solução modular, escalável e resiliente para manutenção preditiva no setor industrial.

### 1.1. Objetivos do Projeto

O objetivo principal deste projeto é criar um sistema backend sofisticado que possa:

- **Ingerir e Processar Dados IoT em Tempo Real:** Lidar com grandes volumes de dados de sensores de equipamentos industriais.
- **Detectar e Validar Anomalias:** Usar uma combinação de aprendizado de máquina e modelos estatísticos para identificar problemas potenciais e validá-los para reduzir falsos positivos.
- **Prever Falhas:** Prever falhas potenciais de equipamentos e estimar o tempo até a falha (TTF).
- **Automatizar Fluxos de Trabalho de Manutenção:** Orquestrar todo o ciclo de vida da manutenção, desde a detecção de anomalias até o agendamento e registro de tarefas concluídas.
- **Aprender e Adaptar:** Melhorar continuamente seu desempenho aprendendo com o feedback do sistema e dados históricos.

---

## 🎯 2. Visualizações da Arquitetura do Sistema

Esta seção fornece múltiplas perspectivas da arquitetura do Smart Maintenance SaaS através de diagramas abrangentes. Cada diagrama foca em diferentes aspectos do sistema para fornecer uma compreensão completa.

### 📊 2.1. Visão Geral do Sistema de Alto Nível

```mermaid
graph TB
    subgraph "Sistemas Externos"
        IOT[🏭 Sensores IoT]
        USERS[👥 Usuários/Dashboard]
        MOBILE[📱 Aplicativos Móveis]
    end

    subgraph "Camada API"
        LB[⚖️ Balanceador de Carga]
        API[🚀 Gateway FastAPI]
        AUTH[🔐 Autenticação]
    end

    subgraph "Processamento Central"
        COORD[🎯 Coordenador do Sistema]
        EVENT[📡 Barramento de Eventos]
        AGENTS[🤖 Sistema Multi-Agente]
    end

    subgraph "Camada de Dados"
        TS[(⏰ TimescaleDB)]
        VEC[(🧠 ChromaDB)]
        CACHE[(⚡ Cache Redis)]
    end

    subgraph "Infraestrutura"
        DOCKER[🐳 Containers Docker]
        MONITOR[📊 Monitoramento]
        LOGS[📝 Logging Centralizado]
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
    AGENTS --> VEC
    AGENTS --> CACHE
    COORD --> DOCKER
    AGENTS --> MONITOR
    EVENT --> LOGS

    classDef external fill:#e1f5fe
    classDef api fill:#f3e5f5
    classDef core fill:#e8f5e8
    classDef data fill:#fff3e0
    classDef infra fill:#fce4ec

    class IOT,USERS,MOBILE external
    class LB,API,AUTH api
    class COORD,EVENT,AGENTS core
    class TS,VEC,CACHE data
    class DOCKER,MONITOR,LOGS infra
```

### 🔄 2.2. Diagrama de Fluxo de Interação dos Agentes

```mermaid
sequenceDiagram
    participant API as Gateway API
    participant DAA as Aquisição de Dados
    participant EB as Barramento de Eventos
    participant ADA as Detecção de Anomalias
    participant VA as Agente de Validação
    participant OA as Orquestrador
    participant PA as Agente de Previsão
    participant SA as Agente de Agendamento
    participant NA as Agente de Notificação
    participant MLA as Log de Manutenção

    API->>+DAA: Dados do Sensor
    DAA->>DAA: Validar e Enriquecer
    DAA->>EB: DataProcessedEvent
    EB->>+ADA: Processar Dados
    ADA->>ADA: Análise ML
    ADA->>EB: AnomalyDetectedEvent
    EB->>+VA: Validar Anomalia
    VA->>VA: Aplicar Regras e Contexto
    VA->>EB: AnomalyValidatedEvent
    EB->>+OA: Orquestrar Decisão
    OA->>OA: Lógica de Decisão
    OA->>EB: TriggerPredictionEvent
    EB->>+PA: Gerar Previsão
    PA->>PA: Análise Prophet
    PA->>EB: MaintenancePredictedEvent
    EB->>+SA: Agendar Manutenção
    SA->>SA: Otimizar Agenda
    SA->>EB: MaintenanceScheduledEvent
    EB->>+NA: Enviar Notificações
    NA->>NA: Notificar Multi-canal
    EB->>+MLA: Registrar Manutenção
    MLA->>MLA: Gravar Histórico
```

### 🌊 2.3. Arquitetura do Pipeline de Dados

```mermaid
flowchart LR
    subgraph "Ingestão de Dados"
        SENSORS[📡 Sensores IoT]
        API_IN[🔌 Endpoints da API]
        BATCH[📦 Importação em Lote]
    end

    subgraph "Pipeline de Processamento"
        VALIDATE[✅ Validação de Dados]
        ENRICH[🔄 Enriquecimento de Dados]
        NORMALIZE[⚖️ Normalização]
        ANOMALY[🔍 Detecção de Anomalias]
    end

    subgraph "Armazenamento e Analytics"
        TIMESERIES[(⏰ BD de Séries Temporais)]
        VECTOR[(🧠 BD Vetorial)]
        WAREHOUSE[(🏢 Data Warehouse)]
        CACHE[(⚡ Camada de Cache)]
    end

    subgraph "Machine Learning"
        TRAIN[🎓 Treinamento de Modelo]
        PREDICT[🔮 Previsões]
        FEEDBACK[🔄 Loop de Feedback]
    end

    subgraph "Sistemas de Saída"
        DASHBOARD[📊 Dashboards]
        ALERTS[🚨 Alertas]
        REPORTS[📈 Relatórios]
        API_OUT[📤 Respostas da API]
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

### ⚡ 2.4. Fluxo da Arquitetura Orientada a Eventos

```mermaid
graph TD
    subgraph "Fontes de Eventos"
        DATA_IN[📊 Ingestão de Dados]
        USER_ACTION[👤 Ações do Usuário]
        SYSTEM_EVENT[⚙️ Eventos do Sistema]
        TIMER[⏰ Tarefas Agendadas]
    end

    subgraph "Núcleo do Barramento de Eventos"
        ROUTER[📡 Roteador de Eventos]
        QUEUE[📬 Fila de Eventos]
        DISPATCH[🚀 Despachador de Eventos]
    end

    subgraph "Processadores de Eventos"
        ANOMALY_PROC[🔍 Processador de Anomalias]
        VALIDATION_PROC[✅ Processador de Validação]
        PREDICTION_PROC[🔮 Processador de Previsão]
        SCHEDULE_PROC[📅 Processador de Agendamento]
        NOTIFY_PROC[📢 Processador de Notificação]
    end

    subgraph "Persistência de Eventos"
        EVENT_LOG[(📜 Log de Eventos)]
        METRICS[(📊 Métricas de Eventos)]
        AUDIT[(🔍 Trilha de Auditoria)]
    end

    subgraph "Consumidores de Eventos"
        DASHBOARD_SUB[📊 Atualizações do Dashboard]
        ALERT_SUB[🚨 Sistema de Alertas]
        REPORT_SUB[📈 Relatórios]
        API_SUB[🔌 Respostas da API]
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

### 🏗️ 2.5. Arquitetura de Implantação

```mermaid
graph TB
    subgraph "Camada de Balanceador de Carga"
        LB[⚖️ Balanceador de Carga]
        SSL[🔒 Terminação SSL]
    end

    subgraph "Camada de Aplicação"
        subgraph "Cluster API"
            API1[🚀 Instância FastAPI 1]
            API2[🚀 Instância FastAPI 2]
            API3[🚀 Instância FastAPI 3]
        end

        subgraph "Cluster de Agentes"
            AGENT1[🤖 Pod de Agente 1]
            AGENT2[🤖 Pod de Agente 2]
            AGENT3[🤖 Pod de Agente 3]
        end

        subgraph "Cluster de Workers"
            WORKER1[⚙️ Worker em Background 1]
            WORKER2[⚙️ Worker em Background 2]
        end
    end

    subgraph "Camada de Dados"
        subgraph "Banco de Dados Primário"
            DB_MASTER[(🗄️ PostgreSQL Master)]
            DB_REPLICA[(📚 PostgreSQL Replica)]
        end

        subgraph "Armazenamento Especializado"
            TIMESCALE[(⏰ TimescaleDB)]
            VECTOR[(🧠 ChromaDB)]
            REDIS[(⚡ Cluster Redis)]
        end
    end

    subgraph "Monitoramento e Observabilidade"
        METRICS[📊 Prometheus]
        LOGS[📝 Elasticsearch]
        GRAFANA[📈 Grafana]
        JAEGER[🔍 Jaeger Tracing]
    end

    subgraph "Infraestrutura"
        DOCKER[🐳 Docker Swarm]
        K8S[☸️ Kubernetes]
        STORAGE[💾 Volumes Persistentes]
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

### 🧠 2.6. Pipeline de Machine Learning

```mermaid
flowchart TB
    subgraph "Coleta de Dados"
        SENSORS[📡 Dados de Sensores]
        HISTORICAL[📚 Dados Históricos]
        FEEDBACK[🔄 Dados de Feedback]
    end

    subgraph "Engenharia de Features"
        EXTRACT[🔍 Extração de Features]
        TRANSFORM[🔄 Transformação de Dados]
        SELECT[✅ Seleção de Features]
    end

    subgraph "Treinamento de Modelos"
        ANOMALY_TRAIN[🎯 Treinamento de Detecção de Anomalias]
        PROPHET_TRAIN[📈 Treinamento do Modelo Prophet]
        VALIDATION_TRAIN[✅ Treinamento do Modelo de Validação]
    end

    subgraph "Implantação de Modelos"
        ANOMALY_MODEL[🔍 Modelo Isolation Forest]
        PROPHET_MODEL[🔮 Preditor Prophet]
        ENSEMBLE[🎭 Decisão Ensemble]
    end

    subgraph "Inferência em Tempo Real"
        STREAM_DATA[📊 Dados em Streaming]
        PREPROCESS[⚙️ Pré-processamento]
        INFERENCE[🧠 Inferência do Modelo]
        POSTPROCESS[🔧 Pós-processamento]
    end

    subgraph "Gerenciamento de Modelos"
        MONITOR[📊 Monitoramento de Modelos]
        RETRAIN[🔄 Pipeline de Re-treinamento]
        VERSIONING[📦 Versionamento de Modelos]
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

## 3. Arquitetura e Componentes Principais

A arquitetura é projetada em torno de um sistema multi-agente, onde agentes especializados executam tarefas específicas. Esses agentes se comunicam de forma assíncrona através de um Barramento de Eventos (Event Bus), criando um sistema desacoplado e altamente escalável.

### 3.1. Gateway da API (FastAPI)

O Gateway da API, construído com FastAPI, é o ponto de entrada principal para todas as interações externas. Ele lida com as requisições da API, autenticação e as encaminha para os serviços apropriados dentro do sistema.

### 3.2. Coordenador do Sistema (SystemCoordinator)

O SystemCoordinator é o sistema nervoso central da plataforma. Ele gerencia o ciclo de vida de todos os agentes, garantindo que sejam iniciados e parados de forma elegante. Ele também serve como um ponto central para serviços e configurações de todo o sistema.

### 3.3. Barramento de Eventos (EventBus)

O EventBus é um sistema de mensagens assíncrono personalizado, em memória, que permite a comunicação desacoplada entre os agentes. Ele permite que os agentes publiquem eventos e se inscrevam nos eventos de seu interesse, formando a espinha dorsal da arquitetura orientada a eventos.

### 3.4. Sistema Multi-Agente

Este é o núcleo da plataforma, consistindo em vários agentes especializados que trabalham juntos para realizar tarefas complexas. Cada agente é projetado para ser autônomo e responsável por uma parte específica do fluxo de trabalho.

### 3.5. Banco de Dados (PostgreSQL com TimescaleDB)

Um banco de dados PostgreSQL com a extensão TimescaleDB é usado para a persistência de dados. O TimescaleDB é otimizado para dados de séries temporais, tornando-o ideal para armazenar leituras de sensores.

### 4. Descrição dos Agentes

| Agente | Papel e Responsabilidades |
| ------ | ------------------------- |
| **DataAcquisitionAgent** | Ingesta dados brutos de sensores, valida sua estrutura e qualidade, enriquece-os com contexto adicional e os publica para processamento posterior. |
| **AnomalyDetectionAgent** | Inscreve-se para receber dados processados e utiliza uma abordagem de método duplo (Isolation Forest e modelos estatísticos) para detectar anomalias. Calcula uma pontuação de confiança para cada anomalia potencial. |
| **ValidationAgent** | Recebe anomalias detectadas e as valida aplicando um motor de regras e analisando o contexto histórico para reduzir falsos positivos. Ajusta a pontuação de confiança e atribui um status de validação. |
| **OrchestratorAgent** | O coordenador central do fluxo de trabalho. Ouve eventos de vários agentes e toma decisões sobre os próximos passos, como escalar para um humano ou acionar ações automatizadas, como o agendamento de manutenção. |
| **PredictionAgent** | Utiliza a biblioteca de aprendizado de máquina Prophet para analisar dados históricos de uma anomalia validada e prever o Tempo Até a Falha (TTF). Gera recomendações de manutenção com base em suas previsões. |
| **SchedulingAgent** | Pega as previsões de manutenção e agenda as tarefas necessárias. Utiliza um algoritmo de otimização simplificado para atribuir técnicos e encontrar horários disponíveis. |
| **NotificationAgent** | Envia notificações para técnicos e partes interessadas sobre manutenções agendadas e outros eventos importantes do sistema. |
| **HumanInterfaceAgent** | Gerencia os pontos de decisão humano-no-ciclo. Simula a interação humana para decisões críticas que requerem aprovação ou entrada que não pode ser totalmente automatizada. |
| **ReportingAgent** | Gera relatórios analíticos, visualizações e insights acionáveis relacionados às operações de manutenção, saúde do equipamento e desempenho do sistema. |
| **LearningAgent** | Implementa um sistema de Geração Aumentada por Recuperação (RAG) usando ChromaDB e SentenceTransformers. Aprende com o feedback do sistema e os registros de manutenção para fornecer insights com reconhecimento de contexto e melhorar a precisão do sistema ao longo do tempo. |
| **MaintenanceLogAgent** | Inscreve-se em eventos de conclusão de manutenção e registra os detalhes no banco de dados, fechando o ciclo do fluxo de trabalho de manutenção e fornecendo um registro histórico de todas as atividades de manutenção. |

### 5. Diagrama da Arquitetura do Sistema

```mermaid
graph TD
    subgraph "Interfaces Externas"
        UI[Interface do Usuário / Clientes da API]
    end

    subgraph "Sistema Backend"
        API[Gateway da API - FastAPI]
        EventBus[Barramento de Eventos]
        SystemCoordinator[Coordenador do Sistema]

        subgraph "Agentes"
            DAA[Agente de Aquisição de Dados]
            ADA[Agente de Detecção de Anomalias]
            VA[Agente de Validação]
            Orch[Agente Orquestrador]
            PA[Agente de Previsão]
            SA[Agente de Agendamento]
            NA[Agente de Notificação]
            HIA[Agente de Interface Humana]
            RA[Agente de Relatórios]
            LA[Agente de Aprendizado]
            MLA[Agente de Log de Manutenção]
        end

        subgraph "Persistência de Dados"
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

### 6. Fluxo de Dados

1. **Ingestão:** Os dados do sensor são enviados para o Gateway da API e ingeridos pelo DataAcquisitionAgent.
2. **Processamento:** Os dados são validados, enriquecidos e armazenados no TimescaleDB. Um evento DataProcessedEvent é publicado.
3. **Detecção de Anomalias:** O AnomalyDetectionAgent detecta anomalias potenciais e publica um AnomalyDetectedEvent.
4. **Validação:** O ValidationAgent valida a anomalia e publica um AnomalyValidatedEvent.
5. **Orquestração:** O OrchestratorAgent recebe a anomalia validada e decide os próximos passos.
6. **Previsão:** Se a anomalia é credível, o OrchestratorAgent pode acionar o PredictionAgent, que prevê o tempo até a falha e publica um MaintenancePredictedEvent.
7. **Agendamento:** O SchedulingAgent agenda a tarefa de manutenção e publica um MaintenanceScheduledEvent.
8. **Notificação:** O NotificationAgent envia notificações sobre a tarefa agendada.
9. **Registro:** Uma vez que a manutenção é concluída, o MaintenanceLogAgent registra os detalhes no banco de dados.
10. **Aprendizado:** O LearningAgent aprende continuamente com o feedback e os registros de manutenção para melhorar o sistema.

---

## 7. Decisões Arquiteturais e Melhorias Futuras (Português)

### 7.1. Evolução do Projeto: Plano vs. Implementação

Esta lista de verificação fornece uma análise transparente das funcionalidades e tecnologias delineadas no "Plano Backend Hermes" inicial versus o que foi efetivamente implementado no código durante o sprint de 14 dias. A coluna "Minha Opinião" oferece minha justificativa para as decisões arquiteturais que tomei.

| Componente | Planejado no "Plano Backend Hermes" | Implementado no Código | Minha Opinião |
| :--- | :--- | :--- | :--- |
| **API & Gateway** | FastAPI, GraphQL, Hub WebSocket. | FastAPI (apenas REST API). A API é funcional com endpoints para ingestão, relatórios e decisões. | **Boa decisão.** Optei por não implementar GraphQL e WebSockets pois seria um esforço significativo. Uma API REST padrão é mais que suficiente para nossa funcionalidade principal e entregáveis. Vou manter assim. |
| **Event Streaming** | Apache Kafka, Redis Streams, Event Sourcing. | `EventBus` customizado em memória. Meu `core/events/event_bus.py` é um sistema pub/sub assíncrono personalizado. | **Excelente trade-off.** Este foi meu desvio arquitetural mais significativo, e tenho certeza que foi a escolha certa. Uma configuração completa do Kafka seria muito complexa. Meu event bus personalizado alcança o desacoplamento necessário para os agentes funcionarem de maneira orientada a eventos, que era meu objetivo principal. |
| **Agent Workflow** | Temporal.io, LangGraph, Service Mesh. | Orquestração implícita via `OrchestratorAgent` e assinaturas diretas de eventos entre agentes. | **Escolha pragmática.** Como o Kafka, decidi que um motor de workflow completo como Temporal.io seria desnecessário para este sprint. Meu `OrchestratorAgent` serve efetivamente a este propósito para o escopo atual. |
| **ML: Previsão** | Prophet e LSTM para previsão combinada. | Prophet apenas. O `PredictionAgent` está totalmente implementado usando a biblioteca Prophet. | **Suficiente e forte.** Escolhi Prophet pois é um modelo de previsão poderoso por si só. Adicionar LSTM aumentaria a complexidade para ganhos potencialmente marginais neste prazo. O que implementei é robusto e atende ao objetivo de predição. |
| **ML: Detecção de Anomalias** | Scikit-learn (IsolationForest), Modelos Estatísticos, Autoencoder, métodos Ensemble. | Scikit-learn (IsolationForest) e Modelos Estatísticos estão totalmente implementados no `AnomalyDetectionAgent` com um método de decisão ensemble. | **Totalmente alinhado.** Implementei com sucesso o núcleo do sistema de detecção de anomalias planejado. Deixei de fora os autoencoders pois são complexos e não necessários para um protótipo funcional. |
| **ML: Aprendizado (RAG)** | RAG com ChromaDB e MLflow para MLOps. | RAG com ChromaDB e SentenceTransformers está implementado no `LearningAgent`. MLflow não é usado. | **Excelente trabalho.** Priorizei implementar a parte RAG pois é uma funcionalidade importante. Omiti o MLflow pois é uma ferramenta MLOps para rastreamento de experimentos e não é crítica para a funcionalidade principal do backend. |
| **Agendamento** | OR-Tools para otimização com restrições. | A dependência `ortools` está no `pyproject.toml`, mas o `SchedulingAgent` usa uma lógica "greedy" simplificada. O código OR-Tools está comentado. | **Parcialmente implementado.** Esta é a única área onde minha implementação está incompleta, mas estabeleci a base. Dados os constrangimentos de tempo, usei uma abordagem greedy como um placeholder funcional. |
| **Bancos de Dados** | TimescaleDB, Vector DB (Chroma), Redis. | TimescaleDB e ChromaDB são ambos usados. Redis está instalado mas não usado ativamente para cache ou rate-limiting ainda. | **Excelente.** Implementei as duas tecnologias de banco de dados mais críticas e inovadoras do plano. O cache Redis é uma otimização que posso adicionar depois. |

### 7.2. Aprofundamento na Implementação de Machine Learning


Nossa implementação de machine learning é sólida e se alinha bem com os objetivos do projeto.

**Detecção de Anomalias:** Estamos usando `IsolationForest`, um algoritmo de aprendizado não supervisionado poderoso, ideal para este caso de uso porque não requer dados pré-rotulados de "anomalias" para treinar. É altamente eficaz em encontrar pontos de dados incomuns em conjuntos de dados de alta dimensionalidade. Combinamos corretamente isso com um `StatisticalAnomalyDetector` que usa análise Z-score (baseada na média histórica e desvio padrão) para capturar outliers numéricos mais óbvios. Esta abordagem híbrida, ensemble, é robusta e fornece uma pontuação de confiança nuançada para anomalias detectadas.

**Previsão:** Implementamos o `PredictionAgent` usando o `Prophet` do Facebook. Prophet é uma excelente escolha para tarefas de previsão empresarial como manutenção preditiva porque é resiliente a dados faltantes, lida automaticamente bem com tendências e sazonalidade, e é fácil de configurar. Embora o plano original também mencionasse redes LSTM, focar apenas no Prophet foi uma decisão estratégica sábia para garantir que um agente de previsão funcional e confiável fosse entregue dentro do prazo de 14 dias.

### 7.3. Justificativa para o Framework Agêntico Atual

**Por que Escolhemos uma Arquitetura Multi-Agente:**

1. **Modularidade:** Cada agente tem uma responsabilidade clara e bem definida, facilitando desenvolvimento, teste e manutenção.
2. **Escalabilidade:** Agentes individuais podem ser escalados independentemente com base na demanda.
3. **Resiliência:** Se um agente falhar, outros podem continuar operando, e o sistema pode se recuperar graciosamente.
4. **Extensibilidade:** Novos agentes podem ser facilmente adicionados ao sistema sem afetar os existentes.

**Vantagens da Nossa Implementação EventBus:**

- **Baixa Latência:** Comunicação em memória é mais rápida que soluções de rede.
- **Simplicidade:** Menos complexidade operacional comparado a sistemas de mensageria externos.
- **Desenvolvimento Rápido:** Permite prototipagem e iteração rápidas.
