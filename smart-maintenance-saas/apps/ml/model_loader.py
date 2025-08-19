import mlflow
import os
from typing import Any, Dict

MLFLOW_TRACKING_URI = "http://mlflow:5000"
os.environ["MLFLOW_TRACKING_URI"] = MLFLOW_TRACKING_URI
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

_model_cache: Dict[str, Any] = {}


def load_model(model_name: str, model_version: str = "1") -> Any:
    """
    Load a model from the MLflow Model Registry with in-memory caching.

    Args:
        model_name (str): The name of the model in the MLflow Registry.
        model_version (str): The version of the model to load.

    Returns:
        Any: The loaded model object, or None if an error occurs.
    """
    cache_key = f"{model_name}:{model_version}"
    if cache_key in _model_cache:
        print(f"Loading model '{cache_key}' from cache.")
        return _model_cache[cache_key]

    try:
        print(f"Loading model '{cache_key}' from MLflow Registry...")
        model_uri = f"models:/{model_name}/{model_version}"
        loaded_model = mlflow.pyfunc.load_model(model_uri)
        _model_cache[cache_key] = loaded_model
        print("Model loaded and cached successfully.")
        return loaded_model
    except Exception as e:
        print(f"Error loading model '{model_name}' v'{model_version}': {e}")
        return None


if __name__ == "__main__":
    print("--- Testing Model Loader ---")
    CHAMPION_MODEL = "ai4i_classifier_randomforest_baseline"
    CHAMPION_VERSION = "2"

    ai4i_model = load_model(CHAMPION_MODEL, CHAMPION_VERSION)
    if ai4i_model:
        print(f"\\n✅ Successfully loaded '{CHAMPION_MODEL}'.")
    else:
        print(f"\\n❌ Failed to load '{CHAMPION_MODEL}'.")

    print("\\n--- Testing Model Caching ---")
    cached_model = load_model(CHAMPION_MODEL, CHAMPION_VERSION)
    if cached_model:
        print("\\n✅ Model was successfully retrieved from the cache.")
