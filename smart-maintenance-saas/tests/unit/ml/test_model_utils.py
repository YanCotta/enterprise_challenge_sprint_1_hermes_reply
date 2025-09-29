import pytest

from apps.ml import model_utils


@pytest.fixture(autouse=True)
def _enable_mlflow_loading(monkeypatch):
    """Ensure tests run with MLflow loading enabled unless overridden."""
    monkeypatch.setattr(model_utils.settings, "DISABLE_MLFLOW_MODEL_LOADING", False, raising=False)


def test_get_model_recommendations_prefers_specific_and_general(monkeypatch):
    monkeypatch.setattr(
        model_utils,
        "get_models_by_sensor_type",
        lambda: {"temperature": ["temp_model"], "general": ["general_model"]},
    )

    result = model_utils.get_model_recommendations("temperature")

    assert result == ["temp_model", "general_model"]


def test_get_model_recommendations_excludes_general_when_flag_false(monkeypatch):
    monkeypatch.setattr(
        model_utils,
        "get_models_by_sensor_type",
        lambda: {"temperature": ["temp_model"], "general": ["general_model"]},
    )

    result = model_utils.get_model_recommendations("temperature", include_general=False)

    assert result == ["temp_model"]


def test_get_model_recommendations_handles_enum_like_values(monkeypatch):
    class DummySensorType:
        def __init__(self, value: str):
            self.value = value

    monkeypatch.setattr(
        model_utils,
        "get_models_by_sensor_type",
        lambda: {"vibration": ["vibration_model"], "bearing": ["bearing_model"]},
    )

    result = model_utils.get_model_recommendations(DummySensorType("vibration"))

    assert result == ["vibration_model", "bearing_model"]


def test_get_model_recommendations_returns_fallback_when_unknown(monkeypatch):
    monkeypatch.setattr(model_utils, "get_models_by_sensor_type", lambda: {})

    result = model_utils.get_model_recommendations(None)

    assert result == [
        "anomaly_detector_refined_v2",
        "synthetic_validation_isolation_forest",
    ]
