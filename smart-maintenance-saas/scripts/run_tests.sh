#!/usr/bin/env bash
# Run tests for Smart Maintenance SaaS

set -e

# Default values
RUN_COVERAGE=0
USE_CONTAINER=1
TEST_PATH="tests"
TEST_ARGS=""

# Parse arguments
while (( "$#" )); do
  case "$1" in
    --cov)
      RUN_COVERAGE=1
      shift
      ;;
    --no-container)
      USE_CONTAINER=0
      export PYTEST_DIRECT_DB=1
      shift
      ;;
    --path)
      TEST_PATH="$2"
      shift 2
      ;;
    -k|--keyword)
      TEST_ARGS="$TEST_ARGS -k $2"
      shift 2
      ;;
    -m|--marker)
      TEST_ARGS="$TEST_ARGS -m $2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo
      echo "Options:"
      echo "  --cov                  Run tests with coverage"
      echo "  --no-container         Don't use Docker container for database tests"
      echo "  --path <path>          Specify test path (default: tests)"
      echo "  -k, --keyword <expr>   Only run tests which match the given substring expression"
      echo "  -m, --marker <marker>  Only run tests with the given marker"
      echo "  --help                 Show this help message"
      exit 0
      ;;
    *)
      TEST_ARGS="$TEST_ARGS $1"
      shift
      ;;
  esac
done

# Set environment variables
export PYTHONPATH=.
export ENV_FILE=.env.test

# Build the pytest command
CMD="python -m pytest $TEST_PATH $TEST_ARGS -v"

if [ $RUN_COVERAGE -eq 1 ]; then
  CMD="$CMD --cov=smart_maintenance_saas --cov-report=xml --cov-report=term"
fi

# Run tests
echo "Running: $CMD"
eval "$CMD"
