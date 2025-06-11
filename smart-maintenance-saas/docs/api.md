# Smart Maintenance SaaS - API Documentation

## 📚 Documentation Navigation

This document is part of the Smart Maintenance SaaS documentation suite. For complete system understanding, please also refer to:

- **[Backend README](../README.md)** - Docker deployment and getting started guide
- **[System Screenshots](./SYSTEM_SCREENSHOTS.md)** - Complete visual system walkthrough with screenshots
- **[System and Architecture](./SYSTEM_AND_ARCHITECTURE.md)** - Complete system architecture and component overview
- **[Future Roadmap](./FUTURE_ROADMAP.md)** - Strategic vision and planned enhancements
- **[Deployment Status](./DEPLOYMENT_STATUS.md)** - Current deployment status and container information
- **[Performance Baseline](./PERFORMANCE_BASELINE.md)** - Load testing results and performance metrics baseline
- **[Load Testing Instructions](./LOAD_TESTING_INSTRUCTIONS.md)** - Comprehensive guide for running performance tests
- **[Test Documentation](../tests/README.md)** - Test organization and execution guide
- **[Project Overview](../../README.md)** - High-level project description and objectives

---

## Overview

The Smart Maintenance SaaS API provides a comprehensive RESTful interface for industrial predictive maintenance operations. The API is built with FastAPI and follows OpenAPI 3.0 standards, offering automatic documentation and validation.

**Base URL**: `http://localhost:8000` (Docker deployment)  
**API Version**: v1  
**Production Status**: ✅ Ready  
**Documentation**: 
- Interactive API Docs: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`

## Quick Start with Docker

```bash
# Start the complete system
docker compose up -d

# Access points
# API: http://localhost:8000
# UI: http://localhost:8501
# Docs: http://localhost:8000/docs
```

## Control Panel UI

For easy interaction with the API, a Streamlit-based control panel is available at `http://localhost:8501`. The control panel provides:

- **Visual forms** for all API endpoints
- **Real-time validation** and error handling  
- **System health monitoring** and connectivity checks
- **Quick testing tools** for rapid API exploration

When using Docker: The UI is automatically available at `http://localhost:8501` when you run `docker compose up -d`.

See the [Backend README](../README.md#control-panel-ui-streamlit) for detailed usage instructions.

## Authentication

Currently, the API operates without authentication for development purposes. In production, implement proper authentication mechanisms such as JWT tokens or API keys.

## Core Endpoints

### Data Ingestion

#### POST /api/v1/data/ingest

Ingests sensor data into the Smart Maintenance system for processing and analysis.

**Request Body:**
```json
{
  "sensor_id": "TEMP_001",
  "sensor_type": "temperature",
  "value": 75.2,
  "unit": "celsius",
  "equipment_id": "PUMP_A001",
  "location": "Plant Floor 1",
  "metadata": {
    "calibration_date": "2024-01-15",
    "maintenance_window": "2024-02-01"
  }
}
```

**Response (200 OK):**
```json
{
  "message": "Data ingested successfully",
  "sensor_reading_id": "123e4567-e89b-12d3-a456-426614174000",
  "timestamp": "2024-01-20T10:30:00Z"
}
```

**Sensor Types Supported:**
- `temperature`
- `vibration` 
- `pressure`
- `humidity`
- `current`
- `voltage`

### Reports Generation

#### POST /api/v1/reports/generate

Generates various maintenance and system reports based on the specified report type.

**Request Body:**
```json
{
  "report_type": "anomaly_summary",
  "parameters": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "equipment_ids": ["PUMP_A001", "PUMP_B002"]
  }
}
```

**Report Types Available:**
- `anomaly_summary` - Summary of detected anomalies
- `system_health` - Overall system health report  
- `maintenance_overview` - Maintenance activities overview
- `prediction_accuracy` - ML prediction accuracy metrics
- `custom` - Custom report with flexible parameters

**Response (200 OK):**
```json
{
  "report_id": "rep_123e4567-e89b-12d3-a456-426614174000",
  "report_type": "anomaly_summary",
  "generated_at": "2024-01-20T10:30:00Z",
  "data": {
    "total_anomalies": 15,
    "high_confidence": 8,
    "medium_confidence": 5,
    "low_confidence": 2,
    "equipment_breakdown": {
      "PUMP_A001": 8,
      "PUMP_B002": 7
    }
  }
}
```

### Human Decision Interface

#### POST /api/v1/decisions/submit

Submits human feedback or decisions on system-prompted queries, enabling human-in-the-loop workflows.

**Request Body:**
```json
{
  "decision_id": "dec_123e4567-e89b-12d3-a456-426614174000",
  "decision": "approve",
  "feedback": "Anomaly confirmed - schedule maintenance immediately",
  "metadata": {
    "reviewer": "technician_001",
    "review_date": "2024-01-20T10:30:00Z"
  }
}
```

**Valid Decision Values:**
- `approve` - Approve the system recommendation
- `reject` - Reject the system recommendation
- `modify` - Approve with modifications
- `escalate` - Escalate to higher authority

**Response (200 OK):**
```json
{
  "message": "Decision submitted successfully",
  "decision_id": "dec_123e4567-e89b-12d3-a456-426614174000",
  "status": "processed",
  "next_actions": [
    "Maintenance task scheduled",
    "Notification sent to technician"
  ]
}
```

## Data Models

### SensorReading

```json
{
  "sensor_id": "string",
  "sensor_type": "temperature|vibration|pressure|humidity|current|voltage",
  "value": "number",
  "unit": "string",
  "equipment_id": "string",
  "location": "string",
  "timestamp": "datetime (ISO 8601)",
  "metadata": "object (optional)"
}
```

### AnomalyAlert

```json
{
  "anomaly_id": "uuid",
  "sensor_reading_id": "uuid", 
  "confidence_score": "number (0.0-1.0)",
  "anomaly_type": "statistical|isolation_forest|ensemble",
  "detected_at": "datetime (ISO 8601)",
  "equipment_id": "string",
  "severity": "low|medium|high|critical",
  "validation_status": "pending|validated|false_positive"
}
```

### MaintenanceTask

```json
{
  "task_id": "uuid",
  "equipment_id": "string",
  "task_type": "preventive|corrective|predictive",
  "priority": "low|medium|high|urgent",
  "scheduled_date": "datetime (ISO 8601)",
  "estimated_duration": "number (hours)",
  "assigned_technician": "string",
  "status": "scheduled|in_progress|completed|cancelled"
}
```

## Error Responses

The API uses standard HTTP status codes and returns errors in a consistent format:

### 400 Bad Request
```json
{
  "detail": "Invalid sensor type. Must be one of: temperature, vibration, pressure, humidity, current, voltage"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "sensor_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error occurred while processing the request"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing:
- 1000 requests per hour for data ingestion endpoints
- 100 requests per hour for report generation endpoints  
- 50 requests per hour for decision submission endpoints

## Usage Examples

### Python Client Example

```python
import requests
import json

# Ingest sensor data
sensor_data = {
    "sensor_id": "TEMP_001",
    "sensor_type": "temperature", 
    "value": 85.5,
    "unit": "celsius",
    "equipment_id": "PUMP_A001",
    "location": "Plant Floor 1"
}

response = requests.post(
    "http://localhost:8000/api/v1/data/ingest",
    json=sensor_data
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Generate anomaly report
report_request = {
    "report_type": "anomaly_summary",
    "parameters": {
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
    }
}

response = requests.post(
    "http://localhost:8000/api/v1/reports/generate",
    json=report_request
)

print(f"Report: {response.json()}")
```

### cURL Examples

```bash
# Ingest temperature data
curl -X POST "http://localhost:8000/api/v1/data/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "TEMP_001",
    "sensor_type": "temperature",
    "value": 75.2,
    "unit": "celsius", 
    "equipment_id": "PUMP_A001",
    "location": "Plant Floor 1"
  }'

# Generate system health report
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "system_health",
    "parameters": {}
  }'

# Submit decision
curl -X POST "http://localhost:8000/api/v1/decisions/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "decision_id": "dec_123e4567-e89b-12d3-a456-426614174000",
    "decision": "approve",
    "feedback": "Anomaly confirmed"
  }'
```

## Interactive API Documentation

For hands-on exploration and testing, visit the interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces provide:
- Real-time API testing capabilities
- Detailed schema documentation  
- Example requests and responses
- Authentication testing (when implemented)

---

*For more technical details about the system architecture and agent workflows, see the [System and Architecture Documentation](./SYSTEM_AND_ARCHITECTURE.md).*

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Authentication

All API endpoints require authentication via API key. Include the API key in the request header:

```http
X-API-Key: your-api-key-here
```

### API Key Scopes

The API uses a scope-based permission system:

- `data:ingest` - Permission to ingest sensor data
- `reports:generate` - Permission to generate reports
- `tasks:update` - Permission to submit human decisions

## Health Check Endpoints

### GET /health

Basic health check for the API service.

**Response:**

```json
{
  "status": "healthy"
}
```

### GET /health/db

Database connectivity health check.

**Response:**

```json
{
  "db_status": "connected"
}
```

**Error Response (503):**

```json
{
  "detail": "Database connection error: <error_message>"
}
```

## Data Ingestion Endpoints

### POST /api/v1/data/ingest

Ingests sensor data into the Smart Maintenance system and triggers the event-driven processing pipeline.

**Required Scope:** `data:ingest`

**Request Body:**
```json
{
  "sensor_id": "sensor_001",
  "value": 45.6,
  "timestamp": "2025-06-10T10:30:00Z",
  "sensor_type": "temperature",
  "unit": "°C",
  "quality": 1.0,
  "correlation_id": "optional-uuid",
  "metadata": {
    "location": "Factory Floor A",
    "equipment_id": "pump_123"
  }
}
```

**Request Schema (`SensorReadingCreate`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sensor_id` | string | Yes | Unique sensor identifier |
| `value` | float | Yes | The sensor reading value |
| `timestamp` | datetime | No | UTC timestamp (defaults to current time) |
| `sensor_type` | enum | No | Type: "temperature", "vibration", "pressure" |
| `unit` | string | No | Unit of measurement |
| `quality` | float | No | Data quality score (0.0-1.0, default: 1.0) |
| `correlation_id` | UUID | No | Correlation ID for tracking (auto-generated if not provided) |
| `metadata` | object | No | Additional metadata as key-value pairs |

**Response (200):**
```json
{
  "status": "event_published",
  "event_id": "12345678-1234-5678-9abc-123456789abc",
  "correlation_id": "87654321-4321-8765-cba9-987654321cba",
  "sensor_id": "sensor_001"
}
```

**Error Responses:**
- `500` - System coordinator or event bus not available
- `422` - Validation error in request data

## Reporting Endpoints

### POST /api/v1/reports/generate

Generates maintenance and system health reports using the ReportingAgent with enhanced async processing.

**Required Scope:** `reports:generate`

**Request Body:**
```json
{
  "report_type": "performance_summary",
  "format": "text",
  "time_range_start": "2025-06-01T00:00:00Z",
  "time_range_end": "2025-06-10T23:59:59Z",
  "parameters": {
    "include_details": true,
    "severity_threshold": "medium"
  },
  "include_charts": true
}
```

**Request Schema (`ReportRequest`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `report_type` | string | Yes | Type of report (see available types below) |
| `format` | string | No | Output format ("json", "text", default: "json") |
| `time_range_start` | datetime | No | Start time for report data (UTC) |
| `time_range_end` | datetime | No | End time for report data (UTC) |
| `parameters` | object | No | Additional report-specific parameters |
| `include_charts` | boolean | No | Whether to include matplotlib charts (default: true) |

**Available Report Types:**

- `performance_summary` - Overall system performance metrics and KPIs
- `anomaly_summary` - Summary of detected anomalies and their status
- `maintenance_summary` - Summary of maintenance activities and schedules  
- `system_health` - Comprehensive system health and status report
- `equipment_status` - Status report for specific equipment
- `prediction_accuracy` - Machine learning model performance metrics

**Enhanced Features:**

- **Async Processing**: Uses ThreadPoolExecutor to prevent blocking on matplotlib and analytics operations
- **Visual Charts**: Automatically generates base64-encoded PNG charts when `include_charts=true`
- **Multiple Formats**: JSON for structured data, text for human-readable reports
- **Rich Metadata**: Includes generation time, data points analyzed, and analytics summary

**Response (200):**
```json
{
  "report_id": "report-a1b2c3d4",
  "report_type": "performance_summary",
  "format": "text",
  "content": "REPORT SUMMARY\n=============\n\nReport Type: performance_summary\nData Points: 285\nProcessing Time: 12.38 ms\n\nGenerated on: 2025-06-10 14:45:00 UTC",
  "generated_at": "2025-06-10T14:45:00.313548+00:00",
  "charts_encoded": {
    "main_chart": "iVBORw0KGgoAAAANSUhEUgAAAoAAAAHgCAYAAAA..."
  },
  "metadata": {
    "parameters": {
      "include_details": true
    },
    "time_range_start": "2025-06-01T00:00:00+00:00",
    "time_range_end": "2025-06-10T23:59:59+00:00",
    "include_charts": true,
    "analytics_summary": {
      "data_points": 285,
      "has_chart_data": true
    }
  },
  "error_message": null
}
```

**Technical Implementation:**

- **Thread Pool Processing**: Reports are generated in a separate thread to avoid blocking the async event loop
- **Chart Generation**: Uses matplotlib with Agg backend for server-side chart generation
- **Error Handling**: Comprehensive error reporting with correlation IDs for debugging
```

**Error Responses:**
- `500` - System coordinator or reporting agent not available
- `422` - Validation error in request data

## Human Decision Endpoints

### POST /api/v1/decisions/submit

Submits human operator decisions in response to system prompts requiring human-in-the-loop input.

**Required Scope:** `tasks:update`

**Request Body:**
```json
{
  "request_id": "decision_req_12345",
  "decision": "approve_maintenance",
  "justification": "Critical temperature anomaly detected, immediate maintenance required",
  "operator_id": "operator_jane_doe",
  "confidence": 0.95,
  "additional_notes": "Contacted equipment vendor for specialized parts",
  "correlation_id": "anomaly_correlation_abc123"
}
```

**Request Schema (`DecisionResponse`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request_id` | string | Yes | ID of the original decision request |
| `decision` | string | Yes | The chosen decision/action |
| `justification` | string | No | Explanation for the decision |
| `operator_id` | string | Yes | ID of the human operator making the decision |
| `timestamp` | datetime | No | When decision was made (auto-generated) |
| `confidence` | float | No | Confidence level (0.0-1.0, default: 1.0) |
| `additional_notes` | string | No | Additional notes or comments |
| `correlation_id` | string | No | Correlation ID for tracking |

**Common Decision Types:**
- `approve_maintenance` - Approve scheduled maintenance
- `reject_maintenance` - Reject/postpone maintenance
- `escalate_to_supervisor` - Escalate to higher authority
- `request_additional_data` - Request more information
- `manual_override` - Override system recommendation
- `confirm_anomaly` - Confirm detected anomaly
- `false_positive` - Mark as false positive

**Response (201):**
```json
{
  "status": "success",
  "event_id": "87654321-4321-8765-cba9-987654321cba",
  "request_id": "decision_req_12345"
}
```

**Error Responses:**
- `500` - System coordinator or event bus not available
- `422` - Validation error in request data

## Event-Driven Architecture

The API endpoints trigger events in the multi-agent system:

### Data Ingestion Flow
1. `POST /api/v1/data/ingest` → `SensorDataReceivedEvent`
2. `DataAcquisitionAgent` processes and validates data
3. `AnomalyDetectionAgent` analyzes for anomalies
4. `ValidationAgent` validates detected anomalies
5. `OrchestratorAgent` coordinates next steps

### Reporting Flow
1. `POST /api/v1/reports/generate` → Direct call to `ReportingAgent`
2. Agent queries database and generates report
3. Optional chart generation and encoding
4. Return structured report data

### Human Decision Flow
1. System generates `HumanDecisionRequiredEvent`
2. UI/external system calls `POST /api/v1/decisions/submit`
3. Creates `HumanDecisionResponseEvent`
4. `OrchestratorAgent` processes decision and continues workflow

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages:

### Standard Error Response Format
```json
{
  "detail": "Error description here"
}
```

### Common Status Codes
- `200` - Success
- `201` - Created successfully
- `422` - Validation error (invalid request data)
- `500` - Internal server error
- `503` - Service unavailable (database connectivity issues)

### Validation Errors (422)
```json
{
  "detail": [
    {
      "loc": ["body", "sensor_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Rate Limiting

The API implements rate limiting to ensure system stability:

- Data ingestion: 100 requests per minute per API key
- Report generation: 10 requests per minute per API key
- Decision submission: 50 requests per minute per API key

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1718026800
```

## Data Formats

### DateTime Format
All datetime fields use ISO 8601 format in UTC:
```
2025-06-10T14:30:00Z
```

### UUID Format
UUIDs follow RFC 4122 standard:
```
12345678-1234-5678-9abc-123456789abc
```

### Sensor Types
Supported sensor types:
- `temperature` - Temperature sensors (°C, °F, K)
- `vibration` - Vibration sensors (mm/s, g, Hz)
- `pressure` - Pressure sensors (Pa, psi, bar)

## Example Workflows

### Complete Sensor Data Processing
```bash
# 1. Ingest sensor data
curl -X POST "http://localhost:8000/api/v1/data/ingest" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "temp_001",
    "value": 85.5,
    "sensor_type": "temperature",
    "unit": "°C"
  }'

# 2. Generate anomaly report
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "anomaly_summary",
    "format": "json"
  }'

# 3. Submit human decision (if required)
curl -X POST "http://localhost:8000/api/v1/decisions/submit" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "decision_12345",
    "decision": "approve_maintenance",
    "operator_id": "maintenance_supervisor_01"
  }'
```

## Security Considerations

- Always use HTTPS in production
- Rotate API keys regularly
- Implement IP whitelisting for additional security
- Monitor API usage for anomalous patterns
- Use scope-based permissions appropriately

## Monitoring and Observability

The API provides built-in monitoring capabilities:

- Health check endpoints for uptime monitoring
- Structured logging for request/response tracking
- Correlation IDs for distributed tracing
- Performance metrics via built-in FastAPI instrumentation

## SDK and Client Libraries

For easier integration, consider using:

- Python: `httpx` or `requests` libraries
- JavaScript/Node.js: `axios` or `fetch`
- cURL: For testing and scripting

Example Python client:
```python
import httpx

class SmartMaintenanceClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    async def ingest_sensor_data(self, sensor_data: dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/data/ingest",
                json=sensor_data,
                headers=self.headers
            )
            return response.json()
```

## Support and Documentation

- **Interactive API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **System Architecture**: [SYSTEM_AND_ARCHITECTURE.md](./SYSTEM_AND_ARCHITECTURE.md)
- **Load Testing Guide**: [LOAD_TESTING_INSTRUCTIONS.md](./LOAD_TESTING_INSTRUCTIONS.md)

---

**Note**: This API documentation reflects the current implementation of the Smart Maintenance SaaS backend. For the most up-to-date endpoint details and schemas, refer to the interactive API documentation at `/docs`.
