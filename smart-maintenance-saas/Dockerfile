# Multi-stage Dockerfile for Smart Maintenance SaaS
# Stage 1: Builder - Install dependencies
FROM python:3.11-slim-bullseye AS builder

# Add metadata labels
LABEL maintainer="Smart Maintenance SaaS Team"
LABEL description="Smart Maintenance SaaS - AI-powered predictive maintenance platform"
LABEL version="1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies with added resilience (retries & no recommends)
RUN echo 'Acquire::Retries "3";' > /etc/apt/apt.conf.d/80-retries \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /etc/apt/apt.conf.d/80-retries

# Install Poetry
RUN pip install poetry==1.8.3

# Configure Poetry to create venv in project
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Create virtual environment and install dependencies
RUN poetry config virtualenvs.create true && \
    poetry config virtualenvs.in-project true && \
    poetry lock && \
    poetry install --only=main --no-root && \
    rm -rf $POETRY_CACHE_DIR && \
    # Clean up unnecessary files to save space
    find /app/.venv -name "*.pyc" -delete && \
    find /app/.venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Verify that .venv was created
RUN ls -la /app/.venv && echo "Virtual environment created successfully"

# Stage 2: Production - Create slim final image
FROM python:3.11-slim-bullseye AS production

# Add metadata labels for production stage
LABEL maintainer="Smart Maintenance SaaS Team"
LABEL description="Smart Maintenance SaaS - AI-powered predictive maintenance platform"
LABEL version="1.0"
LABEL org.opencontainers.image.source="https://github.com/your-username/enterprise_challenge_sprint_1_hermes_reply"
LABEL org.opencontainers.image.description="Smart Maintenance SaaS - Production ready container"
LABEL org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set work directory
WORKDIR /app

# Copy virtual environment from builder stage (with proper ownership)
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code with proper ownership from the start
COPY --chown=appuser:appuser . .

# Create necessary directories with proper ownership
RUN mkdir -p /app/logs /app/data /app/reports && \
    chown appuser:appuser /app/logs /app/data /app/reports

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
