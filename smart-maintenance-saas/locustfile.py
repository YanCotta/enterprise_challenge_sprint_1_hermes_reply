from locust import task, between, User, HttpUser
from apps.ml.model_loader import load_model

# List of some of our champion models to test loading.
# Add more models here as they are registered.
CHAMPION_MODELS = [
    ("ai4i_classifier_randomforest_baseline", "2"),
    ("vibration_anomaly_isolationforest", "1"),
    ("xjtu_anomaly_isolation_forest", "2"),
    ("RandomForest_MIMII_Audio_Benchmark", "1"),
]

class ModelLoaderUser(User):
    """
    A Locust User that simulates an agent or service requesting models
    from the MLflow Model Registry via our model_loader.
    """
    # Wait between 1 and 3 seconds between each task.
    wait_time = between(1, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_index = 0

    @task
    def load_champion_model(self):
        """
        A task that picks a model from our list and attempts to load it.
        This tests the entire model loading and caching pipeline.
        """
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