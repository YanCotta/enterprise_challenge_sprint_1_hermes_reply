import os
import logging
import traceback
import json
from typing import Any, Dict, List, Optional, Tuple

import mlflow
import mlflow.pyfunc
from mlflow.tracking import MlflowClient
from mlflow.artifacts import download_artifacts

from core.config.settings import settings

# Set up logging
logger = logging.getLogger(__name__)

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")


def mlflow_disabled() -> bool:
    """Determine if MLflow interactions are disabled via env/settings."""
    env_override = os.getenv("DISABLE_MLFLOW_MODEL_LOADING")
    if env_override is not None:
        return env_override.lower() in {"1", "true", "yes", "on"}
    return getattr(settings, "DISABLE_MLFLOW_MODEL_LOADING", False)


if not mlflow_disabled():
    os.environ["MLFLOW_TRACKING_URI"] = MLFLOW_TRACKING_URI
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    _MLFLOW_CLIENT: Optional[MlflowClient] = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)
else:
    logger.info("MLflow model loading disabled; skipping MlflowClient initialization.")
    _MLFLOW_CLIENT = None

_model_cache: Dict[str, Tuple[Any, Optional[List[str]]]] = {}

# Direct S3 fallbacks for scenarios where the MLflow registry is unavailable but
# artifacts are still stored remotely. URIs are derived from docs/S3_ARTIFACT_MAPPING.md.
S3_MODEL_URIS: Dict[str, str] = {
    "ai4i_classifier_randomforest_baseline": "s3://yan-smart-maintenance-artifacts/4/c795e657a4d147f1ac84ea0dc2bb68f1/artifacts/model",
    "anomaly_detector_refined_v2": "s3://yan-smart-maintenance-artifacts/2/b702f86472f44eefb1d24ec0b68361ad/artifacts/model",
}

# Feature name hints for S3 fallbacks when feature_names.txt is not accessible.
S3_FEATURE_NAME_HINTS: Dict[str, List[str]] = {
    "ai4i_classifier_randomforest_baseline": [
        "Air_temperature_K",
        "Process_temperature_K",
        "Rotational_speed_rpm",
        "Torque_Nm",
        "Tool_wear_min",
    ],
    "anomaly_detector_refined_v2": [
        "value_lag_1",
        "value_lag_2",
        "value_lag_3",
        "value_lag_4",
        "value_lag_5",
        "value_scaled",
        "quality_scaled",
    ],
}


def _load_from_s3_fallback(model_name: str) -> Tuple[Optional[Any], Optional[List[str]]]:
    """Attempt to load a model directly from S3 when the registry lookup fails."""

    if mlflow_disabled():
        logger.debug("MLflow disabled; skipping S3 fallback for model '%s'", model_name)
        return None, None

    s3_uri = S3_MODEL_URIS.get(model_name)
    if not s3_uri:
        logger.debug("No S3 fallback registered for model '%s'", model_name)
        return None, None

    try:
        logger.warning("Falling back to S3 for model '%s' (%s)", model_name, s3_uri)
        loaded_model = mlflow.pyfunc.load_model(s3_uri)
        feature_names = S3_FEATURE_NAME_HINTS.get(model_name)
        if feature_names:
            logger.info("Loaded S3 fallback with feature schema for model '%s'", model_name)
        return loaded_model, feature_names
    except Exception as s3_err:  # noqa: BLE001
        logger.error("S3 fallback load failed for model '%s': %s", model_name, s3_err, exc_info=True)
        print(f"Failed S3 fallback for model '{model_name}': {s3_err}")
        return None, None


def _debug_list_model_versions(model_name: str) -> None:
    """Log available versions for a model to aid troubleshooting."""
    try:
        if _MLFLOW_CLIENT is None:
            logger.debug("Mlflow client unavailable; cannot list versions for '%s'", model_name)
            return
        versions = _MLFLOW_CLIENT.search_model_versions(f"name='{model_name}'")
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
    if mlflow_disabled():
        logger.warning(
            "MLflow model loading disabled; returning no model for '%s' (requested version %s)",
            model_name,
            model_version,
        )
        return None, None

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
                if _MLFLOW_CLIENT is None:
                    logger.warning(
                        "Mlflow client unavailable; cannot resolve model version for '%s'", model_name
                    )
                    return None, None
                if model_name.startswith("models:/"):
                    # Parse name/version from the URI: models:/<name>/<version>
                    _, _, name_part, version_part = model_name.split("/", 3)
                    mv_info = _MLFLOW_CLIENT.get_model_version(name_part, version_part)
                else:
                    mv_info = _MLFLOW_CLIENT.get_model_version(model_name, model_version)
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
                            raw_content = f.read().strip()
                        if raw_content:
                            try:
                                parsed = json.loads(raw_content)
                                if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
                                    feature_names = parsed
                                else:
                                    feature_names = [line.strip() for line in raw_content.splitlines() if line.strip()]
                            except json.JSONDecodeError:
                                feature_names = [line.strip() for line in raw_content.splitlines() if line.strip()]
                        if feature_names:
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
        fallback_model, fallback_features = _load_from_s3_fallback(model_name)
        if fallback_model is not None:
            _model_cache[cache_key] = (fallback_model, fallback_features)
            return fallback_model, fallback_features
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
