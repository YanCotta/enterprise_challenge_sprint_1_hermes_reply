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
- **[Database Schema](../../../docs/db/schema.sql)** - Complete SQL schema definition

## API & Integration

### API Documentation

- **[API Reference](../../../docs/api.md)** - Complete REST API documentation and examples
- **[Configuration Management](../../core/config/README.md)** - Centralized configuration system
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

---

*This index is automatically maintained and appears at the top of all documentation files for easy navigation.*

---

# Anomaly Service

## Overview

The Anomaly Service is a future microservice designed to handle anomaly detection and drift monitoring for the Smart Maintenance SaaS platform.

## Purpose

This service will be responsible for:

- **Statistical Drift Detection**: Comparing current vs historical sensor data patterns
- **Anomaly Threshold Management**: Managing and updating anomaly detection thresholds
- **Real-time Anomaly Scoring**: Processing sensor data for anomaly detection
- **Historical Pattern Analysis**: Analyzing trends and patterns in sensor behavior
- **Alert Generation**: Creating and routing anomaly alerts
- **Custom Model Training**: Training specialized anomaly detection models

## Current Status

**⚠️ PLACEHOLDER SERVICE ⚠️**

This service is currently a scaffolding placeholder created as part of the microservice migration strategy. It should **NOT** be deployed to production.

## Migration Trigger

This service should be activated when the following conditions from `MICROSERVICE_MIGRATION_STRATEGY.md` are met:

- High volume of drift detection requests impacting main API performance
- Need for specialized anomaly detection algorithms requiring dedicated resources
- Formation of dedicated data science team focused on anomaly detection
- Requirements for custom anomaly models with independent deployment lifecycle

## Future Implementation

When activated, this service will include:

- Integration with TimescaleDB for time-series analysis
- Statistical algorithms (Kolmogorov-Smirnov, Mann-Whitney U, etc.)
- Machine learning-based anomaly detection models
- Real-time stream processing capabilities
- Configurable alerting and notification systems
- Historical anomaly pattern analysis

## API Endpoints

### Current Placeholder Endpoints

- `GET /health` - Service health check
- `POST /check-drift` - Statistical drift detection (placeholder)
- `POST /detect-anomalies` - Real-time anomaly detection (placeholder)

### Future Planned Endpoints

- `GET /sensors/{sensor_id}/drift-status` - Current drift status
- `POST /sensors/{sensor_id}/thresholds` - Update anomaly thresholds
- `GET /anomalies/history` - Historical anomaly data
- `POST /models/train` - Train custom anomaly models
- `GET /algorithms` - Available anomaly detection algorithms
- `POST /alerts/configure` - Configure alert rules

## Development

### Local Development

```bash
# Build the container
docker build -t anomaly-service .

# Run locally
docker run -p 8002:8002 anomaly-service

# Test health endpoint
curl http://localhost:8002/health
```

### Integration with Main Application

This service is designed to integrate with the main Smart Maintenance SaaS application through:

- Shared TimescaleDB access for time-series data
- Event-driven architecture for real-time processing
- Consistent API patterns and error handling
- Standardized logging and monitoring

## Algorithms and Methods

Future implementation will support:

### Statistical Methods
- **Kolmogorov-Smirnov Test**: Distribution comparison for drift detection
- **Mann-Whitney U Test**: Non-parametric difference detection
- **Anderson-Darling Test**: Goodness-of-fit testing
- **CUSUM**: Cumulative sum control charts

### Machine Learning Methods
- **Isolation Forest**: Unsupervised anomaly detection
- **One-Class SVM**: Support vector machine for novelty detection
- **Local Outlier Factor**: Density-based anomaly detection
- **Autoencoders**: Neural network-based anomaly detection

## Security Considerations

- Input validation for all sensor data
- Rate limiting for anomaly detection requests
- Secure access to time-series database
- Audit logging for all anomaly detections
- Role-based access control for threshold management

## Performance Considerations

- Efficient time-series query optimization
- Caching of frequently accessed sensor patterns
- Batch processing for historical analysis
- Async processing for real-time detections
- Resource limits and circuit breakers