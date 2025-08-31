# Database Architecture Documentation

This document describes the production database architecture for Smart Maintenance SaaS, detailing our strategic design decisions, performance optimizations, and operational features.

## Overview

Our database architecture leverages **TimescaleDB** for time-series data with PostgreSQL for relational integrity, designed specifically for industrial IoT sensor data ingestion and analysis at scale.

**Key Architectural Decisions (as of 2025-08-25)**:
- **TimescaleDB Hypertables**: Optimized for high-volume time-series sensor data
- **Composite Indexing Strategy**: Strategic indexing for ML query patterns
- **Continuous Aggregates (CAGG)**: Pre-computed aggregations for dashboard performance
- **Automated Data Lifecycle**: Compression and retention policies for storage efficiency

# Database Architecture Documentation

This document describes the production database architecture for Smart Maintenance SaaS, detailing our strategic design decisions, performance optimizations, and operational features.

## System Overview

Our database architecture leverages **TimescaleDB** for time-series data with PostgreSQL for relational integrity, designed specifically for industrial IoT sensor data ingestion and analysis at scale.

**Key Architectural Decisions (as of 2025-08-25)**:

- **TimescaleDB Hypertables**: Optimized for high-volume time-series sensor data
- **Composite Indexing Strategy**: Strategic indexing for ML query patterns
- **Continuous Aggregates (CAGG)**: Pre-computed aggregations for dashboard performance
- **Automated Data Lifecycle**: Compression and retention policies for storage efficiency

## Schema Overview

### Core Tables

#### sensors (Asset Registry)

- `id` (uuid, PK, default gen_random_uuid())
- `sensor_id` (varchar(255), unique, not null) — business identifier
- `type` (varchar(50), not null) — sensor type (temperature, vibration, pressure, etc.)
- `location` (varchar(255))
- `status` (enum sensor_status, default 'active')
- `created_at`, `updated_at` (timestamptz, defaults)

**Purpose**: Central registry for all sensor assets with lifecycle management.

#### sensor_readings (TimescaleDB Hypertable)

- `id` (integer, PK, auto-generated sequence)
- `timestamp` (timestamptz, not null) — measurement timestamp
- `sensor_id` (varchar(255), not null) — FK to sensors.sensor_id
- `value` (float8, not null) — sensor measurement value
- `unit` (varchar(50)) — measurement unit
- `quality` (float8) — data quality score (0.0-1.0)

**Purpose**: High-volume time-series data storage with TimescaleDB optimization.

### Supporting Tables

#### maintenance_logs

- Complete maintenance activity history
- Links to sensor assets and maintenance tasks
- Immutable log for audit and analysis

#### anomaly_alerts

- ML-generated anomaly detection events
- Severity classification and status tracking
- Evidence storage for investigation

## TimescaleDB Integration

### Hypertable Configuration

The `sensor_readings` table is configured as a **TimescaleDB hypertable** to handle high-volume time-series data efficiently:

- **Partitioning**: Automatic time-based partitioning for query performance
- **Compression**: Automatic compression of older data chunks
- **Parallel Processing**: Distributed query execution across partitions

### Benefits of TimescaleDB

- **Insert Performance**: Optimized for high-volume concurrent sensor data ingestion
- **Query Performance**: Time-based partitioning accelerates temporal queries
- **Storage Efficiency**: Built-in compression reduces storage footprint by 90%+
- **Scalability**: Horizontal scaling capabilities for enterprise deployments

## Performance Optimization Rationale

### Composite Index Strategy

**Primary Index: `(sensor_id, timestamp DESC)`**

This composite index was strategically designed to accelerate the most common ML query pattern:

```sql
-- Optimized query pattern for ML feature engineering
SELECT value, timestamp 
FROM sensor_readings 
WHERE sensor_id = 'sensor-001' 
ORDER BY timestamp DESC 
LIMIT 1000;
```

**Performance Impact**:

- **Query Type**: Single-sensor time-series data retrieval
- **Use Cases**: ML model inference, drift detection, anomaly analysis
- **Optimization**: Index covers both filter condition and sort operation
- **Result**: Sub-millisecond query execution for ML workloads

### Continuous Aggregates (CAGG)

**Implementation**: `sensor_readings_summary_hourly`

Pre-computed hourly aggregations dramatically improve dashboard and analytics performance:

```sql
-- CAGG automatically maintains these aggregations:
SELECT 
    sensor_id,
    time_bucket('1 hour', timestamp) as hour,
    avg(value) as avg_value,
    min(value) as min_value,
    max(value) as max_value,
    count(*) as reading_count
FROM sensor_readings
GROUP BY sensor_id, hour;
```

**Performance Gains Achieved**:

- **Baseline Query Time**: ~2.4 seconds (full table scan)
- **CAGG Query Time**: ~1.5 seconds (pre-computed aggregates)
- **Performance Improvement**: **37.3% reduction** in query execution time
- **Dashboard Impact**: Real-time analytics without performance degradation

### Data Lifecycle Policies

#### Automated Compression

**Policy**: Compress data chunks older than 7 days

- **Storage Savings**: 90%+ compression ratio typical for sensor data
- **Query Performance**: Transparent decompression during queries
- **Cost Optimization**: Dramatic reduction in storage costs for historical data

**Implementation**:

```sql
SELECT add_compression_policy('sensor_readings', INTERVAL '7 days');
```

#### Automated Retention

**Policy**: Retain data for 180 days, automatically drop older chunks

- **Compliance**: Configurable retention for regulatory requirements
- **Storage Management**: Automatic cleanup prevents unlimited storage growth
- **Performance**: Eliminates need for manual data purging operations

**Implementation**:

```sql
SELECT add_retention_policy('sensor_readings', INTERVAL '180 days');
```

## Indexing Strategy

### Primary Indexes

1. **Composite Index**: `(sensor_id, timestamp DESC)`
   - **Purpose**: ML query optimization
   - **Coverage**: Single-sensor time-series analysis
   - **Performance**: Optimizes ORDER BY timestamp DESC operations

2. **Foreign Key Indexes**: Automatic indexing on all FK relationships
   - **sensor_readings.sensor_id** → sensors.sensor_id
   - **maintenance_logs.task_id** → maintenance_tasks.id
   - **anomaly_alerts.sensor_id** → sensors.sensor_id

### Query Optimization Examples

**Efficient ML Feature Extraction**:

```sql
-- Optimized by composite index
SELECT value, timestamp, quality
FROM sensor_readings 
WHERE sensor_id = ? 
  AND timestamp >= NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;
```

**Dashboard Aggregations**:

```sql
-- Optimized by CAGG
SELECT hour, avg_value, max_value 
FROM sensor_readings_summary_hourly 
WHERE sensor_id = ? 
  AND hour >= NOW() - INTERVAL '24 hours';
```

## Database Schema Files

### Current Schema Documentation

- **ERD Source**: `docs/db/erd.dbml` - Authoritative schema definition
- **ERD Visualization**: `docs/db/erd.png` - Generated entity-relationship diagram
- **SQL Schema**: `docs/db/schema.sql` - Complete PostgreSQL/TimescaleDB schema
- **Migration History**: `alembic_migrations/versions/` - Complete migration chain

### Schema Generation Commands

**Export Current Schema**:

```bash
./scripts/export_schema.sh
```

**Generate Updated ERD**:

```bash
./scripts/generate_erd.sh
```

## Operational Considerations

### Performance Monitoring

**Key Metrics to Monitor**:

- TimescaleDB chunk compression ratios
- Query execution times for common ML patterns
- CAGG refresh performance and lag
- Storage growth rates and retention policy effectiveness

### Maintenance Operations

**Regular Maintenance**:

- Monitor compression policy effectiveness
- Validate CAGG refresh schedules
- Review retention policy compliance
- Analyze query performance patterns

**Scaling Considerations**:

- Hypertable chunk sizing optimization
- CAGG refresh interval tuning
- Index usage analysis and optimization
- Connection pooling for high-concurrency workloads

## Integration with Application Stack

### FastAPI Integration

- **Connection Pooling**: SQLAlchemy async connection management
- **Migration Management**: Alembic migration chain for schema evolution
- **ORM Models**: Type-safe database operations with Pydantic validation

### MLOps Integration

- **Feature Engineering**: Optimized queries for ML model training
- **Real-time Inference**: Fast single-sensor data retrieval for predictions
- **Drift Detection**: Efficient time-windowed statistical comparisons
- **Model Training**: Bulk data export capabilities for offline training

### Analytics & Dashboards

- **Streamlit Integration**: Real-time dashboard performance via CAGG
- **Time-series Visualization**: Native TimescaleDB time-bucket functions
- **Historical Analysis**: Compressed data access for long-term trend analysis

## Future Enhancements

### Scalability Roadmap

- **Distributed TimescaleDB**: Multi-node deployment for extreme scale
- **Read Replicas**: Dedicated analytics instances for heavy query workloads
- **Advanced Compression**: Custom compression algorithms for sensor data patterns

### Advanced Features

- **Real-time Alerts**: Database triggers for immediate anomaly notification
- **Automated Rebalancing**: Dynamic chunk management based on query patterns
- **Advanced Analytics**: Built-in statistical functions and machine learning extensions

---

**Schema Evolution**: This architecture supports continuous evolution through Alembic migrations while maintaining TimescaleDB performance optimizations and ensuring zero-downtime deployments for production industrial IoT workloads.
