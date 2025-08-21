import mlflow
import mlflow.pyfunc
from mlflow.tracking import MlflowClient
import os
import logging
from typing import Any, Dict

# Set up logging
logger = logging.getLogger(__name__)

MLFLOW_TRACKING_URI = "http://mlflow:5000"
os.environ["MLFLOW_TRACKING_URI"] = MLFLOW_TRACKING_URI
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Initialize MLflow client for model registry operations
client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)

_model_cache: Dict[str, Any] = {}


def load_model(model_name: str, model_version: str = "1") -> Any:
    """
    Load a model from the MLflow Model Registry with in-memory caching.
    Supports both registry URIs (models:/name/version) and run URIs (runs:/run_id/artifact_path).

    Args:
        model_name (str): The name of the model in the MLflow Registry OR a complete model URI.
        model_version (str): The version of the model to load (ignored for run URIs).

    Returns:
        Any: The loaded model object, or None if an error occurs.
    """
    # Determine if model_name is already a complete URI
    if model_name.startswith("runs:/"):
        # Direct run URI - use as-is
        model_uri = model_name
        cache_key = model_name
        print(f"Using run URI: {model_uri}")
    elif model_name.startswith("models:/"):
        # Direct models URI - use as-is  
        model_uri = model_name
        cache_key = model_name
        print(f"Using models URI: {model_uri}")
    else:
        # Registry name - construct URI
        model_uri = f"models:/{model_name}/{model_version}"
        cache_key = f"{model_name}:{model_version}"
        print(f"Constructing registry URI: {model_uri}")
    
    # Check cache first
    if cache_key in _model_cache:
        print(f"Loading model from cache: {cache_key}")
        return _model_cache[cache_key]

    try:
        print(f"Loading model from MLflow: {model_uri}")
        
        # For registry URIs, validate model exists
        if model_uri.startswith("models:/") and not model_name.startswith("models:/"):
            try:
                model_version_info = client.get_model_version(model_name, model_version)
                print(f"Found model version: {model_version_info.source}")
            except Exception as e:
                print(f"Model version not found in registry: {e}")
                return None
        
        # Load the model
        loaded_model = mlflow.pyfunc.load_model(model_uri)
        
        # Cache and return
        _model_cache[cache_key] = loaded_model
        print(f"Model loaded and cached successfully: {type(loaded_model)}")
        return loaded_model
        
    except Exception as e:
        # THIS IS THE CRITICAL LOGGING WE NEED TO ADD
        logger.error(f"--- MLFLOW LOAD EXCEPTION ---")
        logger.error(f"Failed to load model from URI: '{model_uri}'")
        logger.error(f"Exception Type: {type(e).__name__}")
        logger.error(f"Exception Details: {str(e)}", exc_info=True)
        logger.error(f"--- END MLFLOW LOAD EXCEPTION ---")
        print(f"--- MLFLOW LOAD EXCEPTION ---")
        print(f"Failed to load model from URI: '{model_uri}'")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Details: {str(e)}")
        print(f"--- END MLFLOW LOAD EXCEPTION ---")
        return None


if __name__ == "__main__":
    print("--- Testing Model Loader ---")
    
    # Test with run URI (known to work)
    test_run_uri = "runs:/24a06e342c1449e78a1554bd05730f52/model"
    model = load_model(test_run_uri)
    if model:
        print(f"✅ Successfully loaded model from run URI.")
    else:
        print(f"❌ Failed to load model from run URI.")

    print("\n--- Testing Model Caching ---")
    cached_model = load_model(test_run_uri)
    if cached_model:
        print("✅ Model was successfully retrieved from the cache.")
