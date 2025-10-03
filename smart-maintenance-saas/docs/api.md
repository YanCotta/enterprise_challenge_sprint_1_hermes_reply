# Smart Maintenance SaaS - API Documentation

**Last Updated:** 2025-10-03  
**Status:** V1.0 Production Ready  
**Related Documentation:**
- [v1_release_must_do.md](./v1_release_must_do.md) - V1.0 Deployment Playbook (canonical reference)
- [COMPREHENSIVE_DOCUMENTATION.md](./COMPREHENSIVE_DOCUMENTATION.md) - Complete documentation index
- [EXECUTIVE_SUMMARY.md](./EXECUTIVE_SUMMARY.md) - System status and release readiness
- [SYSTEM_AND_ARCHITECTURE.md](./SYSTEM_AND_ARCHITECTURE.md) - Architecture overview with diagrams

**Architecture Diagrams:**
- [API Endpoints Architecture](./SYSTEM_AND_ARCHITECTURE.md#214-api-endpoints-architecture) - Complete API structure diagram
- [Event-Driven Architecture](./SYSTEM_AND_ARCHITECTURE.md#22-production-event-driven-architecture-flow) - Request flow and event processing
- [Data Ingestion Pipeline](./SYSTEM_AND_ARCHITECTURE.md#29-data-ingestion-and-processing-pipeline) - Data flow through the API

---

## Overview

The Smart Maintenance SaaS API provides a comprehensive RESTful interface for industrial predictive maintenance operations with S3 serverless model loading and cloud-native architecture. The API is built with FastAPI and follows OpenAPI 3.0 standards, offering automatic documentation, validation, and enterprise-grade observability.

**V1.0 Production Status:** All core endpoints operational with cloud deployment verified. Backend capabilities at 100% readiness (see [v1_release_must_do.md Section 2.1](./v1_release_must_do.md)).

**Base URL**: `http://localhost:8000` (Docker deployment)  
**API Version**: v1  
**Production Status**: ✅ **V1.0 Production Ready** (All phases complete)  
**Cloud Services**: TimescaleDB, Redis, S3 (production configuration validated)

**Documentation**:
- Interactive API Docs: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`
- Prometheus Metrics: `http://localhost:8000/metrics`
- Health Check: `http://localhost:8000/health`

Root endpoint: `GET /` returns a welcome message with name and version.

## Quick Start with Docker (Cloud-Native)

⚠️ **IMPORTANT**: Sprint 4 requires cloud services. Populate `.env` with your cloud credentials.

```bash
# Set up cloud-native environment
cd smart-maintenance-saas
cp .env_example.txt .env
# MANUAL: Fill in cloud credentials (DATABASE_URL, REDIS_URL, S3, etc.)

# Start the cloud-connected system  
docker compose up -d

# Access points (cloud-integrated)
# API: http://localhost:8000 (connected to cloud TimescaleDB)
# UI: http://localhost:8501 (cloud data visualization)
# MLflow: http://localhost:5000 (cloud backend + S3 artifacts)
# Docs: http://localhost:8000/docs
# Metrics: http://localhost:8000/metrics
```

> **New in 2025-10-03:** Docker images now build a dedicated virtual environment at `/opt/venv` and install dependencies via `requirements/api.txt`. Poetry is no longer required inside containers, eliminating the previous lock-file parsing failures during `docker compose build`.

## Dependency Management & Local Setup

The API/UI stack shares the same dependency manifest used for container images.

- **Create a local virtual environment (optional but recommended):**

  ```bash
  cd smart-maintenance-saas
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements/api.txt
  ```

- **Regenerate `requirements/api.txt` when dependencies change:**

  - Update `pyproject.toml` (main dependencies section)
  - Manually align the pinned ranges in `requirements/api.txt` (or use an export tool in a clean environment)
  - Commit both files together so Docker builds remain deterministic

- **Docker builds use pip automatically:**

  - `docker compose build api` copies `requirements/api.txt` into the image, creates `/opt/venv`, and runs `pip install --no-cache-dir -r /tmp/requirements.txt`
  - The API service entrypoint now calls `/opt/venv/bin/uvicorn`, so no additional setup is required once the container is running

## Control Panel UI

For easy interaction with the API, a Streamlit-based control panel is available at `http://localhost:8501`. The control panel provides:

- **Visual forms** for all API endpoints
- **Real-time validation** and error handling  
- **System health monitoring** and connectivity checks
- **Quick testing tools** for rapid API exploration
- **Dataset preview** with 9,000+ sensor readings visualization

When using Docker: The UI is automatically available at `http://localhost:8501` when you run `docker compose up -d`.

See the [Backend README](../README.md#control-panel-ui-streamlit) for detailed usage instructions.

## Enterprise Features

### Observability & Monitoring

The API includes production-grade observability features implemented during the development sprint:

#### Prometheus Metrics (`/metrics`)

- **Endpoint**: `GET /metrics`
- **Format**: Standard Prometheus exposition format
- **Metrics Available**:
  - Python GC metrics (objects collected, collections count)
  - Process-level metrics (CPU, memory, threads)
  - HTTP request metrics (latency, status codes, request count)
  - FastAPI-specific application metrics

#### Correlation IDs & Request Tracing

- **Automatic Request ID Generation**: UUIDv4 generated for each request
- **Custom Request ID Support**: Include `X-Request-ID` header to use custom correlation ID
- **Response Headers**: All responses include `X-Request-ID` for end-to-end tracing
- **Structured Logging**: JSON-formatted logs with correlation ID propagation

#### Event Bus Reliability

- **Retry Logic**: Exponential backoff with 3 attempts (2s, 4s, 6s delays)
- **Dead Letter Queue**: Failed events automatically sent to DLQ after retries
- **Circuit Breaker Pattern**: Graceful degradation for downstream service failures

### Security Features

- **API Key Authentication**: Scope-based permission system
- **Input Validation**: Pydantic-based request validation
- **STRIDE Threat Model**: Comprehensive security analysis in `docs/SECURITY.md`
- **Rate Limiting**: Per-endpoint limits to prevent abuse

## Authentication

All API endpoints require authentication via API key. Include the API key in the request header:

```http
X-API-Key: your-api-key-here
```

### API Key Scopes

The API uses a scope-based permission system:

- `data:ingest` - Ingest sensor data
- `reports:generate` - Generate reports
- `tasks:update` - Submit human decisions
- `ml:predict` - Run ML predictions
- `ml:anomaly` - Run anomaly detection
- `ml:drift` - Run drift checks

### Request Headers

#### Required Headers

- `X-API-Key`: Your API authentication key
- `Content-Type`: `application/json` (for POST requests)

#### Optional Headers

- `X-Request-ID`: Custom correlation ID for request tracing (auto-generated if not provided)
- `Idempotency-Key`: Prevents duplicate processing for data ingestion (Redis-backed, 10-minute TTL)

## Core Endpoints

### Data Ingestion

#### POST /api/v1/data/ingest

Ingests sensor data into the Smart Maintenance system. Idempotency is enforced via Redis to prevent duplicate event processing across replicas.

**Headers:**
```http
X-API-Key: your-api-key-here
X-Request-ID: optional-correlation-id
Idempotency-Key: optional-unique-key-for-deduplication
Content-Type: application/json
```

**Request Body:**
```json
{
  "sensor_id": "TEMP_001",
  "value": 25.5,
  "sensor_type": "temperature",
  "unit": "celsius",
  "location": "Factory Floor A",
  "timestamp": "2025-06-11T10:30:00Z"
}
```

**Response (200 OK):**
```json
{
  "status": "event_published",
  "event_id": "1f8b1d7c-0a6d-4b1b-8d2f-9a9b7e0c1234",
  "correlation_id": "e0c4d7a0-1234-4b2a-9a8b-001122334455",
  "sensor_id": "TEMP_001"
}
```

**Response (200 OK - Duplicate):**
```json
{
  "status": "duplicate_ignored",
  "event_id": "1f8b1d7c-0a6d-4b1b-8d2f-9a9b7e0c1234",
  "correlation_id": "e0c4d7a0-1234-4b2a-9a8b-001122334455",
  "sensor_id": "TEMP_001"
}
```

**Sensor Types Supported:**

- `temperature`
- `vibration`
- `pressure`
- `humidity`
- `current`
- `voltage`

**Idempotency Behavior:**
- Include `Idempotency-Key` header to prevent duplicate processing
- Duplicate requests with same key return the original `event_id`
- Redis-backed store with 10-minute TTL (safe across replicas)

### Reports Generation

#### POST /api/v1/reports/generate

Generates various maintenance and system reports based on the specified report type.

**Request Body:**
```json
{
  "report_type": "anomaly_summary",
  "format": "json",
  "time_range_start": "2025-05-11T00:00:00Z",
  "time_range_end": "2025-06-11T00:00:00Z",
  "include_charts": true,
  "parameters": {}
}
```

**Response (200 OK):**
```json
{
  "report_id": "rpt_987654321",
  "report_type": "anomaly_summary",
  "format": "json",
  "content": "...",
  "generated_at": "2025-06-11T10:30:00Z",
  "charts_encoded": {},
  "metadata": {"date_range": "2025-05-11 to 2025-06-11"}
}
```

**Report Types Available:**
- `anomaly_summary` - Summary of detected anomalies
- `system_health` - Overall system health report
- `maintenance_summary` - Maintenance activities summary
- `performance_summary` - System performance metrics

### Human Decision Submission

#### POST /api/v1/decisions/submit

Submits human feedback or decisions on system-prompted queries for maintenance approval/rejection.

Status code: 201 Created

**Request Body:**
```json
{
  "request_id": "req_maintenance_123",
  "decision": "approve",
  "justification": "Critical equipment requires immediate attention",
  "operator_id": "operator_001"
}
```

**Response (201 Created):**
```json
{
  "status": "success",
  "event_id": "3d3c2a1b-9e8f-4a7b-b6a1-0c9d12345678",
  "request_id": "req_maintenance_123"
}
```

**Decision Options:**
- `approve` - Approve the maintenance request
- `reject` - Reject the maintenance request
- `defer` - Defer the decision for later review

## Health Check Endpoints

### GET /health

Basic health check endpoint to verify API availability.

**Response (200 OK):**
```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok",
  "timestamp": "2025-06-11T10:30:00Z"
}
```

### GET /health/db
Checks database connectivity.

**Response (200 OK):**
```json
{ "db_status": "connected" }
```

### GET /health/redis
Checks Redis connectivity and basic stats.

**Response (200 OK):**
```json
{ "status": "healthy", "info": { "mode": "standalone" } }
```

### GET /metrics

Prometheus metrics endpoint for monitoring and observability.

**Response (200 OK):**
```
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 5852.0
python_gc_objects_collected_total{generation="1"} 3109.0
python_gc_objects_collected_total{generation="2"} 2357.0

# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",handler="/health"} 42.0

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
...
```

**Metrics Categories:**
- **Python Runtime**: GC metrics, memory usage, process information
- **HTTP Traffic**: Request counts, response times, status codes
- **FastAPI Specific**: Route-level performance metrics
- **Application**: Custom business metrics

## ML Services Integration

The API integrates with MLflow for model management and provides endpoints for accessing trained models. For convenience, key ML endpoints are also exposed via the API:

### Machine Learning API

- POST `/api/v1/ml/predict` (scope: `ml:predict`)
  - Body: `{ "model_name": "ai4i_classifier_randomforest_baseline", "model_version": "auto", "features": { ... } }`
  - Response: `{ prediction, confidence?, model_info, shap_values?, feature_importance?, timestamp }`

- POST `/api/v1/ml/detect_anomaly` (scope: `ml:anomaly`)
  - Body: `{ "sensor_readings": [ { sensor_id, sensor_type, value, unit, timestamp, quality } ], "model_name": "anomaly_detector_refined_v2", "model_version": "auto", "sensitivity": 0.7 }`
  - Response: `{ anomalies_detected: [...], anomaly_count, total_readings_analyzed, model_info, analysis_timestamp }`

- POST `/api/v1/ml/check_drift` (scope: `ml:drift`, rate limited: 10/min per API key)
  - Body: `{ "sensor_id": "sensor_001", "window_minutes": 60, "p_value_threshold": 0.05, "min_samples": 30 }`
  - Response: `{ drift_detected, p_value, ks_statistic, recent_count, baseline_count, notes? }`

### MLflow Integration
- **MLflow UI**: Available at `http://localhost:5000`
- **Model Registry**: Stores anomaly detection and forecasting models
- **Experiment Tracking**: Complete training run history and metrics
- **Artifact Storage**: Model files, plots, and feature metadata

### Available Models

Based on the latest comprehensive model analysis and Sprint 10.5 improvements:

- **Anomaly Detection**: IsolationForest-based anomaly detector (`anomaly_detector_refined_v2`)
  - **Performance**: Production-ready with validated anomaly detection capabilities
  - **Features**: 12 lag features with MinMaxScaler normalization
  - **Status**: Registered and ready for deployment

- **Time Series Forecasting**: Prophet Tuned model (`prophet_forecaster_sensor-001`)
  - **Performance**: 20.86% improvement over naive baseline (MAE: 2.8258)
  - **Optimization**: Hyperparameter tuned (changepoint_prior_scale: 0.1, seasonality_prior_scale: 5.0)
  - **Features**: Built-in trend, seasonality, and changepoint detection
  - **Status**: Best performing model, recommended for production deployment

- **Challenger Models**: LightGBM evaluation completed
  - **Performance**: 3.0994 MAE (9.68% worse than Prophet Tuned)
  - **Features**: 12 lag features with scaling
  - **Status**: Evaluated but Prophet remains superior for time series forecasting

- **Feature Engineering Pipeline**: 
  - **SensorFeatureTransformer**: Professional sklearn-compatible transformer
  - **Lag Features**: Intelligent forward-fill/back-fill strategy (1-5 lag features)
  - **Scaling**: MinMaxScaler normalization to [0,1] range
  - **Quality**: Robust validation and error handling

### Model Access
Models are accessed through the MLflow API and can be queried programmatically:

```bash
# Get registered models
curl http://localhost:5000/api/2.0/mlflow/registered-models/list

# Get latest model version
curl -X POST http://localhost:5000/api/2.0/mlflow/registered-models/get-latest-versions \
  -H "Content-Type: application/json" \
  -d '{"name": "anomaly_detector_refined_v2"}'
```

## Error Handling

The API uses standard HTTP status codes and returns structured error responses:

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request body is invalid",
    "details": {
      "field": "sensor_id",
      "issue": "This field is required"
    }
  },
  "timestamp": "2025-06-11T10:30:00Z",
  "request_id": "req_error_123"
}
```

### Common Error Codes

- `400 Bad Request` - Invalid request format or missing required fields
- `401 Unauthorized` - Missing or invalid API key
- `403 Forbidden` - Insufficient permissions for the requested operation
- `404 Not Found` - Requested resource not found
- `422 Unprocessable Entity` - Request validation failed
- `500 Internal Server Error` - Unexpected server error

## Rate Limiting

The API uses slowapi for rate limiting where enabled. Currently enforced:

- `/api/v1/ml/check_drift`: 10 requests per minute per API key

Additional per-endpoint limits can be configured. When limits apply, responses include standard `X-RateLimit-*` headers and `Retry-After` when exceeded.

## Examples

### Complete Data Ingestion Workflow with Enhanced Features

```bash
# 1. Ingest sensor data with idempotency and correlation ID
curl -X POST "http://localhost:8000/api/v1/data/ingest" \
  -H "X-API-Key: your-api-key" \
  -H "X-Request-ID: custom-correlation-123" \
  -H "Idempotency-Key: unique-operation-456" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "TEMP_001",
    "value": 85.5,
    "sensor_type": "temperature",
    "unit": "celsius",
    "location": "Factory Floor A"
  }'

# 2. Generate anomaly report (updated schema)
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
  -H "X-API-Key: your-api-key" \
  -H "X-Request-ID: report-correlation-789" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "anomaly_summary",
    "format": "json",
    "time_range_start": "2025-05-11T00:00:00Z",
    "time_range_end": "2025-06-11T00:00:00Z",
    "include_charts": true
  }'

# 3. Submit maintenance decision
curl -X POST "http://localhost:8000/api/v1/decisions/submit" \
  -H "X-API-Key: your-api-key" \
  -H "X-Request-ID: decision-correlation-101" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req_maintenance_123",
    "decision": "approve",
    "justification": "Temperature anomaly requires immediate attention",
    "operator_id": "operator_001"
  }'

# 4. Check system health and metrics
curl -H "X-API-Key: your-api-key" "http://localhost:8000/health/detailed"
curl "http://localhost:8000/metrics"

# 5. Run ML endpoints
curl -X POST "http://localhost:8000/api/v1/ml/predict" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "ai4i_classifier_randomforest_baseline",
    "model_version": "auto",
    "features": {
      "Air_temperature_K": 298.1,
      "Process_temperature_K": 308.6,
      "Rotational_speed_rpm": 1551,
      "Torque_Nm": 42.8,
      "Tool_wear_min": 108
    }
  }'

curl -X POST "http://localhost:8000/api/v1/ml/check_drift" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "sensor_001",
    "window_minutes": 60,
    "p_value_threshold": 0.05,
    "min_samples": 30
  }'

# 6. Access MLflow models (registry)
curl "http://localhost:5000/api/2.0/mlflow/registered-models/list"
```

### Monitoring and Observability

```bash
# Check Prometheus metrics
curl "http://localhost:8000/metrics" | grep -E "(http_requests|python_gc)"

# Verify correlation ID propagation (middleware echoes header)
curl -H "X-Request-ID: test-trace-123" "http://localhost:8000/health" -v

# Monitor TimescaleDB sensor data
# Connect to database and query recent readings
# See Database documentation for connection details
```

### Load Testing MLflow Registry

```bash
# Run MLflow Registry load test with Locust
docker compose run --rm -v $(pwd):/app -w /app --service-ports ml \
  locust -f locustfile.py --host http://mlflow:5000 \
  --users 5 --run-time 2m --headless --print-stats
```

## Production Deployment Notes

### Model Performance Achievements

Based on the latest comprehensive system analysis (Sprint 10.5):

#### Forecasting Performance
- **Best Model**: Prophet Tuned (hyperparameter optimized)
- **Performance**: 2.8258 MAE vs 3.5704 naive baseline
- **Improvement**: 20.86% reduction in forecasting error
- **Status**: Production-ready and validated

#### Model Comparison Results
```
🏆 MODEL PERFORMANCE HIERARCHY:
├── Prophet Tuned (Best):     2.8258 MAE ← RECOMMENDED
├── Prophet v2 Enhanced:      2.8402 MAE
├── LightGBM Challenger:      3.0994 MAE
└── Naive Baseline:           3.5704 MAE
```

#### System Health Validation
- **Infrastructure**: All core Docker containers operational
- **MLflow Integration**: Comprehensive experiment tracking at http://localhost:5000
- **Database Performance**: TimescaleDB with 9,000+ sensor readings
- **Load Testing**: MLflow Registry validated under concurrent access (0 failures)

### Scalability Considerations

- **Idempotency**: Redis-backed idempotency for ingestion supports multi-replica deployments
- **Database**: TimescaleDB with compression policies for time-series data retention
- **Event Bus**: Retry logic with exponential backoff prevents cascade failures
- **ML Pipeline**: Containerized workflow supports horizontal scaling

### Monitoring Integration

- **Prometheus**: Native metrics endpoint ready for scraping
- **Grafana**: Can be connected to visualize API performance
- **Structured Logging**: JSON format ready for ELK/Loki ingestion
- **Correlation IDs**: End-to-end request tracing across microservices
- **MLflow Tracking**: Complete experiment lifecycle monitoring

### Security Hardening

- **STRIDE Analysis**: Comprehensive threat model in `docs/SECURITY.md`
- **Input Validation**: Pydantic schemas prevent injection attacks
- **Rate Limiting**: Prevents DoS and abuse
- **API Key Management**: Scope-based permissions with rotation support
- **Container Security**: Minimal attack surface with production-grade images
