"""Centralized resilient API client for Streamlit UI.
Provides standardized request handling, retries, timeout management,
error normalization, and future caching hooks.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

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
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=HEADERS,
                params=params,
                json=json_data,
                timeout=timeout,
            )
            if 200 <= response.status_code < 300:
                try:
                    data = response.json()
                except ValueError:
                    data = {"raw": response.text}
                return {"success": True, "data": data, "status_code": response.status_code}

            err_msg = f"HTTP {response.status_code} {response.reason}".strip()
            try:
                detail = response.json().get("detail")
                if isinstance(detail, (str, list, dict)):
                    err_msg = _format_error(err_msg, str(detail))
            except ValueError:
                pass
            return {"success": False, "error": err_msg, "status_code": response.status_code}

        except requests.exceptions.Timeout:
            attempt += 1
            if attempt >= retries:
                return {"success": False, "error": f"Timeout after {timeout}s (attempts={retries})"}
            sleep_for = backoff_base ** (attempt - 1)
            st.warning(f"Request timeout. Retrying in {sleep_for:.1f}s ({attempt}/{retries}) ...")
            time.sleep(sleep_for)
        except requests.exceptions.ConnectionError as e:
            attempt += 1
            if attempt >= retries:
                return {"success": False, "error": f"Connection error after {retries} attempts: {e}"}
            sleep_for = backoff_base ** (attempt - 1)
            st.warning(f"Connection error. Retrying in {sleep_for:.1f}s ({attempt}/{retries}) ...")
            time.sleep(sleep_for)
        except requests.exceptions.RequestException as e:  # Catch-all for Requests
            return {"success": False, "error": f"Request exception: {e}"}

    return {"success": False, "error": "Unknown failure after retries"}


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

# Future extension points (stubs):
# - cache_model_versions(model_name)
# - cache_sensor_list()
# - map_error_to_hint(error_message)
