# Dockerfile.ml - ML-focused Docker image for Smart Maintenance SaaS
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Configure Poetry environment variables
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=0 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy Poetry files first
COPY pyproject.toml poetry.lock ./

# Configure Poetry to install globally for Docker
RUN poetry config virtualenvs.create false && \
    poetry install --with dev && \
    rm -rf $POETRY_CACHE_DIR

# Install Jupyter-related packages
RUN pip install ipykernel seaborn && \
    python -m ipykernel install --user --name=python3

# Copy project files
COPY . .

# Install the project itself in editable mode
RUN pip install -e .

# Default command
CMD ["bash"]