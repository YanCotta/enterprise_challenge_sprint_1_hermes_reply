# Smart Maintenance SaaS - Backend

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-41%2F41%20Passing-brightgreen.svg)](#running-tests)
[![Poetry](https://img.shields.io/badge/Poetry-Dependency%20Management-blue.svg)](https://python-poetry.org/)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black.svg)](https://github.com/psf/black)

## Overview

A robust, **event-driven, multi-agent backend** for an industrial predictive maintenance SaaS platform. This system provides a solid foundation for ingesting sensor data, detecting anomalies, predicting failures, and orchestrating maintenance workflows through a sophisticated agent-based architecture.

**Current Status:** End of Day 4 of a 14-day development sprint. Foundational elements and initial `DataAcquisitionAgent` fully implemented and tested. All **41/41 tests passing**, demonstrating system stability and reliability.

## Tech Stack

### Core Technologies
- **Python 3.11+** - Modern Python with full async/await support
- **FastAPI** - High-performance async web framework with automatic OpenAPI docs
- **Pydantic v2** - Advanced data validation and settings management with improved performance
- **SQLAlchemy 2.0** - Modern async ORM with full type safety
- **asyncpg** - Fast PostgreSQL async driver
- **PostgreSQL + TimescaleDB** - Optimized time-series database for sensor data
- **Alembic** - Database migrations with async support

### Architecture & Communication
- **Custom EventBus** (`core/events/event_bus.py`) - Asynchronous inter-agent communication
- **Custom BaseAgent Framework** (`apps/agents/base_agent.py`) - Agent lifecycle and capability management
- **Event-Driven Architecture** - Decoupled system components with strong typing

### Development & Quality
- **Poetry** - Modern dependency management and packaging
- **Docker & Docker Compose** - Containerized development environment
- **Pytest + pytest-asyncio** - Comprehensive async testing framework
- **Pre-commit Hooks** - Black, Flake8, iSort, MyPy for code quality
- **Structured JSON Logging** - Enhanced observability with `python-json-logger`

## Project Structure

The Python project root is `smart-maintenance-saas/`, containing **37 core Python modules** organized for maximum modularity and maintainability:

### 📁 Core Directories

#### `apps/` - Application Logic
- **`api/main.py`** - FastAPI application with health endpoints
- **`agents/base_agent.py`** - Abstract BaseAgent class with lifecycle management
- **`agents/core/data_acquisition_agent.py`** - Production-ready DataAcquisitionAgent
- **`agents/decision/`** - Decision-making agent implementations (placeholder)
- **`agents/interface/`** - User interface agent implementations (placeholder)
- **`agents/learning/`** - Machine learning agent implementations (placeholder)
- **`workflows/`** - Workflow orchestration logic (placeholder files)

#### `core/` - Shared Infrastructure
- **`config/settings.py`** - Pydantic-based configuration management
- **`database/`**
  - `orm_models.py` - SQLAlchemy models (SensorReadingORM, AnomalyAlertORM, MaintenanceTaskORM)
  - `session.py` - Async database session management
  - `crud/crud_sensor_reading.py` - Type-safe CRUD operations
  - `base.py` - SQLAlchemy declarative base
- **`events/`**
  - `event_models.py` - Strongly-typed Pydantic event models
  - `event_bus.py` - Asynchronous event publishing and subscription
- **`logging_config.py`** - Structured JSON logging setup
- **`agent_registry.py`** - Singleton agent discovery and management

#### `data/` - Data Layer
- **`schemas.py`** - **Single source of truth** for Pydantic data models
- **`generators/sensor_data_generator.py`** - Sample data generation utilities
- **`processors/agent_data_enricher.py`** - Data enrichment logic
- **`validators/agent_data_validator.py`** - Data validation logic
- **`exceptions.py`** - Custom data-related exceptions

#### `tests/` - Comprehensive Testing
- **`unit/`** - Component-level tests
- **`integration/`** - End-to-end workflow tests
- **`conftest.py`** - Shared fixtures and test database setup

#### `alembic_migrations/` - Database Schema Management

- **`env.py`** - Async-configured Alembic environment
- **`versions/`** - Version-controlled migration scripts

#### `scripts/` - Utility Scripts

- **`migrate_db.py`** - Database migration utilities
- **`seed_data.py`** - Development data seeding
- **`setup_dev.py`** - Development environment setup

#### `infrastructure/` - Infrastructure as Code

- **`docker/init-scripts/01-init-timescaledb.sh`** - TimescaleDB initialization script
- **`k8s/`** - Kubernetes deployment manifests (placeholder)
- **`terraform/`** - Infrastructure provisioning (placeholder)

#### `docs/` - Project Documentation

- **`api.md`** - API documentation
- **`architecture.md`** - System architecture details
- **`deployment.md`** - Deployment guide

#### `examples/` - Usage Examples

- **`fastapi_logging_example.py`** - FastAPI logging integration
- **`logging_example.py`** - Basic logging usage
- **`using_settings.py`** - Configuration management example

### 📄 Key Configuration Files

- `pyproject.toml` - Poetry dependencies and project metadata
- `docker-compose.yml` - Development database orchestration
- `alembic.ini` - Database migration configuration
- `pytest.ini` - Test execution configuration
- `.pre-commit-config.yaml` - Code quality automation

## Key Features Implemented

### 🤖 Core Agent Framework
- **BaseAgent** - Abstract foundation providing lifecycle management, event handling, and capability registration
- **AgentRegistry** - Singleton pattern for agent discovery and centralized management
- **Type-safe agent communication** with full async support

### ⚡ Event-Driven Architecture
- **Custom EventBus** - High-performance asynchronous communication
- **Strongly-typed events** - Pydantic models ensure data integrity
- **Correlation tracking** - Full request tracing through event correlation IDs

### 🗄️ Asynchronous Data Layer
- **SQLAlchemy 2.0** - Modern async ORM with full type safety
- **TimescaleDB hypertables** - Optimized time-series storage for sensor data
- **Alembic migrations** - Version-controlled schema management
- **Async CRUD operations** - Non-blocking database interactions

### 📊 Data Acquisition Pipeline
- **DataAcquisitionAgent** - Production-ready sensor data ingestion
  - Subscribes to `SensorDataReceivedEvent`
  - Validates data using `DataValidator` and `SensorReadingCreate` schema
  - Enriches data using `DataEnricher`
  - Publishes `DataProcessedEvent` on success or `DataProcessingFailedEvent` on failure
- **Comprehensive error handling** with detailed failure reporting

### 🔧 API Foundation
- **FastAPI application** with automatic OpenAPI documentation
- **Health check endpoints** - Application and database connectivity monitoring
- **Async-native design** for maximum performance

### 📝 Configuration & Observability
- **Centralized settings** - Pydantic BaseSettings with environment variable support
- **Structured JSON logging** - Enhanced debugging and monitoring capabilities
- **Comprehensive testing** - **41/41 tests passing** ensuring system stability

## Setup and Installation

### Prerequisites
- **Python 3.11+**
- **Poetry** (for dependency management)
- **Docker & Docker Compose** (for database)
- **Git**

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone <your-repo-url>
   cd smart-maintenance-saas
   ```

2. **Install Dependencies**
   ```bash
   poetry install
   ```

3. **Configure Environment**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Review and update variables in .env if necessary
   # (defaults work with Docker setup)
   ```

4. **Start Database Service**
   ```bash
   # Starts PostgreSQL with TimescaleDB extension
   docker-compose up -d db
   ```

5. **Apply Database Migrations**
   ```bash
   # Sets up schema and TimescaleDB hypertables
   poetry run alembic upgrade head
   ```

## Running the Application

### Start the API Server
```bash
poetry run uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Access Points
- **API Base URL:** http://localhost:8000
- **Interactive Documentation (Swagger UI):** http://localhost:8000/docs
- **Alternative Documentation (ReDoc):** http://localhost:8000/redoc

## Running Tests

### Execute Test Suite
```bash
poetry run pytest
```

**Current Status:** ✅ **41/41 tests passing** - indicating stable implementation of all current features

### Optional: Run with Coverage
```bash
poetry run pytest --cov=apps --cov=core --cov=data
```

## Current API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | General application health status |
| `GET` | `/health/db` | Database connectivity status |

## Implemented Agents & Their Roles

### BaseAgent (`apps/agents/base_agent.py`)
**The foundational abstract class** for all specialized agents in the system.

**Core Capabilities:**
- 🆔 **Unique identification** with auto-generated agent IDs
- 🔄 **Lifecycle management** - start, stop, health monitoring
- 📡 **Event bus integration** - seamless pub/sub communication
- 🎯 **Capability registration** - dynamic feature discovery
- ⚡ **Async event handling** with default implementations
- 🏥 **Health status reporting** for system monitoring

### DataAcquisitionAgent (`apps/agents/core/data_acquisition_agent.py`)
**Production-ready agent** responsible for the critical first stage of the data pipeline.

**Role & Responsibilities:**
- 📥 **Data Ingestion** - Receives raw sensor data from external sources
- ✅ **Data Validation** - Ensures structural integrity and business rules using `DataValidator`
- 🔧 **Data Enrichment** - Adds contextual information using `DataEnricher`
- 📤 **Event Publishing** - Notifies downstream systems of processing results

**Event Flow:**
- **Subscribes to:** `SensorDataReceivedEvent`
- **Publishes on Success:** `DataProcessedEvent` (with validated & enriched data)
- **Publishes on Failure:** `DataProcessingFailedEvent` (with detailed error information)

## Event Catalog

### Core Event Models (`core/events/event_models.py`)

| Event | Purpose | Key Attributes |
|-------|---------|----------------|
| `BaseEventModel` | Parent model for all events | `timestamp`, `event_id`, `correlation_id` |
| `SensorDataReceivedEvent` | Raw sensor data arrival signal | `raw_data` payload |
| `DataProcessedEvent` | Successful data processing notification | `processed_data` |
| `DataProcessingFailedEvent` | Processing failure with error details | `agent_id`, `error_message`, `original_event_payload` |
| `AnomalyDetectedEvent` | Anomaly detection results *(future use)* | TBD |
| `AgentStatusUpdateEvent` | Agent operational status reports *(future use)* | TBD |

**Event Architecture Benefits:**
- 🔄 **Loose coupling** between system components
- 📊 **Full traceability** through correlation IDs
- 🛡️ **Type safety** with Pydantic validation
- ⚡ **Asynchronous processing** for high performance

## Database Schema Overview

### Technology Stack
- **PostgreSQL** with **TimescaleDB extension** for optimized time-series operations
- **SQLAlchemy 2.0** async ORM with full type safety
- **Alembic** for version-controlled schema migrations

### Core ORM Models (`core/database/orm_models.py`)

| Model | Purpose | Special Features |
|-------|---------|------------------|
| `SensorReadingORM` | Individual sensor measurements | TimescaleDB hypertable partitioned by timestamp |
| `AnomalyAlertORM` | Detected anomaly records *(future use)* | Standard PostgreSQL table |
| `MaintenanceTaskORM` | Maintenance workflow tracking *(future use)* | Standard PostgreSQL table |

**Database Features:**
- 🕒 **TimescaleDB hypertables** for efficient time-series queries
- 🔄 **Async operations** for non-blocking database access
- 📊 **Automatic partitioning** for optimal performance at scale
- 🔄 **Version-controlled migrations** with Alembic

## Code Quality and Best Practices

### Development Standards
- ✨ **Clean, maintainable code** with comprehensive type hints
- 🔍 **Pre-commit hooks** ensure consistent code quality:
  - **Black** - Automated code formatting
  - **Flake8** - Style and complexity linting
  - **iSort** - Import statement organization
  - **MyPy** - Static type checking
- 📝 **Structured JSON logging** for effective monitoring and debugging
- 🧪 **Comprehensive testing** with **41/41 tests passing**

### Architecture Principles
- 🏗️ **Single Responsibility** - Each component has a clear, focused purpose
- 🔌 **Dependency Injection** - Testable, loosely-coupled components
- 📋 **Interface Segregation** - Clean abstractions through protocols
- 🔄 **Event-Driven Design** - Scalable, reactive system architecture

## Exploring the Code

### Key Areas for Understanding the Architecture

| Component | File | What to Look For |
|-----------|------|------------------|
| **Agent Framework** | `apps/agents/base_agent.py` | Abstract agent lifecycle and event handling |
| **Data Processing** | `apps/agents/core/data_acquisition_agent.py` | Production data pipeline implementation |
| **Event System** | `core/events/event_bus.py` | Async pub/sub communication |
| **Event Models** | `core/events/event_models.py` | Strongly-typed event definitions |
| **Data Models** | `data/schemas.py` | Centralized Pydantic schemas |
| **Database Layer** | `core/database/orm_models.py` | SQLAlchemy models and TimescaleDB setup |
| **Integration Testing** | `tests/integration/agents/core/test_data_acquisition_agent.py` | End-to-end workflow verification |

### Recommended Exploration Path
1. Start with `BaseAgent` to understand the agent framework
2. Examine `DataAcquisitionAgent` for a complete implementation example
3. Review `EventBus` and event models for communication patterns
4. Explore test files to understand expected behaviors and edge cases

## Next Steps / Future Development

**Current Progress:** Day 4 of 14-day development sprint

### Planned Implementations (Days 5-14)
- 🤖 **Specialized Agents**
  - Anomaly Detection Agent (ML-based pattern recognition)
  - Predictive Maintenance Agent (failure prediction models)
  - Maintenance Scheduling Agent (workflow orchestration)
- 🌐 **Extended API Layer**
  - Sensor data ingestion endpoints
  - Real-time monitoring dashboards
  - Maintenance task management
- 🔄 **Production Infrastructure**
  - Kafka/Redis integration for persistent messaging
  - Container orchestration (Kubernetes)
  - Monitoring and alerting systems

### Foundation Achieved
✅ **Solid architectural foundation** with proven stability  
✅ **Event-driven communication** ready for complex workflows  
✅ **Type-safe data processing** ensuring reliability  
✅ **Comprehensive testing** providing confidence for future development  

---

*This project demonstrates enterprise-grade Python development practices, modern async architecture, and production-ready code quality standards.*


