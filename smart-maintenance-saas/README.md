# Smart Maintenance SaaS - Backend

This document outlines the backend system for the Smart Maintenance SaaS project, developed as part of the FIAP SP x Hermes Reply challenge. The backend is a multi-agent system designed for predictive maintenance in industrial settings.

**Version:** 0.1.0 (Backend Sprint - In Progress)  
**Last Updated:** May 28, 2025

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Architecture](#3-architecture)
4. [Setup and Installation](#4-setup-and-installation)
5. [Running the Application](#5-running-the-application)
6. [Running Tests](#6-running-tests)
7. [API Endpoints](#7-api-endpoints)
8. [Implemented Agents](#8-implemented-agents)
9. [Event Catalog](#9-event-catalog)
10. [Daily Progress Log](#10-daily-progress-log)
11. [Key Configuration](#11-key-configuration)
12. [Troubleshooting](#12-troubleshooting)

## 1. Project Overview

The Smart Maintenance SaaS backend leverages a multi-agent architecture to ingest sensor data, detect anomalies, predict failures, schedule maintenance, and manage human-in-the-loop decision processes. It's built using Python with FastAPI for APIs and an event-driven approach for inter-agent communication.

## 2. Tech Stack

* **Programming Language:** Python 3.11+
* **Framework:** FastAPI
* **Data Validation:** Pydantic
* **Database:** PostgreSQL with TimescaleDB extension (for time-series data)
* **ORM:** SQLAlchemy with Alembic for migrations
* **Inter-Agent Communication:** Custom EventBus (initially in-memory, planned for Kafka/Redis)
* **Agent Core:** Custom `BaseAgent` class
* **Machine Learning (Planned/In-Progress):**
  * Anomaly Detection: Scikit-learn (Isolation Forest, statistical models)
  * Prediction: Prophet
  * RAG/Knowledge: ChromaDB, SentenceTransformers
* **Scheduling:** Google OR-Tools (CP-SAT Solver)
* **Containerization:** Docker, Docker Compose
* **Orchestration (Planned):** Kubernetes
* **Testing:** Pytest, pytest-asyncio, `unittest.mock`
* **Dependency Management:** Poetry
* **Logging:** `python-json-logger`
* **CI/CD (Planned):** GitHub Actions
* **Code Quality:** Black, Flake8, iSort, MyPy, pre-commit

## 3. Architecture

The system is composed of several specialized agents communicating via an event bus. Key components include:

* **API Layer:** FastAPI endpoints for external interaction
* **Event Streaming Layer:** Manages the flow of events
* **Multi-Agent Orchestration Layer:** Coordinates agent activities
* **Data & ML Layer:** Handles data storage, processing, and machine learning

## 4. Setup and Installation

1. **Prerequisites:**
   * Python 3.11+
   * Poetry (Python dependency manager)
   * Docker and Docker Compose
   * Git

2. **Clone the repository:**
   ```bash
   git clone https://github.com/YanCotta/enterprise_challenge_sprint_1_hermes_reply
   cd smart-maintenance-saas
   ```

3. **Set up Python Environment & Install Dependencies:**
   ```bash
   poetry install
   ```

4. **Environment Variables:**
   * Copy `.env.example` to `.env`
   * Update variables in `.env` as needed (e.g., database credentials if not using defaults for Docker)

5. **Start Docker Services (Database, etc.):**
   ```bash
   docker-compose up -d db # Add other services like redis, kafka if defined
   ```

6. **Run Database Migrations:**
   ```bash
   poetry run alembic upgrade head
   ```

## 5. Running the Application

```bash
poetry run uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at http://localhost:8000.  
API documentation (Swagger UI): http://localhost:8000/docs  
Alternative API documentation (ReDoc): http://localhost:8000/redoc

## 6. Running Tests

Ensure test dependencies and any test-specific setup (like a test database container if using testcontainers) are configured.

```bash
poetry run pytest
```

To run with coverage:

```bash
poetry run pytest --cov=apps --cov=core
```

## 7. API Endpoints

(This section will be populated as API endpoints are defined, starting around Day 11)

* `POST /api/v1/ingestion/sensor-reading/`: Ingests new sensor data.
...

## 8. Implemented Agents

(This section will list agents as they are implemented, starting Day 2/4)

* **BaseAgent:** Foundation class for all agents. Defines common lifecycle, event handling, and health check methods. (Day 2)
* **AgentRegistry:** Singleton class for discovering and managing agent instances. (Day 2)
* **DataAcquisitionAgent:** Handles raw data ingestion, validation, and enrichment. (Day 4)
...

## 9. Event Catalog

(This section will list Pydantic event models defined in core/events/event_models.py as they are created)

* **BaseEventModel:** Base model for all events, providing common fields like event_id and timestamp.
* **SensorDataReceivedEvent:** Published when new sensor data is ingested into the system.
* **DataProcessedEvent:** Published after data is validated, cleaned, and enriched.
* **AnomalyDetectedEvent:** Published when an anomaly detection agent identifies a potential anomaly.
* **AgentStatusUpdateEvent:** Published by agents to report their current status or health.
...

## 10. Daily Progress Log

(This is where you'll add brief notes each day)

* **Day 1 (2025-05-28):**
  * **Environment & Architecture Setup:** Project structure, Poetry, Git, pre-commit hooks.
  * **Core Infrastructure:** Dockerized TimescaleDB, basic async EventBus, Pydantic settings, structured JSON logging.
  * **Testing Foundation:** Pytest setup, test database strategy using `testcontainers`.
* **Day 2 (2025-05-29):**
  * Implemented `AgentCapability` dataclass and `BaseAgent` abstract class (`apps/agents/base_agent.py`) with core lifecycle, event handling, and capability registration methods.
  * Implemented singleton `AgentRegistry` (`core/agent_registry.py`) for agent discovery.
  * Refined `EventBus` (`core/events/event_bus.py`) with enhanced error handling, unsubscribe method, and switched to structured logging.
  * Defined core Pydantic event models (`BaseEventModel`, `SensorDataReceivedEvent`, `DataProcessedEvent`, `AnomalyDetectedEvent`, `AgentStatusUpdateEvent`) in `core/events/event_models.py`.
  * Added unit tests for `EventBus` and `BaseAgent`.
  * Addressed review feedback: refined logging in AgentRegistry and EventBus.
* **Day 3 (2025-05-30):**
  * Finalized Pydantic schemas (`SensorType`, `SensorReading`, `SensorReadingCreate`, `AnomalyAlert`, `MaintenanceTask`) in `data/schemas.py`.
  * Updated `sensor_data_generator.py` to use centralized schemas.
  * Implemented SQLAlchemy ORM models (`SensorReadingORM` with TimescaleDB hypertable setup, `AnomalyAlertORM`, `MaintenanceTaskORM`) in `core/database/orm_models.py`.
  * Configured async database session management in `core/database/session.py`.
  * Completed Alembic setup (`alembic.ini`, `env.py` for async) and successfully generated and applied the initial migration to create tables and TimescaleDB hypertable.
  * Implemented `CRUDSensorReading` class in `core/database/crud/crud_sensor_reading.py`.
  * Set up main FastAPI application (`apps/api/main.py`) with logging integration and `/health`, `/health/db` endpoints.
  * Addressed review feedback: updated Pydantic DSN usage in `settings.py`, removed unused `caller_info` in `logging_config.py`, removed print from `schemas.py`, refined DB URL transformation in `session.py` and `env.py`.

## 11. Key Configuration


