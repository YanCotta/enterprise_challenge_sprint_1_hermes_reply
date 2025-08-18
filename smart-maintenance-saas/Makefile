# Makefile for Smart Maintenance SaaS ML workflows

.PHONY: help build-ml eda train-anomaly test-features clean

# Default target
help:
	@echo "Available targets:"
	@echo "  build-ml       Build the ML Docker image"
	@echo "  eda            Run the EDA notebook in Docker"
	@echo "  train-anomaly  Run the anomaly detection training notebook"
	@echo "  train-forecast Run the forecasting training notebook (Prophet)"
	@echo "  tune-forecast  Run the forecasting tuning & challenger notebook"
	@echo "  classification-gauntlet  Run the Classification Gauntlet notebook (AI4I)"
	@echo "  test-features  Run feature engineering tests"
	@echo "  clean          Clean up Docker images and containers"

# Build ML Docker image
build-ml:
	docker build -f Dockerfile.ml -t smart-maintenance-ml .

# Run EDA notebook in Docker using papermill
eda: build-ml
	@echo "Running EDA notebook in Docker..."
	@mkdir -p docs/ml
	docker run --rm -v $(PWD):/app smart-maintenance-ml \
		papermill notebooks/01_data_exploration.ipynb notebooks/01_data_exploration_output.ipynb

# Run anomaly detection training notebook in Docker
.PHONY: train-anomaly
train-anomaly: build-ml
	@echo "--- Running Anomaly Detection Training Notebook via Docker Compose ---"
	@mkdir -p docs/ml
	docker compose run --rm --service-ports notebook_runner

# Run forecasting training notebook (Prophet) via docker compose
.PHONY: train-forecast
train-forecast: build-ml
	@echo "--- Running Forecast Training Notebook via Docker Compose ---"
	@mkdir -p docs/ml
	docker compose run --rm -e NOTEBOOK_FILE=03_forecast_prophet --service-ports notebook_runner

# Run forecast tuning and challenger models notebook
.PHONY: tune-forecast
tune-forecast: build-ml
	@echo "--- Running Forecast Tuning & Challenger Notebook ---"
	docker compose run --rm -e NOTEBOOK_FILE=04_forecasting_tuning_and_challenger_models --service-ports notebook_runner

# Run Classification Gauntlet notebook (AI4I Dataset)
.PHONY: classification-gauntlet
classification-gauntlet: build-ml
	@echo "--- Running Classification Gauntlet (AI4I Dataset) ---"
	@mkdir -p docs/ml
	docker compose run --rm -e NOTEBOOK_FILE=05_classification_benchmark --service-ports notebook_runner
	@echo "--- Fixing file ownership ---"
	sudo chown -R $(USER):$(USER) notebooks/*_output.ipynb 2>/dev/null || true

# Run feature engineering tests
test-features: build-ml
	@echo "Running feature engineering tests..."
	docker run --rm -v $(PWD):/app smart-maintenance-ml \
		python -m pytest tests/unit/test_features.py -v

# Clean up Docker resources
clean:
	docker image prune -f
	docker container prune -f