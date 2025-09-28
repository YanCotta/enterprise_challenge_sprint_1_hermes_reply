"""Centralized resilient API client for Streamlit UI.
Provides standardized request handling, retries, timeout management,
error normalization, and future caching hooks.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple

import os
import requests
import streamlit as st

# Robust configuration resolution order:
# 1. Environment variables (API_BASE_URL, API_KEY)
# 2. Streamlit secrets (if present and readable)
# 3. Safe defaults (internal Docker network target + dev key placeholder)

def _resolve_config():
    env_base = os.getenv("API_BASE_URL")
    env_key = os.getenv("API_KEY")
    secrets_base = None
    secrets_key = None
    try:
        if hasattr(st, "secrets"):
            secrets_base = st.secrets.get("API_BASE_URL")  # type: ignore
            secrets_key = st.secrets.get("API_KEY")  # type: ignore
    except Exception:
        pass
    api_base = env_base or secrets_base or "http://api:8000"
    api_key = env_key or secrets_key or "your_default_api_key"
    return api_base, api_key

API_BASE_URL, API_KEY = _resolve_config()

# Latency registry (in-memory, rolling)
_LATENCY_REGISTRY: list[Dict[str, Any]] = []
_LATENCY_MAX = 200

def record_latency(label: str, ms: float, meta: Optional[Dict[str, Any]] = None) -> None:
    entry = {"label": label, "ms": ms, "t": time.time()}
    if meta:
        entry.update(meta)
    _LATENCY_REGISTRY.append(entry)
    if len(_LATENCY_REGISTRY) > _LATENCY_MAX:
        del _LATENCY_REGISTRY[:-_LATENCY_MAX]

# Backwards compatibility alias expected by newer UI pages / simulation console
def record_latency_sample(label: str, ms: float, **meta: Any) -> None:
    """Convenience wrapper used by Simulation Console.

    Mirrors legacy naming (record_latency_sample) while delegating to the
    canonical record_latency implementation. Accepts arbitrary keyword meta
    which will be merged into the stored latency entry.
    """
    extra: Dict[str, Any] = dict(meta) if meta else {}
    record_latency(label, ms, extra if extra else None)

def get_latency_samples() -> list[Dict[str, Any]]:
    return list(_LATENCY_REGISTRY)

DEFAULT_TIMEOUT = 20
DEFAULT_RETRIES = 3

HEADERS = {
    "accept": "application/json",
    "X-API-Key": API_KEY,
}

# --- Debug / diagnostics helpers -------------------------------------------------

def get_current_api_config() -> Dict[str, str]:
    """Return the resolved API configuration for debug display in the UI."""
    return {
        "API_BASE_URL": API_BASE_URL,
        "API_KEY_SET": "yes" if API_KEY and API_KEY != "your_default_api_key" else "default/placeholder",
        "TIMEOUT_DEFAULT": str(DEFAULT_TIMEOUT),
        "RETRIES_DEFAULT": str(DEFAULT_RETRIES),
    }

def probe_connectivity(path: str = "/health", timeout: int = 5) -> Dict[str, Any]:
    """Low-level single attempt connectivity probe (no retries, minimal surface)."""
    url = f"{API_BASE_URL}{path}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        return {"ok": r.status_code == 200, "status": r.status_code, "text": r.text[:200]}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e), "url": url}

# -------------------------------------------------------------------------------

def _format_error(prefix: str, detail: Optional[str]) -> str:
    if detail and isinstance(detail, str):
        return f"{prefix} - {detail}"
    return prefix


def make_api_request(
    method: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    backoff_base: float = 2.0,
) -> Dict[str, Any]:
    """Perform a resilient API request."""
    # Allow caller to provide full URL (if endpoint already absolute)
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        url = endpoint
    else:
        url = f"{API_BASE_URL}{endpoint}"
    attempt = 0
    while attempt < retries:
        try:
            req_start = time.perf_counter()
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=HEADERS,
                params=params,
                json=json_data,
                timeout=timeout,
            )
            elapsed_ms = (time.perf_counter() - req_start) * 1000
            if 200 <= response.status_code < 300:
                try:
                    data = response.json()
                except ValueError:
                    data = {"raw": response.text}
                record_latency(endpoint, elapsed_ms, {"status": response.status_code})
                return {"success": True, "data": data, "status_code": response.status_code, "latency_ms": elapsed_ms}

            err_msg = f"HTTP {response.status_code} {response.reason}".strip()
            try:
                detail = response.json().get("detail")
                if isinstance(detail, (str, list, dict)):
                    err_msg = _format_error(err_msg, str(detail))
            except ValueError:
                pass
            record_latency(endpoint, elapsed_ms, {"status": response.status_code, "error": True})
            return format_error_with_hint({"success": False, "error": err_msg, "status_code": response.status_code})

        except requests.exceptions.Timeout:
            attempt += 1
            if attempt >= retries:
                return format_error_with_hint({"success": False, "error": f"Timeout after {timeout}s (attempts={retries})"})
            sleep_for = backoff_base ** (attempt - 1)
            st.warning(f"Request timeout. Retrying in {sleep_for:.1f}s ({attempt}/{retries}) ...")
            time.sleep(sleep_for)
        except requests.exceptions.ConnectionError as e:
            attempt += 1
            if attempt >= retries:
                return format_error_with_hint({"success": False, "error": f"Connection error after {retries} attempts: {e}"})
            sleep_for = backoff_base ** (attempt - 1)
            st.warning(f"Connection error. Retrying in {sleep_for:.1f}s ({attempt}/{retries}) ...")
            time.sleep(sleep_for)
        except requests.exceptions.RequestException as e:  # Catch-all for Requests
            return format_error_with_hint({"success": False, "error": f"Request exception: {e}"})

    return format_error_with_hint({"success": False, "error": "Unknown failure after retries"})


def make_long_api_request(
    method: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = 60,
) -> Dict[str, Any]:
    return make_api_request(
        method=method,
        endpoint=endpoint,
        params=params,
        json_data=json_data,
        timeout=timeout,
        retries=1,
    )


def annotate_latency(start_time: float, end_time: float) -> float:
    return (end_time - start_time) * 1000.0


def health_ping() -> Dict[str, Any]:
    return make_api_request("GET", "/health")

# ---------------- Error Guidance Layer (B2) -----------------

_ERROR_PATTERNS: Tuple[Tuple[str, str], ...] = (
    ("model not found", "Check model name or confirm registry availability (Model Metadata page)."),
    ("no models found", "No registered models – add one or re-enable MLflow."),
    ("feature mismatch", "Verify feature names/types; align with training schema."),
    ("missing required", "Verify feature names/types; align with training schema."),
    ("timeout", "Temporary connectivity issue – retry or confirm API base URL."),
    ("connection error", "Temporary connectivity issue – retry or confirm API base URL."),
    ("failed to establish a new connection", "Temporary connectivity issue – retry or confirm API base URL."),
    ("validation error", "Input payload failed validation. Check required fields and types."),
    ("permission", "Your API key may lack required scope. Confirm credentials."),
    ("unsupported media type", "The server rejected the content type. Ensure JSON body and headers are correct."),
    ("rate limit", "Too many requests in a short time. Slow down or check rate limit configuration."),
    ("database", "A database error occurred. Check backend logs for detail (migration/state issue)."),
    ("ssl", "SSL parameter mismatch or certificate issue. Inspect DATABASE_URL normalization & network config."),
)

def map_error_to_hint(message: Optional[str]) -> Optional[str]:
    if not message or not isinstance(message, str):
        return None
    lower = message.lower()
    for needle, hint in _ERROR_PATTERNS:
        if needle in lower:
            return hint
    return None

def format_error_with_hint(result: Dict[str, Any]) -> Dict[str, Any]:
    """Augment result dict with 'hint' if an error pattern matches."""
    if result.get("success"):
        return result
    hint = map_error_to_hint(result.get("error"))
    if hint:
        result["hint"] = hint
    return result

