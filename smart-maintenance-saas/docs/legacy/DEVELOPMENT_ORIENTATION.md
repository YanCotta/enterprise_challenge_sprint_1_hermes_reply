# Development Orientation Guide (V1.0 Production Complete)

## 🎉 V1.0 Production Completion Achievements

### ✅ **V1.0 Production Hardening Complete**
- **Status:** All deployment blockers resolved, system production-ready
- **Achievements:** UI optimization, reliable testing, enhanced UX, intelligent ML
- **Impact:** System advanced from development to production-complete status

### ✅ **Revolutionary S3 Serverless Model Loading - Operational**
- **Location:** `core/ml/model_loader.py`
- **Status:** Production-validated with intelligent model categorization
- **Impact:** Enterprise-grade serverless inference fully operational

### ✅ **Cloud-Native Infrastructure - Complete**
- **TimescaleDB Cloud:** Production deployment with 20K+ readings seeded
- **Redis Cloud:** Operational with event coordination and caching
- **S3 Artifact Storage:** 17+ models registered and accessible
- **Configuration:** Production-ready environment configuration validated

### ✅ **Enterprise-Grade Multi-Agent System - 100% Complete**
- **Status:** All core agents operational and production-hardened
- **Agents:** ValidationAgent, DataAcquisitionAgent, NotificationAgent, AnomalyDetectionAgent
- **Integration:** Complete event coordination with reliable end-to-end testing

---

## Critical Issues Resolved in Sprint 4 & Prevention Strategies

### 1. Docker Memory Crisis (315GB+ Consumption)
**Issue**: Excessive Docker storage consumption due to build cache accumulation and dataset inclusion in build context.

**Solution Applied**:
- Enhanced `.dockerignore` to exclude large datasets (20GB+ MIMII dataset)
- Implemented multi-stage Docker builds with selective copying
- Regular `docker system prune -af --volumes` for cleanup

**Prevention Strategy**:
```bash
# Regular cleanup routine (run weekly)
docker system prune -af --volumes
docker builder prune -af

# Monitor Docker usage
docker system df
```

### 2. Poetry Dependency Management Issues
**Issue**: Missing `resampy` dependency causing "No module named 'resampy'" errors in audio processing.

**Root Cause**: Poetry lock files became inconsistent when dependencies were added to `pyproject.toml` without regenerating `poetry.lock`.

**Solution Applied**:
- Modified Dockerfiles to handle missing `poetry.lock` gracefully
- Updated Dockerfile.ml: `COPY pyproject.toml ./` → `poetry lock` → `poetry install`
- Added `resampy = "^0.4.3"` to `pyproject.toml` for audio resampling support

**Prevention Strategy**:
```bash
# When adding new dependencies:
1. Add to pyproject.toml
2. Delete poetry.lock (optional but recommended for major changes)
3. Run: poetry lock --no-update
4. Rebuild Docker images with --no-cache for dependency changes

# For Docker builds with Poetry:
# Always use: poetry lock (without --no-update) in Dockerfile to regenerate
```

### 3. Build Context Optimization
**Issue**: 23GB build context due to including datasets in Docker builds.

**Solution Applied**:
Enhanced `.dockerignore`:
```
# Dataset exclusions
data/MIMII_sound_dataset/
data/nasa_bearing_dataset/
data/XJTU_SY_bearing_datasets/
data/AI4I_2020_uci_dataset/
data/kaggle_pump_sensor_data/
*.csv
*.wav
*.parquet
```

**Prevention Strategy**:
- Always exclude large datasets from Docker builds
- Use volume mounts for data access: `-v $(pwd)/data:/app/data`
- Monitor build context size before building

### 4. Audio Processing Dependencies
**Critical Dependencies for Audio Processing**:
- `librosa ^0.10.1` - Core audio analysis
- `resampy ^0.4.3` - Audio resampling (CRITICAL for librosa)
- `libsndfile1` - System library for audio file support
- `tqdm ^4.66.0` - Progress bars for long audio processing

### 5. Docker Build Best Practices
```dockerfile
# Multi-stage pattern for ML containers
FROM python:3.12-slim AS builder
# Install build dependencies and Poetry
# Generate dependencies without application code

FROM python:3.12-slim AS production
# Copy only compiled dependencies
# Install runtime libraries
# Copy application code last
```

### 6. Testing Environment Setup Issues
**Issue**: Tests fail because pytest and other dev dependencies are missing from production containers.

**Root Cause**: Production Dockerfile uses `poetry install --only=main` which excludes dev dependencies including pytest, and poetry itself is not copied to the final image.

**Solutions**:
1. **Quick Fix for Running Containers**: Install pytest directly in running container:
   ```bash
   docker compose exec api pip install pytest pytest-asyncio
   ```

2. **Proper Fix for Development**: Modify Dockerfile to include dev dependencies for development builds:
   ```dockerfile
   # In builder stage, install dev dependencies for development
   RUN poetry install --with dev --no-root  # Instead of --only=main
   ```

3. **Alternative**: Create separate dev Dockerfile or use docker-compose override for development.

**Prevention Strategy**:
- Always verify test dependencies are available before running tests
- Consider separate production and development Docker configurations
- Document which dependencies are needed for testing vs production
- Use `docker compose exec api pip list` to verify available packages

**Verification Commands**:
```bash
# Check if pytest is available
docker compose exec api python -c "import pytest; print('pytest available')"

# List all installed packages
docker compose exec api pip list | grep pytest

# Quick install for testing (temporary)
docker compose exec api pip install pytest pytest-asyncio
```

## Quick Reference Commands

### Docker Management
```bash
# Full system cleanup
docker system prune -af --volumes

# Build without cache (for dependency changes)
docker build --no-cache -f Dockerfile.ml -t smart-maintenance-ml .

# Check Docker usage
docker system df
```

### Poetry Management
```bash
# Add new dependency safely
poetry add package_name
poetry lock --no-update  # Regenerate lock file
# Rebuild Docker images

# Debug dependency issues
poetry show --tree
poetry check
```

### Audio Processing Verification
```bash
# Test audio dependencies in container
docker run --rm smart-maintenance-ml python -c "import librosa, resampy; print('Audio deps OK')"
```

## Environment Setup Checklist
- [ ] Python 3.12+ environment
- [ ] Poetry 1.8.3 for dependency management
- [ ] Docker with sufficient disk space (50GB+ recommended)
- [ ] System libraries: libsndfile1 for audio processing
- [ ] MLflow server running on port 5000
- [ ] TimescaleDB for time-series data storage

## Data Management
- **Mount, Don't Copy**: Always use volume mounts for large datasets
- **Exclude from Builds**: Keep datasets out of Docker build context
- **Version Control**: Use DVC for dataset versioning (already configured)

---

## 7. MLflow Infrastructure & Model Loading Issues (Day 13.5 Critical Findings)

### Problem: "Model Not Found" Despite Successful Registration
**Symptom**: API endpoints return `{"detail":"Model 'model_name' version 'X' not found in MLflow Registry"}` even when models appear registered.

**Root Cause Investigation Process**:
1. **Add Comprehensive Error Logging**: First step should always be adding `traceback.print_exc()` to model loading code
2. **Check for Underlying Filesystem Errors**: The real error was `OSError: No such file or directory: '/mlruns/...'` hidden behind the generic message
3. **Test Registry vs Artifact Access**: Use `client.search_model_versions()` to distinguish between registry connectivity and file access issues

**Critical Diagnostic Commands**:
```bash
# Test MLflow registry connectivity from API container
docker compose exec api python -c "
from mlflow.tracking import MlflowClient
import mlflow
mlflow.set_tracking_uri('http://mlflow:5000')
client = MlflowClient()
print('Models:', [m.name for m in client.search_registered_models()])
print('Versions:', client.search_model_versions(\"name='MODEL_NAME'\"))
"

# Test direct model loading
docker compose exec api python -c "
import mlflow.sklearn
model = mlflow.sklearn.load_model('models:/MODEL_NAME/VERSION')
print('Model loaded:', type(model))
"

# Check if artifact files exist
docker compose exec api ls -la /mlruns/EXPERIMENT_ID/RUN_ID/artifacts/model/
```

### Issue 1: Stale Docker Images with Wrong MLflow Configuration
**Problem**: MLflow server running with in-memory storage despite correct `Dockerfile.mlflow` configuration.

**Root Cause**: Docker was using cached image built before persistent storage configuration was added.

**Solution**:
```bash
# Always do a complete reset when debugging MLflow issues
docker compose down
docker system prune -af --volumes  # Remove ALL cached images and volumes
docker compose up -d --build
```

**Prevention**:
- Use `--no-cache` flag when rebuilding MLflow-related containers
- Regular cleanup: `docker system prune -af` weekly
- Check running configuration: `docker compose exec mlflow env | grep MLFLOW`

### Issue 2: Docker Volume Mount Path Inconsistencies
**Problem**: Containers mount MLflow artifacts at different paths, causing filesystem access failures.

**Critical Check**: Ensure ALL containers that need MLflow access use IDENTICAL mount paths:
```yaml
# WRONG - Different paths across containers:
api:
  volumes:
    - ./mlflow_data:/app/mlruns
mlflow:
  volumes:
    - ./mlflow_data:/mlruns
notebook_runner:
  volumes: []  # Missing volume!

# CORRECT - Consistent paths:
api:
  volumes:
    - ./mlflow_data:/mlruns
mlflow:
  volumes:
    - ./mlflow_data:/mlruns
notebook_runner:
  volumes:
    - ./mlflow_data:/mlruns
```

**Validation Command**:
```bash
# Check mount consistency across all containers
docker compose exec api ls -la /mlruns/
docker compose exec mlflow ls -la /mlruns/
docker compose exec notebook_runner ls -la /mlruns/
# All should show identical contents
```

### Issue 3: Multi-Container File Permission Conflicts
**Problem**: Files created by one container (notebook_runner) not accessible by another (api) due to UID/GID mismatches.

**Solution**: Add consistent user mapping to ALL containers that share volumes:
```yaml
api:
  user: "1000:1000"  # Match host user
notebook_runner:
  user: "1000:1000"  # Must match API container
```

**Recovery Commands**:
```bash
# Fix existing file permissions
sudo chown -R 1000:1000 ./mlflow_data ./mlflow_db

# Verify permissions after restart
docker compose exec api python -c "
import mlflow.sklearn
model = mlflow.sklearn.load_model('models:/MODEL_NAME/VERSION')
print('✅ Permissions fixed!')
"
```

### Issue 4: Empty MLflow Registry After Restart
**Symptoms**: 
- `client.search_model_versions()` returns empty list `[]`
- Models disappeared after container restart
- MLflow UI shows no experiments

**Diagnosis**: Check if MLflow is using persistent storage:
```bash
# Check MLflow startup command
docker compose logs mlflow | grep "mlflow server"
# Should see: --backend-store-uri sqlite:////mlflow_db/mlflow.db

# Check if database file exists
docker compose exec mlflow ls -la /mlflow_db/
# Should see mlflow.db file

# Check if database is actually being used
docker compose exec mlflow sqlite3 /mlflow_db/mlflow.db ".tables"
# Should show MLflow tables: experiments, runs, etc.
```

**Solution**: Verify `Dockerfile.mlflow` has correct persistent configuration:
```dockerfile
CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000", 
     "--backend-store-uri", "sqlite:////mlflow_db/mlflow.db", 
     "--default-artifact-root", "/mlruns"]
```

### MLflow Debugging Methodology (Proven Process)

**Phase 1: Error Surface Analysis**
```bash
# Add comprehensive logging to model_loader.py
import traceback
try:
    model = mlflow.sklearn.load_model(model_uri)
except Exception as e:
    print(f"MLflow load error: {e}")
    traceback.print_exc()  # CRITICAL - reveals underlying issues
    raise
```

**Phase 2: Registry vs Filesystem Separation**
```bash
# Test registry connectivity (metadata)
client.search_registered_models()
client.get_model_version('model_name', 'version')

# Test filesystem access (artifacts)
os.path.exists('/mlruns/EXPERIMENT/RUN/artifacts/model')
os.listdir('/mlruns/EXPERIMENT/RUN/artifacts/model')
```

**Phase 3: Container Environment Validation**
```bash
# Check MLflow tracking URI
echo $MLFLOW_TRACKING_URI

# Test container-to-container connectivity
curl http://mlflow:5000/health

# Verify volume mounts
mount | grep mlruns
```

**Phase 4: Clean Slate Approach**
```bash
# When in doubt, complete reset
docker compose down
sudo rm -rf ./mlflow_db ./mlflow_data
docker system prune -af
docker compose up -d
```

### Self-Contained Testing for MLflow Issues
**Create Minimal Reproduction**: Always test with synthetic data to isolate infrastructure issues:

```python
# notebooks/mlflow_validation_test.ipynb
import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import IsolationForest

# Generate synthetic data (no external dependencies)
data = pd.DataFrame({
    'feature1': np.random.normal(0, 1, 100),
    'feature2': np.random.normal(0, 1, 100)
})

# Train and register model
mlflow.set_tracking_uri("http://mlflow:5000")
with mlflow.start_run():
    model = IsolationForest()
    model.fit(data)
    mlflow.sklearn.log_model(model, "model", 
                            registered_model_name="test_model")
```

### Prevention Checklist for MLflow Issues
- [ ] **Volume Consistency**: All containers use identical `/mlruns` mount paths
- [ ] **User Mapping**: All containers that share MLflow volumes use `user: "1000:1000"`
- [ ] **Persistent Storage**: MLflow uses SQLite backend, not in-memory
- [ ] **Clean State**: Regular `docker system prune` to prevent stale cache issues
- [ ] **Comprehensive Logging**: Always add `traceback.print_exc()` to model loading code
- [ ] **Direct Testing**: Test MLflow client calls directly in containers before API integration
- [ ] **Self-Contained Validation**: Use synthetic data for infrastructure testing

### Quick MLflow Health Check Commands
```bash
# Complete MLflow system validation
echo "=== MLflow Health Check ==="

# 1. Service connectivity
curl -f http://localhost:5000/health && echo "✅ MLflow server responsive"

# 2. Registry functionality
docker compose exec api python -c "
from mlflow.tracking import MlflowClient
import mlflow
mlflow.set_tracking_uri('http://mlflow:5000')
client = MlflowClient()
models = client.search_registered_models()
print(f'✅ Registry has {len(models)} models')
"

# 3. Artifact accessibility
docker compose exec api ls /mlruns/ && echo "✅ Artifacts accessible"

# 4. Model loading
docker compose exec api python -c "
import mlflow.sklearn
# Test with known model
model = mlflow.sklearn.load_model('models:/MODEL_NAME/latest')
print('✅ Model loading working')
"

# 5. File permissions
docker compose exec api python -c "
import os
test_file = '/mlruns/test_write'
with open(test_file, 'w') as f: f.write('test')
os.remove(test_file)
print('✅ File permissions working')
"
```

### Emergency MLflow Recovery Procedure
When MLflow is completely broken:

```bash
# Step 1: Complete reset
docker compose down
sudo rm -rf ./mlflow_db ./mlflow_data
docker system prune -af

# Step 2: Verify docker-compose.yml configuration
grep -A 5 "mlflow:" docker-compose.yml
grep -A 5 "user:" docker-compose.yml
grep "mlruns" docker-compose.yml

# Step 3: Rebuild and test
docker compose up -d
sleep 30

# Step 4: Run self-contained validation
docker compose run --rm notebook_runner jupyter execute notebooks/mlflow_validation_test.ipynb

# Step 5: Verify API can load models
curl -X POST http://localhost:8000/api/v1/ml/predict \
  -H 'Content-Type: application/json' \
  -d '{"model_name": "test_model", "model_version": "1", "features": {}}'
```
