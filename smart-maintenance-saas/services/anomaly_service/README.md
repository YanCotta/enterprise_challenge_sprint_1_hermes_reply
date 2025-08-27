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