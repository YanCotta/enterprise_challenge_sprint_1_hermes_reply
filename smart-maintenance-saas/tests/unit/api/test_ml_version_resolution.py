import importlib

import pytest

MODULE_NAME = "apps.api.routers.ml_endpoints"


def _reload_ml_endpoints(monkeypatch):
    module = importlib.import_module(MODULE_NAME)
    return importlib.reload(module)


def test_resolve_model_version_prefers_mlflow_latest(monkeypatch):
    module = _reload_ml_endpoints(monkeypatch)
    monkeypatch.setenv("DISABLE_MLFLOW_MODEL_LOADING", "false")
    monkeypatch.setattr(module, "mlflow_disabled", lambda: False, raising=False)
    module.MLFLOW_AVAILABLE = True

    class _DummyVersion:
        version = "7"

    class _DummyClient:
        def get_latest_versions(self, model_name, stages):
            return [_DummyVersion()]

    monkeypatch.setattr(module, "MlflowClient", lambda: _DummyClient(), raising=False)

    load_calls = []

    def fake_load(model_name, model_version):
        load_calls.append((model_name, model_version))
        return (None, None)

    monkeypatch.setattr(module, "load_model", fake_load, raising=False)

    resolved = module._resolve_model_version("demo_model", "auto")

    assert resolved == "7"
    assert not load_calls  # should not fall back when MLflow succeeds


def test_resolve_model_version_falls_back_to_load_model(monkeypatch):
    module = _reload_ml_endpoints(monkeypatch)
    monkeypatch.setenv("DISABLE_MLFLOW_MODEL_LOADING", "false")
    monkeypatch.setattr(module, "mlflow_disabled", lambda: False, raising=False)
    module.MLFLOW_AVAILABLE = True

    class _FailingClient:
        def get_latest_versions(self, model_name, stages):
            raise RuntimeError("registry unavailable")

    monkeypatch.setattr(module, "MlflowClient", lambda: _FailingClient(), raising=False)

    def fake_load(model_name, model_version):
        if model_version == "3":
            return (object(), None)
        return (None, None)

    monkeypatch.setattr(module, "load_model", fake_load, raising=False)

    resolved = module._resolve_model_version("demo_model", "auto")

    assert resolved == "3"


@pytest.mark.asyncio
async def test_predict_raises_when_mlflow_disabled(monkeypatch):
    module = _reload_ml_endpoints(monkeypatch)
    monkeypatch.setattr(module, "mlflow_disabled", lambda: True, raising=False)

    request = module.PredictionRequest(
        model_name="demo_model",
        model_version="auto",
        features={"feature": 1.0},
    )

    with pytest.raises(module.HTTPException) as exc_info:
        await module.predict(request, db=None)  # type: ignore[arg-type]

    assert exc_info.value.status_code == module.status.HTTP_503_SERVICE_UNAVAILABLE
    assert "MLflow" in exc_info.value.detail
