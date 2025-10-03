# Dockerfile.ml - Optimized ML-focused Docker image for Smart Maintenance SaaS
# NOTE 2025-10-03: notebook_runner service is disabled in docker-compose while we fix the Poetry build failure.
FROM python:3.11-slim AS builder

# Install only system dependencies needed for building
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    libgomp1 \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry (use 1.7.1 to avoid "Could not parse version constraint" bug in 1.8.x)
RUN pip install --no-cache-dir poetry==1.7.1

# Set working directory
WORKDIR /app

# Copy Poetry files for dependency installation
COPY pyproject.toml poetry.lock* ./

# Configure Poetry and install dependencies
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=0 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install dependencies from lock file (or generate if missing)
RUN poetry config virtualenvs.create false && \
    (test -f poetry.lock || poetry lock) && \
    poetry install --no-root && \
    rm -rf $POETRY_CACHE_DIR

# === Final stage ===
FROM python:3.11-slim

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libsndfile1 \
    libgomp1 \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Install Jupyter-related packages and AWS dependencies for MLflow
RUN pip install --no-cache-dir ipykernel seaborn boto3 && \
    python -m ipykernel install --user --name=python3

# Copy only application code (datasets are excluded by .dockerignore)
COPY . .

# Install the project itself in editable mode
RUN pip install -e . --no-deps

# Default command
CMD ["bash"]