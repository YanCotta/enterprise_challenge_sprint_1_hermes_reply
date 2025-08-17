"""Locust load test focused on MLflow Model Registry endpoints.

Simulates users querying registered model metadata and latest versions to
validate availability and basic performance characteristics of the MLflow
service inside the Docker Compose network.

Run (from smart-maintenance-saas directory):
  docker compose run --rm -v $(pwd):/app -w /app --service-ports ml \
    locust -f locustfile.py --host http://mlflow:5000 --users 5 --run-time 2m --headless --print-stats
"""

from locust import HttpUser, task, between
import random
import json


class MLflowUser(HttpUser):
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    def on_start(self):
        """Initialize list of registered models to probe."""
        self.registered_models = [
            "anomaly_detector_refined_v2",
            "prophet_forecaster_sensor-001",
        ]

    @task
    def get_registered_model(self):
        """Fetch a registered model's details."""
        model_name = random.choice(self.registered_models)
        self.client.get(
            f"/api/2.0/mlflow/registered-models/get?name={model_name}",
            name="/api/2.0/mlflow/registered-models/get",
        )

    @task
    def get_latest_versions(self):
        """Fetch latest versions for a registered model (correct POST usage)."""
        model_name = random.choice(self.registered_models)
        # MLflow API expects POST to /registered-models/get-latest-versions with JSON body
        self.client.post(
            "/api/2.0/mlflow/registered-models/get-latest-versions",
            json={"name": model_name, "stages": []},
            name="/api/2.0/mlflow/registered-models/get-latest-versions",
        )
