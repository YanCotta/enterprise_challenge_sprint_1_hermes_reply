# Development Orientation Guide

## Critical Issues Resolved in Phase 3 & Prevention Strategies

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
