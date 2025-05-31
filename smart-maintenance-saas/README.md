# Smart Maintenance SaaS - Backend

This document outlines the backend system for the Smart Maintenance SaaS project, developed as part of the FIAP SP x Hermes Reply challenge. The backend is a multi-agent system designed for predictive maintenance in industrial settings.

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

The Smart Maintenance SaaS backend is a multi-agent system that ingests sensor data, detects anomalies, predicts failures, schedules maintenance, and manages human-in-the-loop decision processes. It utilizes Python, FastAPI for APIs, and an event-driven architecture for communication between agents.

## 2. Tech Stack

* **Programming Language:** Python 3.11+
* **Framework:** FastAPI
* **Data Validation:** Pydantic (v2)
* **Database:** PostgreSQL with TimescaleDB extension, using `asyncpg` driver
* **ORM:** SQLAlchemy 2.0 (async) with Alembic for migrations
* **Inter-Agent Communication:** Custom EventBus (in-memory for development, Kafka/Redis for production)
* **Agent Core:** Custom `BaseAgent` class
* **Containerization:** Docker, Docker Compose
* **Testing:** Pytest, pytest-asyncio, `unittest.mock`, `testcontainers`, `httpx`, `factory-boy`
* **Dependency Management:** Poetry
* **Logging:** `python-json-logger`
* **Code Quality:** Black, Flake8, iSort, MyPy, pre-commit

## 3. Architecture

This section outlines the structure of the `smart-maintenance-saas` backend project.

### Project Structure

The Python project root is `smart-maintenance-saas/`. The codebase is organized into several key directories, promoting modularity and separation of concerns.

#### Key Directories

*   **`apps/`**: Contains the application-specific logic.
    *   API endpoints are defined in `apps/api/main.py`.
    *   Agent implementations reside in `apps/agents/`, including the `base_agent.py` and specific agents like `apps/agents/core/data_acquisition_agent.py`.
    *   Placeholders for future workflow implementations.
*   **`core/`**: Houses shared, core functionalities used across the application.
    *   `core/config/`: Pydantic settings for application configuration.
    *   `core/database/`: SQLAlchemy ORM models (`orm_models.py`), asynchronous database session management (`session.py`), CRUD operations (e.g., `crud_sensor_reading.py`), and the declarative base for models.
    *   `core/events/`: Pydantic models for defining event structures (`event_models.py`) and the central `EventBus` for inter-agent communication.
    *   `core/logging_config.py`: Configuration for structured JSON logging.
    *   `core/agent_registry.py`: Manages agent discovery and lifecycle.
*   **`data/`**: Includes all data-related definitions and utilities.
    *   `data/schemas.py`: Pydantic schemas, serving as the single source of truth for data structures.
    *   `data/sensor_data_generator.py`: Scripts for generating sample sensor data.
    *   `data/agent_data_enricher.py`: Utilities for enriching data within agents.
    *   `data/agent_data_validator.py`: Utilities for validating data within agents.
    *   `data/exceptions.py`: Custom data-related exceptions.
*   **`tests/`**: Contains all Pytest tests.
    *   Includes unit and integration tests.
    *   `conftest.py` provides shared fixtures and test setup.
*   **`alembic_migrations/`**: Stores Alembic database migration scripts.
    *   Includes the `env.py` configured for asynchronous migrations.
*   **`scripts/`**: Utility shell scripts for development and operational tasks (e.g., `run_tests.sh`).
*   **`infrastructure/`**: Contains infrastructure-as-code files.
    *   `docker/`: Dockerfiles and related scripts (e.g., `init-scripts/` for database initialization).
*   **`docs/`**: Project documentation in Markdown format (e.g., `architecture.md`).
*   **`examples/`**: Example scripts demonstrating usage of components or the system.

#### Root Files

The following important files are located at the `smart-maintenance-saas/` project root:

*   `README.md`: This file, providing an overview of the project.
*   `pyproject.toml`: Poetry project file, managing dependencies and build settings.
*   `poetry.lock`: Poetry lock file, ensuring deterministic builds.
*   `docker-compose.yml`: Docker Compose file for orchestrating development and production services.
*   `alembic.ini`: Alembic configuration file.
*   `pytest.ini`: Pytest configuration file.
*   `.pre-commit-config.yaml`: Configuration for pre-commit hooks.
*   `.env.example`: Example environment variables file.
*   `.gitignore`: Specifies intentionally untracked files that Git should ignore.

## 4. Setup and Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YanCotta/enterprise_challenge_sprint_1_hermes_reply # Replace with the actual URL if different
   cd smart-maintenance-saas
   ```

2. **Install Dependencies:**
   ```bash
   poetry install
   ```

3. **Environment Variables (Optional but Recommended):**
   - Copy `.env.example` to `.env`.
   - Update variables in `.env` if necessary (e.g., for non-default database credentials or custom configurations).

4. **Start Database Service:**
   ```bash
   docker-compose up -d db
   ```

5. **Run Database Migrations:**
   ```bash
   poetry run alembic upgrade head
   ```

## 5. Running the Application

```bash
poetry run uvicorn apps.api.main:app --reload
```

The API will be available at http://localhost:8000.  
API documentation (Swagger UI): http://localhost:8000/docs

## 6. Running Tests

To run the automated tests, use the following command:

```bash
poetry run pytest
```

## 7. API Endpoints

The following API endpoints are currently implemented:

*   `GET /health`: Returns the health status of the application.
*   `GET /health/db`: Returns the health status of the database connection.

## 8. Implemented Agents

The system currently includes the following core agents:

*   **`BaseAgent`** (`apps/agents/base_agent.py`): An abstract base class defining the common interface and core functionalities for all agents in the system. This includes aspects like event handling, lifecycle management, and capability registration.
*   **`DataAcquisitionAgent`** (`apps/agents/core/data_acquisition_agent.py`): Responsible for ingesting raw sensor data from external sources. It performs initial validation and enrichment on the incoming data. Upon processing, it publishes a `DataProcessedEvent` if successful, or a `DataProcessingFailedEvent` if issues are encountered. This agent subscribes to `SensorDataReceivedEvent` to trigger its workflow.

## 9. Event Catalog

The system uses an event-driven architecture. Key events include:

*   **`BaseEventModel`**: The base model for all events, providing common fields like `event_id`, `timestamp`, `version`, and `source_service`.
*   **`SensorDataReceivedEvent`**: Published when new sensor data is initially received by the system, typically before extensive processing.
*   **`DataProcessedEvent`**: Published by an agent (e.g., DataAcquisitionAgent) after successfully validating, cleaning, and enriching sensor data.
*   **`DataProcessingFailedEvent`**: Published if an error occurs during data processing, validation, or enrichment.
*   **`AnomalyDetectedEvent`**: Published when an anomaly detection agent identifies a potential anomaly in the data. (Note: Anomaly detection agent is planned but not yet fully implemented).
*   **`AgentStatusUpdateEvent`**: Published by agents to report their current operational status, health, or significant state changes.

All event models are defined in `core/events/event_models.py`.

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


