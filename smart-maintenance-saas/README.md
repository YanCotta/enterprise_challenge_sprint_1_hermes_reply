# Smart Maintenance SaaS - Backend

## 📚 Documentation Navigation

This document is part of the Smart Maintenance SaaS documentation suite. For complete system understanding, please also refer to:

- **[Performance Baseline](./docs/PERFORMANCE_BASELINE.md)** - Load testing results and performance metrics baseline
- **[System and Architecture](./docs/SYSTEM_AND_ARCHITECTURE.md)** - Complete system architecture and component overview
- **[API Documentation](./docs/api.md)** - Complete REST API reference and usage examples  
- **[Load Testing Instructions](./docs/LOAD_TESTING_INSTRUCTIONS.md)** - Comprehensive guide for running performance tests
- **[Project Overview](../README.md)** - High-level project description and objectives

---

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests Passing](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](#running-tests)
[![Poetry](https://img.shields.io/badge/Poetry-Dependency%20Management-blue.svg)](https://python-poetry.org/)

A robust, event-driven, multi-agent backend for an industrial predictive maintenance SaaS platform. This system provides a solid foundation for ingesting sensor data, detecting anomalies, predicting failures, and orchestrating maintenance workflows.

**Current Status:** The system is fully functional, with a complete end-to-end workflow from data ingestion to maintenance scheduling and logging. All core agents are implemented and integrated through an event-driven architecture.

## 🚀 Recent Updates

### Enhanced Streamlit UI & Async Fix (June 2025)

**Key Improvements:**
- **🔧 Resolved Async/Await Issue**: Fixed critical thread-blocking problems in `/api/v1/reports/generate` endpoint using ThreadPoolExecutor
- **🎨 Enhanced UI Components**: Improved Streamlit interface with better formatting, success indicators, and metadata displays
- **📊 Advanced Report Generation**: Added support for multiple report types, output formats (JSON/text), date ranges, and chart generation
- **🖼️ Visual Charts**: Proper base64 image decoding and display for matplotlib-generated charts
- **🛡️ Better Error Handling**: Comprehensive error messages and graceful degradation

**Technical Details:**
- Reports endpoint now uses `asyncio.loop.run_in_executor()` with ThreadPoolExecutor for non-blocking operations
- Enhanced UI with date pickers, format selectors, and chart options
- All 249 unit tests pass with no regressions
- Fully functional integration between FastAPI backend and Streamlit frontend

## Tech Stack

- **Core:** Python 3.11+, FastAPI, Pydantic v2
- **Database:** PostgreSQL, TimescaleDB, Alembic for migrations
- **Communication:** Custom asynchronous EventBus
- **Machine Learning:** Scikit-learn (Isolation Forest), Prophet
- **Development:** Poetry, Docker, Pytest, Pre-commit hooks

## Project Structure

The project is organized into modular directories:

- `apps/`: Contains the application logic, including the multi-agent system (`agents`), API endpoints (`api`), and workflows.
- `core/`: Shared infrastructure, such as database connections, event bus, and configuration management.
- `data/`: Data-related components, including Pydantic schemas, data generators, and validators.
- `tests/`: A comprehensive test suite with unit, integration, and end-to-end tests.
- `scripts/`: Utility scripts for development and maintenance.

For a detailed architecture overview, please refer to the [System and Architecture Documentation](./docs/SYSTEM_AND_ARCHITECTURE.md).

## Key Features

- **Multi-Agent System:** A sophisticated system of specialized agents that handle different aspects of the maintenance workflow.
- **Event-Driven Architecture:** Decoupled components that communicate asynchronously through an event bus.
- **Predictive Maintenance:** Utilizes machine learning to predict equipment failures and recommend maintenance actions.
- **Automated Workflows:** End-to-end automation from anomaly detection to maintenance logging.
- **Comprehensive Testing:** A robust test suite ensures system reliability and stability.

## Implemented Agents

For detailed descriptions of each agent's role and responsibilities, please refer to the [System and Architecture Documentation](./docs/SYSTEM_AND_ARCHITECTURE.md#22-agent-descriptions).

## API Endpoints

The system exposes the following main API endpoints:

- `POST /api/v1/data/ingest`: Ingests sensor data into the system.
- `POST /api/v1/reports/generate`: Generates maintenance and system health reports.
- `POST /api/v1/decisions/submit`: Submits human feedback or decisions on system-prompted queries.

All endpoints are secured and require a valid `X-API-Key` in the header.

## Getting Started

### Prerequisites

- Python 3.11+
- Poetry
- Docker and Docker Compose

### Installation and Setup

1. **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd smart-maintenance-saas
    ```

2. **Install dependencies:**

    ```bash
    poetry install
    ```

3. **Set up the environment:**

    ```bash
    cp .env.example .env
    # Review and update .env if necessary
    ```

4. **Start the database:**

    ```bash
    docker-compose up -d
    ```

5. **Run database migrations:**

    ```bash
    poetry run alembic upgrade head
    ```

## Running the Application

- **Start the API server:**

    ```bash
    poetry run uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
    ```

- **Access the API documentation:**
  - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
  - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Control Panel UI (Streamlit)

The system includes a comprehensive web-based control panel built with Streamlit that provides an intuitive interface for interacting with the Smart Maintenance backend.

### Features

- **Manual Data Ingestion**: Submit sensor readings with real-time validation
- **Advanced Report Generation**: Create detailed reports with customizable options:
  - Multiple report types: performance_summary, anomaly_summary, maintenance_summary, system_health
  - Selectable output formats: JSON or text
  - Date range selection for historical analysis
  - Optional chart generation with base64-encoded visualizations
- **Human Decision Simulation**: Submit maintenance approval/rejection decisions
- **System Health Monitoring**: Real-time backend connectivity and status checks
- **Enhanced User Experience**: Improved formatting, metadata displays, and error handling

### Starting the Control Panel

1. **Ensure the backend is running** (see "Running the Application" above)

2. **Start the Streamlit app:**

    ```bash
    poetry run streamlit run ui/streamlit_app.py --server.port 8501
    ```

3. **Access the Control Panel:**
   - Open your browser to [http://localhost:8501](http://localhost:8501)
   - The UI will automatically check backend connectivity

### Using the Control Panel

**Data Ingestion:**
- Enter sensor details (ID, value, type, unit)
- Supported sensor types: temperature, vibration, pressure
- Submit button validates and sends data to backend

**Report Generation:**
- Select report type: performance_summary, anomaly_summary, maintenance_summary, system_health
- Choose output format: JSON (structured data) or text (human-readable)
- Set date range for historical analysis (default: last 30 days)
- Enable/disable chart generation for visual insights
- View formatted report content with metadata and charts (when available)

**Human Decisions:**
- Enter request ID for maintenance decisions
- Choose approve/reject with justification
- Simulates human operator decision workflow

**System Monitoring:**
- Sidebar shows real-time backend status
- Quick actions for testing and health checks
- Enhanced error handling with descriptive messages

### Technical Improvements

- **Async/Await Resolution**: Fixed thread-blocking issues in the reports endpoint using ThreadPoolExecutor for non-blocking operations
- **Enhanced UI Components**: Better formatting, success indicators, and collapsible metadata sections
- **Real Chart Support**: Proper base64 image decoding and display for matplotlib-generated charts
- **Improved Error Handling**: Comprehensive error messages and graceful degradation

## Running Tests

To run the full test suite, use the following command:

```bash
poetry run pytest
```

## 🇧🇷 Sumário em Português

Um backend robusto, orientado a eventos e multi-agente para uma plataforma de SaaS de manutenção preditiva industrial. Este sistema fornece uma base sólida para a ingestão de dados de sensores, detecção de anomalias, previsão de falhas e orquestração de fluxos de trabalho de manutenção.

**Status Atual:** O sistema está totalmente funcional, com um fluxo de trabalho completo desde a ingestão de dados até o agendamento e registro de manutenção. Todos os agentes principais estão implementados e integrados através de uma arquitetura orientada a eventos.
