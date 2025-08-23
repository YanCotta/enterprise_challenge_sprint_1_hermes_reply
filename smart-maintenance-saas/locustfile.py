from locust import task, between, User, HttpUser
from apps.ml.model_loader import load_model
import mlflow
import random

def get_available_models():
    """
    Dynamically discover available models and their latest versions from MLflow.
    This prevents test failures due to hardcoded version mismatches.
    """
    try:
        mlflow.set_tracking_uri('http://mlflow:5000')
        client = mlflow.MlflowClient()
        models = client.search_registered_models()
        
        available_models = []
        for model in models:
            try:
                # Get all versions for the model and find the highest version number
                model_versions = client.search_model_versions(f'name="{model.name}"')
                if model_versions:
                    # Sort by version number (as integers) and get the highest
                    latest_version = max(model_versions, key=lambda v: int(v.version))
                    available_models.append((model.name, latest_version.version))
                    print(f"Found model: {model.name} v{latest_version.version}")
            except Exception as e:
                print(f"Warning: Could not get versions for model {model.name}: {e}")
                continue
        
        return available_models
    except Exception as e:
        print(f"Warning: Could not connect to MLflow, using fallback models: {e}")
        # Fallback to known working models with correct versions
        return [
            ("vibration_anomaly_isolationforest", "1"),
            ("RandomForest_MIMII_Audio_Benchmark", "1"),
            ("ai4i_classifier_randomforest_baseline", "1"),
        ]

# Dynamically get available models at startup
CHAMPION_MODELS = get_available_models()
print(f"Loaded {len(CHAMPION_MODELS)} champion models for testing: {[m[0] for m in CHAMPION_MODELS]}")

class ModelLoaderUser(User):
    """
    A Locust User that simulates an agent or service requesting models
    from the MLflow Model Registry via our model_loader.
    """
    # Wait between 1 and 3 seconds between each task.
    wait_time = between(1, 3)

    def on_start(self):
        """Initialize with a random starting position in the model list."""
        if CHAMPION_MODELS:
            self.model_index = random.randint(0, len(CHAMPION_MODELS) - 1)
        else:
            self.model_index = 0

    @task
    def load_champion_model(self):
        """
        A task that picks a model from our list and attempts to load it.
        This tests the entire model loading and caching pipeline.
        """
        if not CHAMPION_MODELS:
            # No models available, skip this task
            return
            
        # Cycle through available models
        if self.model_index >= len(CHAMPION_MODELS):
            self.model_index = 0  # Reset index to loop through models

        model_to_load, version_to_load = CHAMPION_MODELS[self.model_index]
        self.model_index += 1

        # We use the 'name' parameter in the request to track which model is being loaded.
        # This will show up in the Locust UI statistics.
        with self.environment.events.request.measure(
            request_type="mlflow_model_load",
            name=f"load:{model_to_load}"
        ) as request:
            try:
                model = load_model(model_name=model_to_load, model_version=version_to_load)
                if model:
                    request.success()
                else:
                    request.failure(f"Model '{model_to_load}' v{version_to_load} failed to load (returned None).")
            except Exception as e:
                request.failure(str(e))


class DriftCheckUser(HttpUser):
    """Locust user that exercises the /check_drift endpoint under light load."""

    wait_time = between(1, 2)

    @task
    def check_drift(self):
        payload = {
            "sensor_id": "drift_sensor_load_test",
            "window_minutes": 30,
            "p_value_threshold": 0.05,
            "min_samples": 10,
        }
        with self.client.post("/api/v1/ml/check_drift", json=payload, name="check_drift") as resp:
            if resp.status_code != 200:
                resp.failure(f"Unexpected status {resp.status_code}: {resp.text}")