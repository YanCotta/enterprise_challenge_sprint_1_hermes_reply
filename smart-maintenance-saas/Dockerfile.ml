# Dockerfile.ml - Optimized ML-focused Docker image for Smart Maintenance SaaS
FROM python:3.12-slim AS builder

# Install only system dependencies needed for building
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Set working directory
WORKDIR /app

# Copy only Poetry files first for better layer caching
COPY pyproject.toml ./

# Configure Poetry and install dependencies
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=0 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --with dev --no-root && \
    rm -rf $POETRY_CACHE_DIR

# === Final stage ===
FROM python:3.12-slim

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Install Jupyter-related packages
RUN pip install --no-cache-dir ipykernel seaborn && \
    python -m ipykernel install --user --name=python3

# Copy only application code (datasets are excluded by .dockerignore)
COPY . .

# Install the project itself in editable mode
RUN pip install -e . --no-deps

# Default command
CMD ["bash"]