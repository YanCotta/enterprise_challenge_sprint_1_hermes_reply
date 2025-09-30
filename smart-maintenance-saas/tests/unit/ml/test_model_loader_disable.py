import importlib

import pytest

MODULE_PATH = "apps.ml.model_loader"


def _reload_loader(monkeypatch, disabled_value: str):
    monkeypatch.setenv("DISABLE_MLFLOW_MODEL_LOADING", disabled_value)
    module = importlib.import_module(MODULE_PATH)
    return importlib.reload(module)


def test_load_model_returns_none_when_disabled(monkeypatch):
    loader = _reload_loader(monkeypatch, "true")

    model, features = loader.load_model("demo_model", "1")

    assert model is None
    assert features is None

    # Reset module state to avoid side effects on other tests
    _reload_loader(monkeypatch, "false")


def test_mlflow_disabled_helper_honors_env_override(monkeypatch):
    loader = _reload_loader(monkeypatch, "true")
    assert loader.mlflow_disabled() is True

    loader = _reload_loader(monkeypatch, "false")
    assert loader.mlflow_disabled() is False
