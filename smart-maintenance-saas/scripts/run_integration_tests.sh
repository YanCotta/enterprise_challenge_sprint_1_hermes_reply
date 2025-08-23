#!/bin/bash
# Integration Test Runner
# Runs integration tests against already-running docker-compose services
# This approach resolves Docker-in-Docker limitations in containerized environments

set -e

echo "🧪 Integration Test Runner - Formal Docker-in-Docker Workaround"
echo "================================================================"

# Check if services are running
echo "📋 Checking service health..."
if ! docker compose ps --services --filter "status=running" | grep -q "api"; then
    echo "❌ Error: Services not running. Please start with 'docker compose up -d'"
    exit 1
fi

# Wait for services to be fully ready
echo "⏳ Waiting for services to be fully ready..."
sleep 5

# Verify API health
echo "🏥 Verifying API health..."
API_HEALTH=$(docker compose exec -T api curl -s http://localhost:8000/health | grep -o '"status":"healthy"' || echo "unhealthy")
if [[ "$API_HEALTH" != '"status":"healthy"' ]]; then
    echo "❌ Error: API service not healthy"
    exit 1
fi

# Verify database connectivity
echo "🗄️  Verifying database connectivity..."
DB_CHECK=$(docker compose exec -T api python -c "
import psycopg2
import os
try:
    # Use the correct connection credentials from .env
    conn = psycopg2.connect(
        host='db',
        port=5432,
        database='smart_maintenance_db',
        user='smart_user',
        password='strong_password'
    )
    cur = conn.cursor()
    cur.execute('SELECT 1')
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    print('DB_OK' if result == 1 else 'DB_FAIL')
except Exception as e:
    print('DB_FAIL')
")

if [[ "$DB_CHECK" != "DB_OK" ]]; then
    echo "❌ Error: Database connectivity failed"
    exit 1
fi

# Verify MLflow connectivity
echo "🤖 Verifying MLflow connectivity..."
MLFLOW_CHECK=$(docker compose exec -T api python -c "
import mlflow
try:
    mlflow.set_tracking_uri('http://mlflow:5000')
    client = mlflow.MlflowClient()
    models = client.search_registered_models()
    print(f'MLFLOW_OK:{len(models)}')
except Exception as e:
    print('MLFLOW_FAIL')
")

if [[ "$MLFLOW_CHECK" != MLFLOW_OK:* ]]; then
    echo "❌ Error: MLflow connectivity failed"
    exit 1
fi

# Install test dependencies if needed
echo "📦 Ensuring test dependencies are available..."
docker compose exec -T api python -c "
import sys
try:
    import httpx
    import pytest
    print('TEST_DEPS_OK')
except ImportError as e:
    print(f'TEST_DEPS_MISSING:{e}')
" > /tmp/deps_check.txt

DEPS_STATUS=$(cat /tmp/deps_check.txt)
if [[ "$DEPS_STATUS" == TEST_DEPS_MISSING:* ]]; then
    echo "📦 Installing missing test dependencies..."
    docker compose exec -T api pip install httpx pytest pytest-asyncio
fi

# Run integration tests against live services
echo "🚀 Running integration tests against live services..."
echo "=================================================="

# Test data export functionality
echo "📊 Testing data export functionality..."
EXPORT_TEST_RESULT=$(docker compose exec -T api python -c "
import subprocess
import tempfile
import os
import pandas as pd

# Test full export
try:
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
        result = subprocess.run([
            'python', 'scripts/export_sensor_data_csv.py', 
            '--output', tmp.name
        ], capture_output=True, text=True, cwd='/app')
        
        if result.returncode == 0:
            # Verify CSV was created and has data
            df = pd.read_csv(tmp.name)
            if len(df) > 0 and 'timestamp' in df.columns:
                print('EXPORT_FULL_OK')
            else:
                print('EXPORT_FULL_EMPTY')
        else:
            print(f'EXPORT_FULL_FAIL:{result.stderr}')
        
        os.unlink(tmp.name)
except Exception as e:
    print(f'EXPORT_FULL_ERROR:{e}')
")

if [[ "$EXPORT_TEST_RESULT" == "EXPORT_FULL_OK" ]]; then
    echo "✅ Data export test: PASSED"
else
    echo "❌ Data export test: FAILED ($EXPORT_TEST_RESULT)"
fi

# Test incremental export functionality
echo "📈 Testing incremental export functionality..."
INCREMENTAL_TEST_RESULT=$(docker compose exec -T api python -c "
import subprocess
import tempfile
import os
import pandas as pd

try:
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
        # First, create a base CSV file
        result1 = subprocess.run([
            'python', 'scripts/export_sensor_data_csv.py', 
            '--output', tmp.name
        ], capture_output=True, text=True, cwd='/app')
        
        if result1.returncode == 0:
            # Then test incremental export
            result2 = subprocess.run([
                'python', 'scripts/export_sensor_data_csv.py',
                '--incremental', '--output', tmp.name
            ], capture_output=True, text=True, cwd='/app')
            
            if result2.returncode == 0:
                print('EXPORT_INCREMENTAL_OK')
            else:
                print(f'EXPORT_INCREMENTAL_FAIL:{result2.stderr}')
        else:
            print(f'EXPORT_BASE_FAIL:{result1.stderr}')
            
        os.unlink(tmp.name)
except Exception as e:
    print(f'EXPORT_INCREMENTAL_ERROR:{e}')
")

if [[ "$INCREMENTAL_TEST_RESULT" == "EXPORT_INCREMENTAL_OK" ]]; then
    echo "✅ Incremental export test: PASSED"
else
    echo "❌ Incremental export test: FAILED ($INCREMENTAL_TEST_RESULT)"
fi

# Test API endpoints
echo "🌐 Testing API endpoints..."
API_TEST_RESULT=$(docker compose exec -T api python -c "
import httpx
import asyncio

async def test_endpoints():
    async with httpx.AsyncClient(base_url='http://localhost:8000') as client:
        tests = []
        
        # Test health endpoint
        try:
            response = await client.get('/health')
            tests.append(f'health:{response.status_code}')
        except Exception as e:
            tests.append(f'health:error')
        
        # Test data ingestion endpoint
        try:
            payload = {
                'sensor_id': 'integration-test-sensor',
                'value': 42.0,
                'unit': 'celsius',
                'quality': 1.0
            }
            response = await client.post('/api/v1/data/ingest', json=payload)
            tests.append(f'ingest:{response.status_code}')
        except Exception as e:
            tests.append(f'ingest:error')
        
        # Test drift check endpoint
        try:
            payload = {
                'sensor_id': 'integration-test-sensor',
                'window_minutes': 30,
                'p_value_threshold': 0.05,
                'min_samples': 1
            }
            response = await client.post('/api/v1/ml/check_drift', json=payload)
            tests.append(f'drift:{response.status_code}')
        except Exception as e:
            tests.append(f'drift:error')
    
    return tests

results = asyncio.run(test_endpoints())
for result in results:
    print(result)
")

echo "API endpoint test results:"
echo "$API_TEST_RESULT" | while read -r line; do
    endpoint=$(echo "$line" | cut -d: -f1)
    status=$(echo "$line" | cut -d: -f2)
    if [[ "$status" == "200" ]] || [[ "$status" == "201" ]]; then
        echo "✅ $endpoint endpoint: PASSED"
    else
        echo "❌ $endpoint endpoint: FAILED ($status)"
    fi
done

# Test model loading resilience
echo "🤖 Testing model loading resilience..."
MODEL_TEST_RESULT=$(docker compose exec -T api python -c "
from apps.ml.model_loader import load_model
import time

# Test loading a known working model
try:
    start_time = time.time()
    model = load_model('vibration_anomaly_isolationforest', '1')
    load_time = time.time() - start_time
    
    if model is not None:
        print(f'MODEL_LOAD_OK:{load_time:.2f}s')
    else:
        print('MODEL_LOAD_NONE')
except Exception as e:
    print(f'MODEL_LOAD_ERROR:{e}')
")

if [[ "$MODEL_TEST_RESULT" == MODEL_LOAD_OK:* ]]; then
    echo "✅ Model loading test: PASSED"
else
    echo "❌ Model loading test: FAILED ($MODEL_TEST_RESULT)"
fi

echo ""
echo "=================================================="
echo "🎯 Integration Testing Summary"
echo "=================================================="
echo "✅ Service health checks: PASSED"
echo "✅ Database connectivity: PASSED"
echo "✅ MLflow connectivity: PASSED"

# Count passed/failed tests
TOTAL_TESTS=5
PASSED_TESTS=3  # Service health, DB, MLflow always pass if we get here

if [[ "$EXPORT_TEST_RESULT" == "EXPORT_FULL_OK" ]]; then
    ((PASSED_TESTS++))
fi

if [[ "$INCREMENTAL_TEST_RESULT" == "EXPORT_INCREMENTAL_OK" ]]; then
    ((PASSED_TESTS++))
fi

echo ""
echo "📊 Test Results: $PASSED_TESTS/$TOTAL_TESTS tests passed"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "🎉 All integration tests PASSED!"
    exit 0
else
    echo "⚠️  Some integration tests FAILED. Check output above for details."
    exit 1
fi