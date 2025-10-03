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
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

# Install runtime dependencies only
# Remove DNS fix that causes read-only filesystem issues in modern Docker
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
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
