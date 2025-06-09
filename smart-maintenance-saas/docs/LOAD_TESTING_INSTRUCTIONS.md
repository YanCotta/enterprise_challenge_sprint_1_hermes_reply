# Load Testing Instructions for Smart Maintenance SaaS

## Overview
This document provides comprehensive instructions for running load tests against the Smart Maintenance SaaS API using Locust.

## Prerequisites

1. **Install Dependencies**: Ensure Locust is installed in your environment:
   ```bash
   cd smart-maintenance-saas
   poetry install  # Locust should already be installed
   ```

2. **Start the API Server**: The API must be running before starting load tests:
   ```bash
   poetry run uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Database Setup**: Ensure PostgreSQL is running and tables are migrated:
   ```bash
   poetry run alembic upgrade head
   ```

## Load Test Configuration

The `locustfile.py` defines two main user behaviors:

### 1. SensorIngestionUser (Weight: 3)
- **Purpose**: Simulates high-frequency IoT sensor data ingestion
- **Endpoints**: `/api/v1/data/ingest`
- **Tasks**:
  - `ingest_normal_sensor_data` (Weight: 10) - Normal sensor readings
  - `ingest_anomalous_sensor_data` (Weight: 2) - Anomalous readings for detection testing
- **Wait Time**: 0.5-2.0 seconds between requests
- **Data Generated**: Temperature, vibration, and pressure sensor readings with realistic values

### 2. ReportRequestUser (Weight: 1)
- **Purpose**: Simulates report generation requests from maintenance managers
- **Endpoints**: `/api/v1/reports/generate`
- **Tasks**:
  - `request_anomaly_summary` (Weight: 5)
  - `request_system_health_report` (Weight: 3)
  - `request_maintenance_overview` (Weight: 2)
  - `request_custom_report` (Weight: 1)
- **Wait Time**: 5.0-15.0 seconds between requests

## Running Load Tests

### Basic Load Test
```bash
cd smart-maintenance-saas
poetry run locust -f locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089 in your browser to configure and start the test.

### Command Line Load Test (Headless)
```bash
# Light load test (10 users, 2 spawn rate, 60 seconds)
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 10 --spawn-rate 2 --run-time 60s --headless

# Medium load test (50 users, 5 spawn rate, 5 minutes)
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 5m --headless

# Heavy load test (100 users, 10 spawn rate, 10 minutes)
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 10m --headless
```

### Load Test with HTML Report
```bash
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 5m --headless --html load_test_report.html
```

## Test Scenarios

### Scenario 1: Normal Operations Load
- **Users**: 25 (19 sensor users, 6 report users)
- **Duration**: 5 minutes
- **Purpose**: Test normal operational load

```bash
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 25 --spawn-rate 3 --run-time 5m --headless --html normal_load_report.html
```

### Scenario 2: Peak Load Testing
- **Users**: 100 (75 sensor users, 25 report users)
- **Duration**: 10 minutes
- **Purpose**: Test system under peak load conditions

```bash
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 10m --headless --html peak_load_report.html
```

### Scenario 3: Spike Testing
- **Users**: Gradually increase from 10 to 200
- **Duration**: 15 minutes
- **Purpose**: Test system behavior under sudden load spikes

```bash
# Run step load test manually through web UI or use custom step load script
poetry run locust -f locustfile.py --host=http://localhost:8000
# Configure in web UI: Start with 10 users, then increase to 50, 100, 150, 200 every 3 minutes
```

### Scenario 4: Endurance Testing
- **Users**: 30 (moderate consistent load)
- **Duration**: 30 minutes
- **Purpose**: Test system stability over extended periods

```bash
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 30 --spawn-rate 2 --run-time 30m --headless --html endurance_test_report.html
```

## Performance Metrics to Monitor

### Application Metrics
- **Response Time**: 
  - 95th percentile < 500ms for data ingestion
  - 95th percentile < 2s for report generation
- **Throughput**: Requests per second
- **Error Rate**: Should be < 1% under normal load
- **Success Rate**: Should be > 99% under normal load

### System Metrics (Monitor with `htop`, `iostat`, etc.)
- **CPU Usage**: Should not exceed 80% sustained
- **Memory Usage**: Monitor for memory leaks
- **Database Connections**: Monitor PostgreSQL connection pool
- **Disk I/O**: Database write performance

### Database Metrics
- **Connection Pool**: Monitor active/idle connections
- **Query Performance**: Slow query logs
- **Lock Contention**: Monitor database locks
- **Storage Growth**: Monitor data ingestion impact

## Expected Results

### Normal Load (25 users)
- **Sensor Ingestion**: ~60-120 requests/minute
- **Report Generation**: ~10-20 requests/minute
- **Average Response Time**: < 200ms for ingestion, < 1s for reports
- **Error Rate**: < 0.5%

### Peak Load (100 users)
- **Sensor Ingestion**: ~300-600 requests/minute
- **Report Generation**: ~50-100 requests/minute
- **Average Response Time**: < 500ms for ingestion, < 2s for reports
- **Error Rate**: < 2%

### Breaking Point Identification
Run increasing load tests to identify:
- **Maximum Throughput**: Requests/second before performance degrades
- **Response Time Degradation Point**: When 95th percentile > acceptable limits
- **Error Rate Threshold**: When error rate > 5%
- **Resource Exhaustion**: CPU, memory, or database connection limits

## Troubleshooting Common Issues

### High Error Rates
1. Check API server logs: `docker logs <container_name>` or application logs
2. Verify database connectivity and performance
3. Check for authentication/authorization issues (API key)
4. Monitor resource usage (CPU, memory, disk)

### Poor Performance
1. Check database query performance with EXPLAIN ANALYZE
2. Monitor database connection pool utilization
3. Review application logging level (reduce in production)
4. Check for database locks or long-running transactions

### Test Setup Issues
1. Ensure API server is running and accessible
2. Verify database migrations are up to date
3. Check API key configuration in both server and test script
4. Confirm network connectivity between test client and server

## Post-Test Analysis

### Report Analysis
1. **Response Time Distribution**: Look for outliers and p95/p99 values
2. **Failure Analysis**: Categorize and investigate failed requests
3. **Throughput Trends**: Identify throughput degradation points
4. **Resource Correlation**: Compare performance metrics with system resource usage

### Optimization Recommendations
Based on test results, consider:
1. **Database Indexing**: Add indexes for frequently queried columns
2. **Connection Pooling**: Tune database connection pool settings
3. **Caching**: Implement caching for frequently accessed data
4. **Rate Limiting**: Add rate limiting to prevent abuse
5. **Horizontal Scaling**: Consider load balancing and multiple instances

## Load Test Automation

For CI/CD integration, create automated performance tests:

```bash
#!/bin/bash
# performance_test.sh

echo "Starting performance regression test..."

# Run light load test
poetry run locust -f locustfile.py --host=http://localhost:8000 \
  --users 20 --spawn-rate 2 --run-time 2m --headless \
  --html performance_regression_report.html

# Check exit code and parse results for performance regression
if [ $? -eq 0 ]; then
    echo "Performance test passed"
    exit 0
else
    echo "Performance test failed"
    exit 1
fi
```

## Summary

This load testing setup provides comprehensive coverage of the Smart Maintenance SaaS API under various load conditions. Regular execution of these tests will help identify performance bottlenecks, ensure system stability, and guide scaling decisions.

Key Benefits:
- **Realistic Load Simulation**: Mimics actual IoT sensor ingestion and reporting patterns
- **Scalable Test Scenarios**: From normal operations to stress testing
- **Comprehensive Metrics**: Response times, throughput, error rates
- **Automated Reporting**: HTML reports for analysis and documentation
- **CI/CD Ready**: Can be integrated into deployment pipelines
