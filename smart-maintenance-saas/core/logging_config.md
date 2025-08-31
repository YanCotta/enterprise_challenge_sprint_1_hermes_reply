# Smart Maintenance SaaS - Complete Documentation Index

## Core Documentation

### Getting Started

- **[Main README](../../../README.md)** - Project overview, quick start, and repository structure
- **[Backend README](../../README.md)** - Docker deployment and getting started guide
- **[Development Orientation](../../../DEVELOPMENT_ORIENTATION.md)** - Development guidelines and best practices

### Project History & Changelog

- **[30-Day Sprint Changelog](../../../30-day-sprint-changelog.md)** - Complete development history and daily progress
- **[Final Sprint Summary](../../../final_30_day_sprint.md)** - Executive summary of sprint achievements

## System Architecture & Design

### Architecture Documentation

- **[System and Architecture](../../docs/SYSTEM_AND_ARCHITECTURE.md)** - Comprehensive system architecture and design patterns
- **[System Screenshots](../../docs/SYSTEM_SCREENSHOTS.md)** - Visual documentation of system interfaces
- **[Comprehensive System Analysis](../../docs/COMPREHENSIVE_SYSTEM_ANALYSIS_REPORT.md)** - Detailed technical analysis report
- **[Microservice Migration Strategy](../../docs/MICROSERVICE_MIGRATION_STRATEGY.md)** - Future architecture evolution plans

### Database Design

- **[Database Documentation](../../docs/db/README.md)** - Database schema and design documentation
- **[Database ERD](../../docs/db/erd.dbml)** - Entity Relationship Diagram source
- **[Database ERD (PNG)](../../docs/db/erd.png)** - Entity Relationship Diagram visualization
- **[Database ERD (Dark Mode)](../../docs/db/erd_darkmode.png)** - Entity Relationship Diagram (dark theme)
- **[Database Schema](../../docs/db/schema.sql)** - Complete SQL schema definition

## API & Integration

### API Documentation

- **[API Reference](../../docs/api.md)** - Complete REST API documentation and examples
- **[Configuration Management](./config/README.md)** - Centralized configuration system
- **[Logging Configuration](./logging_config.md)** - Structured JSON logging setup

## Performance & Testing

### Performance Documentation

- **[Performance Baseline](../../docs/PERFORMANCE_BASELINE.md)** - Performance metrics and SLO targets
- **[Day 17 Load Test Report](../../docs/DAY_17_LOAD_TEST_REPORT.md)** - Comprehensive load testing results (103.8 RPS)
- **[Day 18 Performance Results](../../docs/DAY_18_PERFORMANCE_RESULTS.md)** - TimescaleDB optimization results
- **[Load Testing Instructions](../../docs/LOAD_TESTING_INSTRUCTIONS.md)** - Guide for running performance tests

### Testing Documentation

- **[Test Documentation](../tests/README.md)** - Test organization and execution guide
- **[Coverage Improvement Plan](../../docs/COVERAGE_IMPROVEMENT_PLAN.md)** - Test coverage strategy and current status

## Machine Learning & Data Science

### ML Documentation

- **[ML Documentation](../../docs/ml/README.md)** - Machine learning models and pipelines
- **[Models Summary](../../docs/MODELS_SUMMARY.md)** - Overview of all 17+ production models
- **[Project Gauntlet Plan](../../docs/PROJECT_GAUNTLET_PLAN.md)** - Real-world dataset integration execution

## Security & Operations

### Security Documentation

- **[Security Documentation](../../docs/SECURITY.md)** - Security architecture and implementation
- **[Security Audit Checklist](../../docs/SECURITY_AUDIT_CHECKLIST.md)** - Comprehensive security audit framework

### Service Documentation

- **[Anomaly Service](../services/anomaly_service/README.md)** - Future anomaly detection microservice
- **[Prediction Service](../services/prediction_service/README.md)** - Future ML prediction microservice

---

*This index is automatically maintained and appears at the top of all documentation files for easy navigation.*

---

# Structured JSON Logging & Correlation Architecture

This document specifies the production logging architecture for Smart Maintenance SaaS, synchronized with sprint changelog events (Days 4–23).

---

## 1. Purpose

Provide:
- Machine‑parsable JSON logs
- Deterministic correlation across HTTP requests, background agents, and event bus messages
- Low‑overhead diagnostics for performance, ML lifecycle, drift automation, and resilience testing
- A secure baseline (no secrets / PII) ready for future OpenTelemetry expansion

---

## 2. Design Goals

| Goal | Implementation |
|------|----------------|
| Correlation across layers | X-Request-ID middleware + ContextVar filter |
| JSON structure | Single custom Formatter (ISO8601 UTC) |
| Low overhead | Synchronous stdlib logging (~ microseconds per call) |
| Extensibility | `extra={}` passthrough & helper filters |
| Failure transparency | Full exception trace with structured fields |
| Event lineage | Correlation ID forwarded into events & agents |
| Security hygiene | Whitelisted fields; no secret interpolation |

---

## 3. Architecture Overview (Flow)

Client → FastAPI Middleware (assign / propagate X-Request-ID) → Business / ML layer log calls (ContextVar supplies correlation_id) → Event Bus publisher adds same correlation_id into event payload → Background agent / retrain worker restores correlation context → JSON emitted to STDOUT (container runtime) → Aggregated by log collector (ELK / Loki future).

---

## 4. Core Components

| Component | Role |
|-----------|------|
| `setup_logging()` | Initializes root logger, sets JSON formatter, attaches stream handler (idempotent) |
| `get_logger(name)` | Returns module / domain logger pre-configured |
| `CorrelationIdFilter` (ContextVar) | Injects `correlation_id` into every record if present |
| Request ID Middleware (`apps/api/middleware/request_id.py`) | Extract or create UUIDv4; sets header + context |
| Event Bus (`core/events/event_bus.py`) | Includes correlation_id in published event dict |
| Retry Wrapper (tenacity) | Emits attempt count & backoff semantics in structured logs |

---

## 5. Log Schema

Field | Description
------|------------
timestamp | UTC ISO8601 with microseconds
level | Log level (INFO, WARNING, ERROR, DEBUG)
message | Human-readable event description
logger | Logger name (module dotted path)
service | Static service identifier (e.g. api, drift_agent)
correlation_id | Request / workflow trace UUID
file | Origin filename
line | Source line number
process / thread | Execution context
hostname | Container host identifier
event_type (optional) | Domain event name (e.g. AnomalyDetectedEvent)
model_name / model_version (optional) | ML operation context
attempt / max_attempts (optional) | Retry metadata
duration_ms (optional) | Operation latency
extra-* | Any additional domain fields via `extra={}`

Example (anomaly model load):

```json
{
  "timestamp": "2025-08-26T19:42:11.281904Z",
  "level": "INFO",
  "message": "Model loaded",
  "logger": "apps.ml.model_loader",
  "service": "api",
  "correlation_id": "0b7e9e9c-0d3a-47bb-9a7b-a0d2f1f7c901",
  "model_name": "vibration_anomaly_isolationforest",
  "model_version": "3",
  "duration_ms": 18.4
}
```

---

## 6. Correlation & Propagation

Source | Mechanism
-------|----------
Inbound HTTP | `X-Request-ID` header (client-supplied or generated)
Event Bus | Field copied when publishing
Background Agents (drift / retrain) | Restored from event payload into ContextVar
Nested Calls | Child loggers inherit filter
External API / future microservices | Pass `X-Request-ID` forward; treat absence as new root span

If correlation id missing in log lines → check middleware order or early import (see troubleshooting).

---

## 7. Usage Patterns

### 7.1 Basic

```python
from core.logging_config import get_logger
logger = get_logger(__name__)
logger.info("Scheduled drift check started")
```

### 7.2 With Extra Fields

```python
logger.info(
    "Drift metrics computed",
    extra={"model_name": model, "p_value": round(p, 5), "ks_stat": stat}
)
```

### 7.3 Exception Logging

```python
try:
    loader.load_model(name, version)
except Exception:
    logger.exception("Model load failed", extra={"model_name": name, "model_version": version})
```

### 7.4 Retry (Event Bus Handler)

Inside retry-decorated function, augment with attempt metadata:

```python
logger.warning(
    "Event handler retry",
    extra={"event_type": event.type, "attempt": attempt, "max_attempts": max_attempts}
)
```

### 7.5 ML Lifecycle

Stage | Recommended Fields
------|-------------------
Train start | model_name, dataset, run_id
Train complete | model_name, metrics dict, duration_ms
Drift detected | model_name, p_value, window_minutes
Retrain scheduled | model_name, trigger="drift", cooldown_active(bool)
Retrain skipped | model_name, reason
Prediction | model_name, model_version, latency_ms

### 7.6 Idempotent Ingestion

```python
logger.info(
  "Ingestion duplicate ignored",
  extra={"sensor_id": sid, "idempotency_key": key, "event_id": original_id}
)
```

### 7.7 Async Tasks

ContextVar handles async boundaries. If spawning threads (e.g. ThreadPoolExecutor) pass correlation id manually:

```python
cid = get_correlation_id()
executor.submit(run_with_context, cid, task_fn)
```

---

## 8. Performance Characteristics

Metric | Observation
-------|------------
Average log emit cost | < 0.2 ms (Day 6 validation)
P95 request latency impact | Negligible (overall P95 2 ms under load Day 17)
Memory overhead | Single handler; no accumulation
Throughput verified | 100+ RPS sustained without log-induced backpressure

---

## 9. Security & Compliance

Control | Status
--------|-------
Secret Redaction | Do not log API keys / tokens (enforced by review)
PII | None collected / emitted
Injection Safety | Structured JSON, no string eval
Rate Limit Events | Logged without user-identifying payload
Future | Add optional hashing for sensor IDs if privacy requirements evolve

Optional future hook: implement a `SensitiveValueFilter` to whitelist keys.

---

## 10. Observability Integration

- Metrics (Prometheus) supply quantitative latency; logs supply qualitative root cause.
- Correlation IDs allow pairing a slow request metric sample with precise log sequence.
- Drift / retrain events produce structured series enabling downstream alert rules (e.g. count of drift_detected per hour).

---

## 11. Troubleshooting

Symptom | Likely Cause | Resolution
--------|--------------|-----------
Missing correlation_id | Middleware not registered first / early import | Ensure middleware added before routers
Duplicate log lines | `setup_logging()` called twice | Guard with module-level flag (already implemented)
Plain text output | External lib logger without propagation | Attach filter to 3rd-party logger or adjust log level
JSON parse errors downstream | Out-of-band prints | Remove stray `print()` / use logger
Model load 404 w/out stack trace | Exception swallowed pre-Day12 code | Confirm updated model_loader w/ `.exception()`

---

## 12. Extensibility

Add global field:
1. Extend custom formatter to inject `environment` (e.g. from settings)
2. Adjust CI tests validating schema (future enhancement)
3. Document new field in Section 5

Planned extensions:
- OpenTelemetry trace/span id injection
- Structured sampling for high-volume success logs
- Log shipping sidecar (Fluent Bit) configuration

---

## 13. Operational Guidelines

Action | Recommendation
-------|---------------
High-frequency loops | Use DEBUG and guard by config
Bulk data dumps | Avoid logging large payloads; summarize counts
Exception floods | Add circuit breaker or temporary downgrade to WARNING
Drift storm | Only first detection per model within cooldown logs at INFO; subsequent suppressed to DEBUG
Cold model loads | Emit duration_ms; page if > threshold (future alert)

---

## 14. Minimal Public API (Code Reference)

```python
# core/logging_config.py (excerpt)
def setup_logging():
    # idempotent initialization
    # create handler -> JSONFormatter -> add CorrelationIdFilter
    ...

def get_logger(name: str):
    return logging.getLogger(name)
```

(Note: File implements ContextVar & filter registration; unchanged runtime code.)

---

## 15. Changelog Mapping

Feature / Change | Changelog Day(s)
-----------------|-----------------
Request IDs added | Day 4
Structured logging & correlation filter | Day 6
Event bus retry visibility | Day 6
Prediction endpoint instrumentation & error surfacing | Day 12
Drift endpoint + statistical logging | Day 13
Idempotent ingestion duplicate logging | Day 15
Load test validation of negligible overhead | Day 17
Performance optimization logs (CAGG rationale) | Day 18
Model hash validation (integrity logging) | Day 21
Intelligent model selection tagging logs | Day 21.5
Drift + retrain agents lifecycle logging | Day 23

---

## 16. Summary

The logging layer delivers low-latency structured observability across API, ML workflows, drift automation, and resilience subsystems, enabling rapid root-cause analysis while remaining compliant and production-ready.

---
- `timestamp`: Timestamp em formato ISO8601 (UTC)
- `level`: Nível do log (INFO, WARNING, ERROR, etc.)
- `name`: Nome do logger
- `message`: Mensagem do log
- `service`: Nome do serviço
- `hostname`: Identificador do host
- `file`: Arquivo fonte
- `line`: Número da linha
- `process` e `process_name`: Informações do processo
- `thread` e `thread_name`: Informações da thread
- `correlation_id`: ID da requisição (quando disponível)
- Quaisquer campos adicionais passados via `extra`

## Exemplo de Saída

```json
{
  "timestamp": "2025-06-11T12:30:38.161550Z",
  "level": "INFO",
  "name": "api",
  "message": "Usuário autenticado com sucesso",
  "service": "smart-maintenance-saas",
  "hostname": "server-01",
  "file": "user_service.py",
  "line": 56,
  "process": 123456,
  "process_name": "MainProcess",
  "thread": 140123456789,
  "thread_name": "MainThread",
  "correlation_id": "44f05c3e-6723-4b97-a208-3d874a3c50c7",
  "username": "john.doe",
  "roles": ["user", "admin"],
  "auth_method": "password"
}
```
