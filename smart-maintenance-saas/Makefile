# Makefile for Smart Maintenance SaaS ML workflows

.PHONY: help build-ml eda test-features clean

# Default target
help:
	@echo "Available targets:"
	@echo "  build-ml       Build the ML Docker image"
	@echo "  eda            Run the EDA notebook in Docker"
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

# Run feature engineering tests
test-features: build-ml
	@echo "Running feature engineering tests..."
	docker run --rm -v $(PWD):/app smart-maintenance-ml \
		python -m pytest tests/unit/test_features.py -v

# Clean up Docker resources
clean:
	docker image prune -f
	docker container prune -f