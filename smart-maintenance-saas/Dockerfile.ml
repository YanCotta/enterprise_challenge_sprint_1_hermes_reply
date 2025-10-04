# Dockerfile.ml - Optimized ML-focused Docker image for Smart Maintenance SaaS
# Updated 2025-10-03: Replaced Poetry with pip/virtualenv to resolve build failures
# This follows the same approach successfully implemented for the API container
FROM python:3.11-slim AS builder

# Add metadata labels
LABEL maintainer="Smart Maintenance SaaS Team"
LABEL description="Smart Maintenance SaaS - ML training and notebook execution"
LABEL version="1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies with added resilience
RUN echo 'Acquire::Retries "3";' > /etc/apt/apt.conf.d/80-retries \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        libsndfile1 \
        libgomp1 \
        libomp-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /etc/apt/apt.conf.d/80-retries

# Create virtual environment location
ENV VENV_PATH=/opt/venv

# Create virtual environment up front for dependency installs
RUN python -m venv ${VENV_PATH}

# Make sure the venv is active for subsequent commands
ENV PATH="${VENV_PATH}/bin:${PATH}"

# Set work directory
WORKDIR /app

# Copy dependency specification
COPY requirements/api.txt /tmp/requirements.txt

# Install Python dependencies inside the virtual environment
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm -rf /root/.cache/pip

# === Final stage ===
FROM python:3.11-slim

# Add metadata labels for production stage
LABEL maintainer="Smart Maintenance SaaS Team"
LABEL description="Smart Maintenance SaaS - ML training runtime"
LABEL version="1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    libsndfile1 \
    libgomp1 \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set work directory
WORKDIR /app

# Copy virtual environment from builder stage (with proper ownership)
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv

# Copy application code with proper ownership
COPY --chown=appuser:appuser . .

# Install Jupyter-related packages and AWS dependencies for MLflow
RUN pip install --no-cache-dir ipykernel seaborn boto3 papermill && \
    python -m ipykernel install --user --name=python3

# Switch to non-root user
USER appuser

# Default command
CMD ["bash"]