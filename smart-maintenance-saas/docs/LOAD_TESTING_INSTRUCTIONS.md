# Load Testing Instructions for Smart Maintenance SaaS

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
- **[Unified System Documentation](./UNIFIED_SYSTEM_DOCUMENTATION.md)** - Comprehensive system state and analysis
- **[Microservice Migration Strategy](./MICROSERVICE_MIGRATION_STRATEGY.md)** - Future architecture evolution plans

### Database Design

- **[Database Documentation](./db/README.md)** - Database schema and design documentation
- **[Database ERD](./db/erd.dbml)** - Entity Relationship Diagram source
- **[Database Schema](./db/schema.sql)** - Complete SQL schema definition

## API & Integration

### API Documentation

- **[API Reference](./api.md)** - Complete REST API documentation and examples

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

## Overview

This document provides comprehensive instructions for running load tests against the Smart Maintenance SaaS API using Locust. The system has been extensively tested and validated through Day 17 comprehensive load testing.

**Last Updated**: August 31, 2025  
**Performance Baseline**: Day 17 load testing achieved 103.8 RPS peak with sub-3ms response times

## Quick Start with Docker

1. **Start the Complete System**:

   ```bash
   cd smart-maintenance-saas
   docker compose up -d
   ```

2. **Verify System Health**:

   ```bash
   curl http://localhost:8000/health
   # Expected: {"status":"healthy"}
   ```

3. **Run Load Tests**:

   ```bash
   # Option 1: Simple API load test (recommended)
   docker compose exec api locust -f locustfile_simple.py --host=http://localhost:8000 --users 10 --run-time 1m --headless
   
   # Option 2: Full MLflow integration test
   docker compose exec api locust -f locustfile.py --host=http://localhost:8000 --users 5 --run-time 30s --headless
   ```

## Available Load Test Scripts

Based on Day 17 load testing validation, the system provides two load test configurations:

### locustfile_simple.py (Recommended)
- **Purpose**: Core API endpoint testing for SLO compliance
- **Endpoints**: `/health`, `/api/v1/data/ingest`, health checks  
- **Authentication**: Configured for containerized execution
- **Best For**: Performance baseline validation, CI/CD pipeline integration

### locustfile.py (Advanced)
- **Purpose**: Full MLflow Registry integration testing
- **Endpoints**: MLflow model registry, dynamic model discovery
- **Authentication**: MLflow client with version management
- **Best For**: ML pipeline stress testing, model registry load validation

## Load Test Configuration

The load testing suite includes two specialized scripts based on Day 17 comprehensive testing:

### APILoadTestUser (locustfile_simple.py)

- **Purpose**: Core API endpoint validation for SLO compliance
- **Active Endpoints**: `/health`, `/health/db`, `/health/redis`, `/health/detailed`, `/api/v1/data/ingest`
- **Authentication**: Containerized execution with proper networking
- **Wait Time**: 0.5-2.0 seconds between requests for sustained load
- **Active Tasks**:
  - `test_health_checks` (Weight: 30) - System health monitoring 
  - `test_data_ingestion` (Weight: 20) - Event bus throughput testing
  - `test_drift_detection` (Weight: 15) - ML endpoint validation
- **Data Generated**: Realistic sensor readings (temperature, pressure, vibration, humidity)

### MLflowUser (locustfile.py)

- **Purpose**: MLflow Registry stress testing and model loading validation
- **Active Endpoints**: MLflow Registry API, dynamic model discovery
- **Authentication**: MLflow client with automatic version management
- **Features**:
  - Dynamic model discovery to prevent version mismatches
  - Model loading performance testing
  - Registry throughput validation
- **Best For**: ML pipeline load testing, model registry scalability assessment

**Performance Baseline (Day 17 Results)**:
- **Peak Throughput**: 103.8 RPS (4x improvement over baseline)
- **Response Times**: P50=1ms, P95=2ms, P99=3ms
- **Infrastructure Utilization**: <6% CPU across all containers
- **Reliability**: 100% success rate on properly configured endpoints

## Running Load Tests

### Containerized Load Testing (Recommended)

Based on Day 17 validation, all load tests should be executed within the API container for consistent networking:

```bash
# Simple API load test (validated approach)
docker compose exec api locust -f locustfile_simple.py --host http://localhost:8000 --users 10 --run-time 1m --headless --print-stats

# MLflow registry load test
docker compose exec api locust -f locustfile.py --host http://mlflow:5000 --users 5 --run-time 30s --headless --print-stats
```

### Web UI Load Testing

```bash
# Start interactive load test
docker compose exec api locust -f locustfile_simple.py --host http://localhost:8000
```

Then open <http://localhost:8089> in your browser to configure and start the test.

### Command Line Load Test (Headless)

```bash
# Light load test (10 users, 2 spawn rate, 60 seconds) - Day 14 baseline
docker compose exec api locust -f locustfile_simple.py --host http://localhost:8000 --users 10 --spawn-rate 2 --run-time 60s --headless

# Medium load test (25 users, 5 spawn rate, 3 minutes) - Day 17 equivalent
docker compose exec api locust -f locustfile_simple.py --host http://localhost:8000 --users 25 --spawn-rate 5 --run-time 3m --headless

# Heavy load test (50 users, 10 spawn rate, 3 minutes) - Day 17 validated configuration
docker compose exec api locust -f locustfile_simple.py --host http://localhost:8000 --users 50 --spawn-rate 10 --run-time 3m --headless
```

### Load Test with HTML Report

```bash
docker compose exec api locust -f locustfile_simple.py --host http://localhost:8000 --users 25 --spawn-rate 5 --run-time 3m --headless --html load_test_report.html
```

## Test Scenarios

### Scenario 1: Normal Operations Load

- **Users**: 25 (primarily sensor data ingestion)
- **Duration**: 5 minutes
- **Purpose**: Test normal operational load for sensor data processing

```bash
poetry run locust -f locustfile.py --host=http://localhost:8000 --users 25 --spawn-rate 3 --run-time 5m --headless --html normal_load_report.html
```

### Scenario 2: Peak Load Testing

- **Users**: 100 (high-frequency sensor data ingestion)
- **Duration**: 10 minutes
- **Purpose**: Test system under peak sensor data load conditions

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

Based on Day 17 comprehensive load testing validation:

### Validated Performance Baseline (50 Users, 3 Minutes)

- **Peak Throughput**: 103.8 RPS (4x improvement over initial baseline)
- **Average Throughput**: 88.83 RPS sustained
- **Response Time Performance**: 
  - **P50 (Median)**: 1ms
  - **P95**: 2ms (100x better than 200ms SLO)
  - **P99**: 3ms (67x better than 200ms SLO)
  - **Maximum**: 124ms (well below 200ms SLO)
- **Infrastructure Utilization**:
  - **API Container**: 0.07% CPU, 263.6 MiB memory
  - **Database**: 2.43% CPU, 758.4 MiB memory
  - **Redis**: 5.61% CPU, 14.37 MiB memory
- **Reliability**: 100% infrastructure stability, container health maintained

### Load Test Scenarios (Validated Configurations)

#### Scenario 1: Normal Operations (Day 14 Baseline)

- **Users**: 10 (sensor data ingestion focus)
- **Duration**: 1 minute
- **Expected Results**:
  - **Throughput**: ~25 RPS
  - **P95 Response Time**: <20ms
  - **Error Rate**: <1%

#### Scenario 2: Production Load (Day 17 Validated)

- **Users**: 25-50 (mixed API and high-volume users)
- **Duration**: 3 minutes
- **Expected Results**:
  - **Throughput**: 80-100+ RPS sustained
  - **P95 Response Time**: <5ms
  - **Error Rate**: <2% (primarily configuration-related, not performance)

#### Scenario 3: Stress Testing (Beyond Current Validation)

- **Users**: 100+ (stress testing capacity)
- **Duration**: 5-10 minutes
- **Expected Results**: Based on infrastructure headroom (95%+ CPU capacity remaining):
  - **Estimated Throughput**: 200+ RPS potential
  - **Response Time**: Should maintain <50ms P95
  - **Infrastructure**: System designed for much higher loads

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

This load testing setup provides comprehensive coverage of the Smart Maintenance SaaS API with validated performance characteristics. Based on Day 17 comprehensive testing, the system demonstrates exceptional performance capabilities far exceeding SLO requirements.

**Key Benefits**:

- **Validated Performance**: 103.8 RPS peak throughput with sub-3ms response times
- **Production Ready**: Extensive infrastructure headroom (95%+ capacity remaining)  
- **Comprehensive Coverage**: Full API surface testing including health endpoints, data ingestion, and ML pipeline
- **Containerized Execution**: Consistent networking and dependency management
- **CI/CD Integration**: Automated performance baseline validation in CI pipeline
- **Multiple Test Scenarios**: From baseline (10 users) to stress testing (50+ users)

**Performance Highlights (Day 17 Validation)**:
- **4x Throughput Improvement**: From 25 RPS baseline to 104 RPS peak
- **10x Latency Improvement**: P95 response time from 20ms to 2ms
- **Infrastructure Stability**: 100% container health under sustained load
- **Scalability Headroom**: System capable of much higher loads based on resource utilization

**Recommended Usage**:
- **Development**: Use `locustfile_simple.py` for API endpoint validation
- **CI/CD**: Automated baseline testing with 10-25 users for 1-3 minutes
- **Production Planning**: Reference Day 17 results for capacity planning and SLO validation
- **Stress Testing**: Validated configurations up to 50 users with room for expansion