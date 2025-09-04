#!/bin/bash
# Wrapper script to run retrain agent with proper Python environment

# Set up environment for accessing virtual environment packages
export PYTHONPATH="/app:/app/.venv/lib/python3.11/site-packages"

# Run the retrain agent using system python with venv packages in path
exec python /app/scripts/retrain_models_on_drift.py