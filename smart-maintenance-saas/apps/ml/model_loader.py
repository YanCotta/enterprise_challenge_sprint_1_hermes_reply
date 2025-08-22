import mlflow
import mlflow.pyfunc
from mlflow.tracking import MlflowClient
from mlflow.artifacts import download_artifacts
import os
import logging
import traceback
from typing import Any, Dict, List, Optional, Tuple

# Set up logging
logger = logging.getLogger(__name__)

MLFLOW_TRACKING_URI = "http://mlflow:5000"
os.environ["MLFLOW_TRACKING_URI"] = MLFLOW_TRACKING_URI
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Initialize MLflow client for model registry operations
client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)

_model_cache: Dict[str, Tuple[Any, Optional[List[str]]]] = {}


def _debug_list_model_versions(model_name: str) -> None:
    """Log available versions for a model to aid troubleshooting."""
    try:
        versions = client.search_model_versions(f"name='{model_name}'")
        if not versions:
            print(f"[model_loader] No versions found for model '{model_name}'.")
            return
        rows = []
        for mv in versions:
            rows.append(
                f"version={mv.version} stage={mv.current_stage or '-'} run_id={mv.run_id} status={getattr(mv, 'status', '-') }"
            )
        print(f"[model_loader] Existing versions for '{model_name}':\n  - " + "\n  - ".join(rows))
    except Exception as e:
        print(f"[model_loader] Failed listing versions for '{model_name}': {e}")


def load_model(model_name: str, model_version: str = "1") -> Tuple[Optional[Any], Optional[List[str]]]:
    """Load an MLflow model (registry or run URI) and accompanying feature schema.

    Enhancements for Day 13.5 hardening:
    - Returns a tuple ``(model, feature_names)`` instead of only the model.
    - Attempts to locate and read an artifact named ``feature_names.txt`` which SHOULD
      contain one feature name per line (order preserved). If not present, ``feature_names``
      is ``None`` and the caller should skip schema validation.

    Args:
        model_name: Registry model name, or a full "models:/" or "runs:/" URI.
        model_version: Registry version (ignored for explicit run or models URIs).

    Returns:
        (model, feature_names) where ``feature_names`` is ``None`` if unavailable.
        If loading fails, returns ``(None, None)``.
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
        run_id: Optional[str] = None
        # Acquire run_id for registry URIs so we can fetch artifacts
        if model_uri.startswith("models:/"):
            # model_name may already be a full models URI or a plain name
            try:
                if model_name.startswith("models:/"):
                    # Parse name/version from the URI: models:/<name>/<version>
                    _, _, name_part, version_part = model_name.split("/", 3)
                    mv_info = client.get_model_version(name_part, version_part)
                else:
                    mv_info = client.get_model_version(model_name, model_version)
                run_id = mv_info.run_id
                print(f"Found model version; associated run_id: {run_id}")
            except Exception as e:
                print(f"Model version lookup failed for '{model_name}' version '{model_version}': {e}")
                traceback.print_exc()
                _debug_list_model_versions(model_name if not model_name.startswith("models:/") else name_part)
                # Re-raise so outer except prints structured details & stack
                raise
        elif model_uri.startswith("runs:/"):
            # Extract run_id: runs:/<run_id>/optional_subpath
            try:
                run_id = model_uri.split("/", 2)[1]
            except Exception:
                run_id = None
        
        # Load the model
        loaded_model = mlflow.pyfunc.load_model(model_uri)
        feature_names: Optional[List[str]] = None

        # Attempt to retrieve feature_names.txt artifact if we have a run_id
        if run_id:
            candidate_paths = [
                "feature_names.txt",              # Root artifact
                "model/feature_names.txt",        # Inside model subdir
            ]
            for artifact_rel_path in candidate_paths:
                try:
                    local_path = download_artifacts(run_id=run_id, artifact_path=artifact_rel_path)
                    if os.path.isfile(local_path):
                        with open(local_path, "r", encoding="utf-8") as f:
                            # Strip whitespace, ignore empty lines
                            feature_names = [line.strip() for line in f if line.strip()]
                        print(f"Loaded feature schema from artifact: {artifact_rel_path} -> {feature_names}")
                        break
                except Exception:
                    # Silent fallback - we'll report absence below
                    continue
            if feature_names is None:
                print("No feature_names.txt artifact found; schema validation will be skipped.")
        else:
            print("run_id unavailable; skipping feature schema retrieval.")

        # Cache and return
        _model_cache[cache_key] = (loaded_model, feature_names)
        print(f"Model loaded and cached successfully: {type(loaded_model)}; feature_names={feature_names}")
        return loaded_model, feature_names
        
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
        # Print full stack trace to stdout for container log capture
        traceback.print_exc()
        print(f"--- END MLFLOW LOAD EXCEPTION ---")
    return None, None


if __name__ == "__main__":
    print("--- Testing Model Loader ---")
    
    # Test with run URI (known to work)
    test_run_uri = "runs:/24a06e342c1449e78a1554bd05730f52/model"
    model, feature_names = load_model(test_run_uri)
    if model:
        print(f"✅ Successfully loaded model from run URI.")
        print(f"Feature names: {feature_names}")
    else:
        print(f"❌ Failed to load model from run URI.")

    print("\n--- Testing Model Caching ---")
    cached_model, cached_features = load_model(test_run_uri)
    if cached_model:
        print("✅ Model was successfully retrieved from the cache.")
        print(f"Cached feature names: {cached_features}")
