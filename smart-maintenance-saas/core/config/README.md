# Smart Maintenance SaaS - Complete Documentation Index

## Core Documentation

### Getting Started

- **[Main README](../../../../README.md)** - Project overview, quick start, and repository structure
- **[Backend README](../../../README.md)** - Docker deployment and getting started guide
- **[Development Orientation](../../../../DEVELOPMENT_ORIENTATION.md)** - Development guidelines and best practices

### Project History & Changelog

- **[30-Day Sprint Changelog](../../../../30-day-sprint-changelog.md)** - Complete development history and daily progress
- **[Final Sprint Summary](../../../../final_30_day_sprint.md)** - Executive summary of sprint achievements

## System Architecture & Design

### Architecture Documentation

- **[System and Architecture](../../../docs/SYSTEM_AND_ARCHITECTURE.md)** - Comprehensive system architecture and design patterns
- **[System Screenshots](../../../docs/SYSTEM_SCREENSHOTS.md)** - Visual documentation of system interfaces
- **[Comprehensive System Analysis](../../../docs/COMPREHENSIVE_SYSTEM_ANALYSIS_REPORT.md)** - Detailed technical analysis report
- **[Microservice Migration Strategy](../../../docs/MICROSERVICE_MIGRATION_STRATEGY.md)** - Future architecture evolution plans

### Database Design

- **[Database Documentation](../../../docs/db/README.md)** - Database schema and design documentation
- **[Database ERD](../../../docs/db/erd.dbml)** - Entity Relationship Diagram source
- **[Database ERD (PNG)](../../../docs/db/erd.png)** - Entity Relationship Diagram visualization
- **[Database ERD (Dark Mode)](../../../docs/db/erd_darkmode.png)** - Entity Relationship Diagram (dark theme)
- **[Database Schema](../../../docs/db/schema.sql)** - Complete SQL schema definition

## API & Integration

### API Documentation

- **[API Reference](../../../docs/api.md)** - Complete REST API documentation and examples
- **[Configuration Management](./README.md)** - Centralized configuration system
- **[Logging Configuration](../../core/logging_config.md)** - Structured JSON logging setup

## Performance & Testing

### Performance Documentation

- **[Performance Baseline](../../../docs/PERFORMANCE_BASELINE.md)** - Performance metrics and SLO targets
- **[Day 17 Load Test Report](../../../docs/DAY_17_LOAD_TEST_REPORT.md)** - Comprehensive load testing results (103.8 RPS)
- **[Day 18 Performance Results](../../../docs/DAY_18_PERFORMANCE_RESULTS.md)** - TimescaleDB optimization results
- **[Load Testing Instructions](../../../docs/LOAD_TESTING_INSTRUCTIONS.md)** - Guide for running performance tests

### Testing Documentation

- **[Test Documentation](../../tests/README.md)** - Test organization and execution guide
- **[Coverage Improvement Plan](../../../docs/COVERAGE_IMPROVEMENT_PLAN.md)** - Test coverage strategy and current status

## Machine Learning & Data Science

### ML Documentation

- **[ML Documentation](../../../docs/ml/README.md)** - Machine learning models and pipelines
- **[Models Summary](../../../docs/MODELS_SUMMARY.md)** - Overview of all 17+ production models
- **[Project Gauntlet Plan](../../../docs/PROJECT_GAUNTLET_PLAN.md)** - Real-world dataset integration execution

## Security & Operations

### Security Documentation

- **[Security Documentation](../../../docs/SECURITY.md)** - Security architecture and implementation
- **[Security Audit Checklist](../../../docs/SECURITY_AUDIT_CHECKLIST.md)** - Comprehensive security audit framework

### Service Documentation

- **[Anomaly Service](../../services/anomaly_service/README.md)** - Future anomaly detection microservice
- **[Prediction Service](../../services/prediction_service/README.md)** - Future ML prediction microservice

---

*This index is automatically maintained and appears at the top of all documentation files for easy navigation.*

---

# Configuration Management (Pydantic BaseSettings)

Centralized, explicit, 12‑factor aligned runtime configuration for the Smart Maintenance SaaS backend. Synchronized with changelog (Days 4–23).

---

## 1. Purpose

Provide a single, declarative source of runtime behavior (database, security, ML, event handling, orchestration) enabling:
- Predictable container start (no hidden "magic" defaults)
- Reproducible ML & drift automationtion Management (Pydantic BaseSettings)

Centralized, explicit, 12‑factor aligned runtime configuration for the Smart Maintenance SaaS backend. Synchronized with changelog (Days 4–23).

---

## 1. Purpose

Provide a single, declarative source of runtime behavior (database, security, ML, event handling, orchestration) enabling:
- Predictable container start (no hidden “magic” defaults)
- Reproducible ML & drift automation
- Safe resilience tuning (retries, DLQ)
- Observability correlation (static metadata + dynamic toggles)

---

## 2. Design Principles

| Principle | Implementation |
|-----------|----------------|
| Explicit over implicit | All tunables declared in `core/config/settings.py` |
| 12‑Factor config | Environment variables (.env for dev only) |
| Immutable at runtime | Settings loaded once at process start (no hot reload) |
| Separation of concerns | Infra (DB, Redis) vs Domain (orchestrator) vs ML |
| Fail fast | Missing mandatory secrets raise ValidationError |
| Safe defaults | Conservative retry counts, disabled advanced schedulers |
| Traceability | Changelog references for new settings (e.g. retries Day 6) |

---

## 3. Load & Precedence Order

1. Environment variables (highest)
2. `.env` file (development / local only)
3. In‑class default values (fallback)
4. Code overrides (test fixtures using `get_settings()`)

No dynamic mutation after instantiation. Use dependency injection (`Depends(get_settings)`) in FastAPI endpoints / background tasks.

---

## 4. Access Patterns

```python
from core.config import settings
db_url = settings.database_url
```

FastAPI DI:

```python
from fastapi import Depends
from core.config import get_settings, Settings

@router.get("/health/config")
def config_probe(cfg: Settings = Depends(get_settings)):
    return {"debug": cfg.debug, "dlq_enabled": cfg.dlq_enabled}
```

---

## 5. Settings Reference (Current Surface)

Group | Keys (prefix) | Notes / Changelog
------|---------------|------------------
Database | DATABASE_URL / DB_* | Composite index + CAGG (Day 18) rely on correct target DB
API Core | API_HOST, API_PORT, DEBUG | DEBUG=false recommended in prod
Security | SECRET_KEY, API_KEY, ACCESS_TOKEN_EXPIRE_MINUTES | API_KEY used by rate limiting (Day 16)
Orchestrator | ORCHESTRATOR_* | Threshold logic for maintenance prediction & auto‑approval
Event Bus & DLQ | EVENT_HANDLER_MAX_RETRIES, EVENT_HANDLER_RETRY_DELAY_SECONDS, DLQ_ENABLED, DLQ_LOG_FILE | Retry & resilience improvements (Day 6, Day 12)
Logging | LOG_LEVEL | Structured JSON layer (Day 6)
ML / Registry | MODEL_REGISTRY_PATH | MLflow now persistent volume (Days 9–13 infra hardening)
Agent Ops | AGENT_COMMUNICATION_TIMEOUT | Agent-to-agent / workflow deadlines
Scheduling | USE_OR_TOOLS_SCHEDULER | Advanced solver deferred (placeholder)
Notification | WHATSAPP_API_KEY, EMAIL_SMTP_* | Optional; not required for core flows
Cache / MQ (future) | REDIS_URL, KAFKA_BOOTSTRAP_SERVERS | Redis used for idempotency & events (Days 4, 15); Kafka future
Testing | TEST_DATABASE_URL | Isolated DB for integration / CI tests

(See Section 6 for critical rationale.)

---

## 6. Critical Settings & Rationale

| Setting | Why It Matters | Failure Mode if Misconfigured |
|---------|----------------|-------------------------------|
| DATABASE_URL | Timescale hypertable + CAGG (Day 18) rely on correct instance | Startup DB errors, drift endpoint fails |
| API_KEY | Auth + rate limiting identity (Day 16) | 403 on protected endpoints or no isolation |
| SECRET_KEY | Token / signing primitives (future) | Weak cryptographic posture |
| EVENT_HANDLER_MAX_RETRIES | Backoff window for anomaly / drift events (Day 6) | Lost events under transient faults |
| DLQ_ENABLED | Post‑retry capture for investigation | Silent event loss |
| MODEL_REGISTRY_PATH | Legacy local model storage fallback | Inference fails if MLflow unreachable |
| ORCHESTRATOR_* thresholds | Auto-approval business logic gating | Over / under scheduling of maintenance |
| REDIS_URL | Idempotent ingestion (Days 4, 15) & event pub/sub | Duplicate events, reduced resilience |
| LOG_LEVEL | Noise vs signal in production analysis | Debug noise or missing forensic detail |

---

## 7. Drift & ML Lifecycle Dependencies

Automated drift / retrain agents (Day 23) expect:
- Stable DB connection (reference & current windows)
- Redis (event emission & consumption)
- Persistent MLflow volume (model version increment)
Configuration alignment ensures: drift event → retrain agent → new model version registered → selection UI tags.

---

## 8. Production Hardening Recommendations

Area | Short Term | Future (Roadmap)
-----|------------|-----------------
Secrets | Move API_KEY / SECRET_KEY to vault | Dynamic rotation + audit
Rate Limiting | Code constant | Externalize limit/window per endpoint
Drift Windows | Hard-coded logic | Expose DRIFT_WINDOW_MINUTES, DRIFT_MIN_SAMPLES
Retrain Cooldowns | In-script defaults | CONFIG: MODEL_RETRAIN_COOLDOWN_HOURS
Redis | Single instance | Sentinel / cluster aware URL
Scopes | Single API_KEY | Add SCOPED_KEYS mapping (JSON env)

(Do not add env vars until implemented.)

---

## 9. Adding a New Setting (Checklist)

1. Add field to `Settings` class with type + default.
2. Update `.env.example` (document intent & security sensitivity).
3. Reference via `settings.new_value` (avoid re-import caches).
4. Add test: override with `monkeypatch.setenv` → assert propagation.
5. Update this README (Section 5 or 6).
6. If security / performance critical: add to SECURITY_AUDIT_CHECKLIST / PERFORMANCE_BASELINE.

---

## 10. Patterns & Anti‑Patterns

Good:
```python
timeout = settings.agent_communication_timeout
```
Bad:
```python
from core.config.settings import Settings; Settings().agent_communication_timeout  # new instance
```

Avoid constructing new Settings instances; single instantiation preserves consistent view.

---

## 11. Precedence & Environment Profiles

Profile | Mechanism | Notes
--------|-----------|------
Local Dev | `.env` + docker compose | Compose service names (db, redis) not localhost
CI | Explicit env injection | Avoid `.env` leakage
Prod | Managed secrets store export | No `.env` file baked into image

---

## 12. Security Considerations

- No secrets logged (logging layer redacts by omission).
- `.env` excluded from VCS (validated Day 7).
- Future: add `ALLOWED_ORIGINS`, `RATE_LIMIT_REDIS_URL` when multi-replica.

---

## 13. Observability Tie‑Ins

LOG_LEVEL influences:
- Event bus retry visibility (Day 6)
- Drift detection diagnostic lines (Day 13)
- Migration recovery logs (Days 12, 15)
Changing to DEBUG in prod only during incident windows.

---

## 14. Microservice Migration Impact (Days 19–20)

Extraction of prediction / anomaly services will:
- Introduce per-service configuration subsets (shared core via env prefix or dedicated Settings modules).
- Require consistent API_KEY & Redis / MLflow settings across services (pass through deployment orchestrator).

Plan ahead: keep naming stable to allow sidecar reuse.

---

## 15. Troubleshooting Matrix

Symptom | Check | Likely Setting Issue
--------|-------|----------------------
403 everywhere | API key header mismatch | API_KEY incorrect / unset
Prediction model not found | Path fallback used | MODEL_REGISTRY_PATH stale or MLflow volume missing
Duplicate ingestion accepted | Redis warnings in logs | REDIS_URL unset / unreachable
Event retries exhausted rapidly | Short delays | EVENT_HANDLER_RETRY_DELAY_SECONDS too low
Unexpected auto approvals | Maintenance predictions frequent | ORCHESTRATOR_* thresholds mis-tuned
High log noise | Excess debug lines | LOG_LEVEL accidentally DEBUG
Drift endpoint slow | Large unindexed scans? | Database URL pointing to wrong instance (missing index migration)

---

## 16. Minimal Code Surface (Excerpt)

```python
# settings.py excerpt (illustrative)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    api_key: str
    secret_key: str
    event_handler_max_retries: int = 3
    dlq_enabled: bool = True
    log_level: str = "INFO"
    # ...additional fields...

settings = Settings()
def get_settings() -> Settings:
    return settings
```

---

## 17. Change Log Mapping (Selected)

Feature / Setting | Changelog Day
------------------|--------------
Idempotency (Redis fallback) | Day 4 / Day 15
Event retries & DLQ toggles | Day 6 / Day 12
Structured logging level | Day 6
MLflow persistence path assurance | Days 9–13.5 hardening
Composite index & DB perf | Day 12 + Day 18
Drift endpoint dependency (DB + Redis) | Day 13
Model hash validation (CI context) | Day 21
Microservice scaffolding alignment | Days 19–20
Drift/retrain automation | Day 23

---

## 18. Future (Planned Config Keys — Not Yet Implemented)

| Planned | Purpose |
|---------|---------|
| DRIFT_WINDOW_MINUTES | Standardized drift window tuning |
| MODEL_RETRAIN_COOLDOWN_HOURS | Guardrail for retrain frequency |
| RATE_LIMIT_REDIS_URL | Shared distributed rate limiting backend |
| SIGNED_MODEL_MANIFESTS_ENABLED | Supply chain integrity |

(Do not predefine until code integration committed.)

---

## 19. Summary

Configuration surface is lean, explicit, and aligned with resilience, ML lifecycle automation, and observability goals. Expansion follows documented checklist to prevent drift or hidden coupling.

---
1. Adicione a configuração à classe `Settings` em `settings.py`
2. Adicione um valor padrão
3. Atualize o arquivo `.env.example`
4. Use a configuração em sua aplicação via `settings.sua_nova_configuracao`
