#!/usr/bin/env python3
"""Minimal V1.0 smoke script for Smart Maintenance SaaS.

Flow:
1. Ingest a single sensor reading (idempotent payload).
2. Verify the reading via paginated sensor readings endpoint.
3. Perform a prediction with auto model version resolution.
4. Submit a human decision response.
5. Fetch metrics snapshot.

Outputs a JSON summary and exits 0 on success, non-zero on first failure.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_MODEL_NAME = "ai4i_classifier_randomforest_baseline"
DEFAULT_SENSOR_ID = "smoke_sensor_v1"
REQUEST_TIMEOUT = 15
VERIFY_ATTEMPTS = 10
VERIFY_DELAY_SEC = 1.0


@dataclass
class StepResult:
    status: str
    latency_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = {"status": self.status, "latency_ms": round(self.latency_ms, 1)}
        if self.details:
            payload.update(self.details)
        if self.error:
            payload["error"] = self.error
        return payload


class SmokeRunner:
    def __init__(self, base_url: str, api_key: str, sensor_id: str, model_name: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.sensor_id = sensor_id
        self.model_name = model_name
        self.summary: Dict[str, Any] = {
            "ingest": {},
            "prediction": {},
            "decision": {},
            "metrics": {},
            "overall": "pending",
        }
        self._correlation_id = str(uuid.uuid4())
        self._decision_request_id = f"smoke-{uuid.uuid4()}"

    def run(self) -> bool:
        try:
            ingest = self._ingest()
            if ingest.status not in {"ok", "warn"}:
                return self._fail("ingest", ingest)
            self.summary["ingest"] = ingest.to_dict()

            prediction = self._predict()
            if prediction.status != "ok":
                return self._fail("prediction", prediction)
            self.summary["prediction"] = prediction.to_dict()

            decision = self._submit_decision()
            if decision.status != "ok":
                return self._fail("decision", decision)
            self.summary["decision"] = decision.to_dict()

            metrics = self._fetch_metrics()
            if metrics.status != "ok":
                return self._fail("metrics", metrics)
            self.summary["metrics"] = metrics.to_dict()

            self.summary["overall"] = "pass"
            return True
        except Exception as exc:  # noqa: BLE001
            self.summary["overall"] = "fail"
            self.summary["error"] = f"Unhandled exception: {exc}"
            return False

    def _fail(self, step: str, result: StepResult) -> bool:
        self.summary[step] = result.to_dict()
        self.summary["overall"] = "fail"
        return False

    def _ingest(self) -> StepResult:
        url = f"{self.base_url}/api/v1/data/ingest"
        payload = {
            "sensor_id": self.sensor_id,
            "sensor_type": "temperature",
            "value": round(25 + (time.time() % 5), 3),
            "unit": "C",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": self._correlation_id,
        }
        start = time.perf_counter()
        response = requests.post(url, headers=self.headers, json=payload, timeout=REQUEST_TIMEOUT)
        latency_ms = (time.perf_counter() - start) * 1000
        if response.status_code >= 300:
            return StepResult("fail", latency_ms, error=f"HTTP {response.status_code}: {response.text[:200]}")
        try:
            ingest_body = response.json()
        except ValueError:
            ingest_body = {}

        # Verification loop
        verify_url = f"{self.base_url}/api/v1/sensors/readings"
        attempt = 0
        last_error = None
        while attempt < VERIFY_ATTEMPTS:
            attempt += 1
            params = {
                "limit": 1,
                "sensor_id": self.sensor_id,
            }
            try:
                verify_resp = requests.get(verify_url, headers=self.headers, params=params, timeout=REQUEST_TIMEOUT)
                if verify_resp.status_code == 200:
                    readings = verify_resp.json()
                    if readings:
                        reading = readings[0]
                        if reading.get("sensor_id") == self.sensor_id:
                            return StepResult(
                                "ok",
                                latency_ms,
                                details={
                                    "verification_attempts": attempt,
                                    "event_id": ingest_body.get("event_id"),
                                },
                            )
                    last_error = "Reading not yet available"
                else:
                    last_error = f"HTTP {verify_resp.status_code}: {verify_resp.text[:200]}"
            except requests.RequestException as exc:  # noqa: PERF203
                last_error = str(exc)
            time.sleep(VERIFY_DELAY_SEC)
        details = {
            "verification_attempts": attempt,
            "event_id": ingest_body.get("event_id"),
        }
        return StepResult("warn", latency_ms, details=details, error=last_error or "Verification failed")

    def _predict(self) -> StepResult:
        url = f"{self.base_url}/api/v1/ml/predict"
        payload = {
            "model_name": self.model_name,
            "model_version": "auto",
            "features": {
                "Air_temperature_K": 298.1,
                "Process_temperature_K": 308.6,
                "Rotational_speed_rpm": 1551,
                "Torque_Nm": 42.8,
                "Tool_wear_min": 108,
            },
            "sensor_id": f"prediction-{self.sensor_id}",
            "include_explainability": False,
        }
        start = time.perf_counter()
        response = requests.post(url, headers=self.headers, json=payload, timeout=REQUEST_TIMEOUT)
        latency_ms = (time.perf_counter() - start) * 1000
        if response.status_code >= 300:
            return StepResult("fail", latency_ms, error=f"HTTP {response.status_code}: {response.text[:200]}")
        try:
            body = response.json()
        except ValueError:
            body = {}
        model_version = body.get("model_info", {}).get("model_version") or body.get("model_version")
        return StepResult(
            "ok",
            latency_ms,
            details={
                "model_version": model_version,
                "prediction": body.get("prediction"),
            },
        )

    def _submit_decision(self) -> StepResult:
        url = f"{self.base_url}/api/v1/decisions/submit"
        payload = {
            "request_id": self._decision_request_id,
            "decision": "approved",
            "justification": "Automated smoke validation",
            "operator_id": "smoke_runner",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "confidence": 0.9,
            "additional_notes": "Smoke test submission",
            "correlation_id": self._correlation_id,
        }
        start = time.perf_counter()
        response = requests.post(url, headers=self.headers, json=payload, timeout=REQUEST_TIMEOUT)
        latency_ms = (time.perf_counter() - start) * 1000
        if response.status_code >= 300:
            return StepResult("fail", latency_ms, error=f"HTTP {response.status_code}: {response.text[:200]}")
        try:
            body = response.json()
        except ValueError:
            body = {}
        return StepResult(
            "ok",
            latency_ms,
            details={
                "request_id": body.get("request_id"),
                "operator_id": body.get("operator_id"),
            },
        )

    def _fetch_metrics(self) -> StepResult:
        url = f"{self.base_url}/metrics"
        start = time.perf_counter()
        response = requests.get(url, headers=self.headers, timeout=REQUEST_TIMEOUT)
        latency_ms = (time.perf_counter() - start) * 1000
        if response.status_code >= 300:
            return StepResult("fail", latency_ms, error=f"HTTP {response.status_code}: {response.text[:200]}")
        sample = response.text.splitlines()[:3]
        return StepResult("ok", latency_ms, details={"sample": sample})


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run V1.0 smoke validation flow.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL (default: %(default)s)")
    parser.add_argument("--api-key", required=True, help="API key with required scopes")
    parser.add_argument("--sensor-id", default=DEFAULT_SENSOR_ID, help="Sensor ID for ingestion (default: %(default)s)")
    parser.add_argument("--model-name", default=DEFAULT_MODEL_NAME, help="Model name for prediction (default: %(default)s)")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> None:
    args = parse_args(argv)
    runner = SmokeRunner(args.base_url, args.api_key, args.sensor_id, args.model_name)
    success = runner.run()
    print(json.dumps(runner.summary, indent=2))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
