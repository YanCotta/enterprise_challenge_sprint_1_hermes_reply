# Test Coverage Improvement Plan

## Current Status
- **Current Coverage**: 22.83%
- **CI Requirement**: 20% (temporarily lowered from 80% for active development)
- **Target Goal**: 80% (long-term production readiness)
- **Last Updated**: August 31, 2025

# Smart Maintenance SaaS - Complete Documentation Index

## Core Documentation

### Getting Started

- **[Main README](../../README.md)** - Project overview, quick start, and repository structure
- **[Backend README](../README.md)** - Docker deployment and getting started guide
- **[Development Orientation](../../DEVELOPMENT_ORIENTATION.md)** - Development guidelines and best practices

### Project History & Changelog

- **[30-Day Sprint Changelog](../../30-day-sprint-changelog.md)** - Complete development history and daily progress
- **[Final Sprint Summary](../../final_30_day_sprint.md)** - Executive summary of sprint achievements

## System Architecture & Design

### Architecture Documentation

- **[System and Architecture](./SYSTEM_AND_ARCHITECTURE.md)** - Comprehensive system architecture and design patterns
- **[System Screenshots](./SYSTEM_SCREENSHOTS.md)** - Visual documentation of system interfaces
- **[Comprehensive System Analysis](./COMPREHENSIVE_SYSTEM_ANALYSIS_REPORT.md)** - Detailed technical analysis report
- **[Microservice Migration Strategy](./MICROSERVICE_MIGRATION_STRATEGY.md)** - Future architecture evolution plans

### Database Design

- **[Database Documentation](./db/README.md)** - Database schema and design documentation
- **[Database ERD](./db/erd.dbml)** - Entity Relationship Diagram source
- **[Database Schema](./db/schema.sql)** - Complete SQL schema definition

## API & Integration

### API Documentation

- **[API Reference](./api.md)** - Complete REST API documentation and examples
- **[Configuration Management](../core/config/README.md)** - Centralized configuration system
- **[Logging Configuration](../core/logging_config.md)** - Structured JSON logging setup

## Performance & Testing

### Performance Documentation

- **[Performance Baseline](./PERFORMANCE_BASELINE.md)** - Performance metrics and SLO targets
- **[Day 17 Load Test Report](./DAY_17_LOAD_TEST_REPORT.md)** - Comprehensive load testing results (103.8 RPS)
- **[Day 18 Performance Results](./DAY_18_PERFORMANCE_RESULTS.md)** - TimescaleDB optimization results
- **[Load Testing Instructions](./LOAD_TESTING_INSTRUCTIONS.md)** - Guide for running performance tests

### Testing Documentation

- **[Test Documentation](../tests/README.md)** - Test organization and execution guide
- **[Coverage Improvement Plan](./COVERAGE_IMPROVEMENT_PLAN.md)** - Test coverage strategy and current status

## Machine Learning & Data Science

### ML Documentation

- **[ML Documentation](./ml/README.md)** - Machine learning models and pipelines
- **[Models Summary](./MODELS_SUMMARY.md)** - Overview of all 17+ production models
- **[Project Gauntlet Plan](./PROJECT_GAUNTLET_PLAN.md)** - Real-world dataset integration execution

## Security & Operations

### Security Documentation

- **[Security Documentation](./SECURITY.md)** - Security architecture and implementation
- **[Security Audit Checklist](./SECURITY_AUDIT_CHECKLIST.md)** - Comprehensive security audit framework

---

*This index is automatically maintained and appears at the top of all documentation files for easy navigation.*

---

## Coverage Analysis (from latest CI run)

### High Priority - Core Components (0% coverage)

These are critical system components that need immediate test coverage:

1. **API Layer** (0% coverage)
   - `apps/api/main.py` (90 statements) - FastAPI with Prometheus metrics, idempotency, correlation IDs
   - `apps/api/dependencies.py` (15 statements) - API key authentication, dependency injection
   - Need: FastAPI endpoint tests, authentication tests, rate limiting tests

2. **ML Components** (0% coverage)
   - `apps/ml/model_loader.py` (108 statements) - MLflow integration and model loading
   - `apps/ml/features.py` (48 statements) - Feature engineering with lag features
   - `apps/ml/statistical_models.py` (41 statements) - Prophet and LightGBM models
   - `apps/ml/model_utils.py` - MLflow registry interaction and model tagging
   - Need: Model loading tests, feature engineering tests, MLflow integration tests

3. **System Coordinator** (0% coverage)
   - `apps/system_coordinator.py` (88 statements) - Event bus coordination and retry logic
   - Need: System integration tests, event bus tests

4. **Data Export & Processing** (0% coverage)
   - `scripts/export_sensor_data_csv.py` - CSV export functionality
   - `data/processors/` - Data transformation pipelines
   - Need: Export tests, data processor validation tests



### Medium Priority - Agent System (0% coverage)

These components have extensive functionality but are less critical for immediate CI:

1. **Core Agents** (0% coverage)
   - `apps/agents/core/anomaly_detection_agent.py` (254 statements) - Statistical anomaly detection with Redis integration
   - `apps/agents/core/orchestrator_agent.py` (189 statements) - Agent coordination and workflow management
   - `apps/agents/core/data_acquisition_agent.py` (137 statements) - Sensor data collection and processing

2. **Decision Agents** (0% coverage)
   - `apps/agents/decision/scheduling_agent.py` (309 statements) - Maintenance scheduling logic
   - `apps/agents/decision/prediction_agent.py` (247 statements) - ML prediction coordination
   - `apps/agents/decision/reporting_agent.py` (147 statements) - Report generation and Slack notifications

3. **Drift Detection & Automation** (0% coverage)
   - `scripts/run_drift_check_agent.py` (230 lines) - APScheduler-based drift monitoring
   - `scripts/retrain_models_on_drift.py` (280 lines) - Event-driven model retraining
   - Need: Automated testing of drift detection, retraining workflows


### Well-Covered Components (>75% coverage)
These components have good test coverage and should be maintained:

1. **Event System** (77% coverage)
   - `core/events/event_bus.py` - Continue improving
   - `core/events/event_models.py` (100% coverage) ✅

2. **Database Models** (98-100% coverage)
   - `core/database/orm_models.py` (100% coverage) ✅
   - `data/schemas.py` (98% coverage) ✅
   - `core/config/settings.py` (98% coverage) ✅

3. **Data Validation** (79-81% coverage)
   - `data/validators/agent_data_validator.py` (79% coverage)
   - `data/exceptions.py` (81% coverage)

## Progressive Coverage Targets

### Phase 1: Immediate CI Stability (Target: 25%)

- **Timeline**: Current sprint
- **Focus**: Add basic tests for API endpoints and ML components
- **Action Items**:
  - [ ] Add tests for `/health`, `/api/v1/data/ingest` endpoints with correlation ID validation
  - [ ] Add basic model loader tests with MLflow integration
  - [ ] Add feature engineering tests (lag features, sensor data transformers)
  - [ ] Add idempotency key validation tests
  - [ ] Add rate limiting tests for protected endpoints
  - [ ] Add CSV export functionality tests

### Phase 2: Core System Coverage (Target: 40%)

- **Timeline**: Next 2 sprints
- **Focus**: System coordinator, database layer, and Redis integration
- **Action Items**:
  - [ ] Add system coordinator integration tests with event bus
  - [ ] Add TimescaleDB hypertable tests and database CRUD operations
  - [ ] Add Redis client tests with idempotency cache validation
  - [ ] Add Prometheus metrics collection tests
  - [ ] Add Toxiproxy resilience testing framework
  - [ ] Add ML pipeline integration tests (Prophet, LightGBM models)

### Phase 3: Agent System Coverage (Target: 60%)

- **Timeline**: Medium term (2-4 sprints)
- **Focus**: Core agents, decision logic, and automation systems
- **Action Items**:
  - [ ] Add anomaly detection agent tests with statistical validation
  - [ ] Add orchestrator agent tests with workflow management
  - [ ] Add validation agent tests (currently 49% - improve to 80%+)
  - [ ] Add drift detection automation tests (APScheduler, Redis events)
  - [ ] Add model retraining workflow tests
  - [ ] Add Slack notification integration tests

### Phase 4: Full System Coverage (Target: 80%)
- **Timeline**: Long term (4-8 sprints)
- **Focus**: Complete agent ecosystem
- **Action Items**:
  - [ ] Add all decision agent tests
  - [ ] Add learning agent tests
  - [ ] Add interface agent tests
  - [ ] Add integration test suites

## Coverage Thresholds Schedule

| Phase | Target Coverage | CI Threshold | Timeline |
|-------|----------------|--------------|----------|
| Current | 22.83% | 20% | ✅ Implemented |
| Phase 1 | 25% | 23% | Sprint +1 |
| Phase 2 | 40% | 35% | Sprint +3 |
| Phase 3 | 60% | 55% | Sprint +6 |
| Phase 4 | 80% | 75% | Sprint +10 |

## Implementation Strategy

1. **Prioritize by Impact**: Focus on components with highest statement counts first
2. **Test Real Functionality**: Write integration tests that verify actual system behavior
3. **Mock External Dependencies**: Use mocks for TimescaleDB, MLflow, Redis in unit tests
4. **Maintain Quality**: Ensure tests are meaningful, not just coverage-driven
5. **Continuous Integration**: Update CI thresholds progressively as coverage improves
6. **Infrastructure Testing**: Use Toxiproxy for resilience testing and failure simulation
7. **ML Model Validation**: Implement automated model hash validation for reproducibility
8. **Security Testing**: Include rate limiting, authentication, and input validation tests

## Current CI/CD Infrastructure

Based on Day 21 enhancements:
- **ML Model Validation**: Automated model hash verification via `scripts/validate_model_hashes.py`
- **Multi-Environment Testing**: PostgreSQL, Redis, and Toxiproxy services in CI pipeline
- **Security Scanning**: Integrated safety and bandit security checks
- **Coverage Reporting**: pytest with 80% minimum threshold (temporarily lowered to 20%)
- **Docker Validation**: End-to-end container testing
- **Performance Baseline**: Automated load testing with Locust on main branch

## Notes

- Coverage requirement temporarily lowered to ensure CI stability during active development
- Focus on testing critical path functionality first (API endpoints, data ingestion, ML pipeline)
- Agent system can have lower priority as it's more modular and less critical for core system operation
- ML model reproducibility enforced through automated hash validation in CI pipeline
- Security testing prioritized due to STRIDE threat model implementation
- Drift detection and automated retraining systems require comprehensive E2E test coverage