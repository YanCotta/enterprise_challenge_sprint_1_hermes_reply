"""Utilities for API key management shared across API, UI, and tests."""

from __future__ import annotations

import os
from typing import Iterable, List, Set

from core.config.settings import settings

API_KEY_HEADER_NAME = "X-API-Key"
PLACEHOLDER_API_KEY = "your_default_api_key"


def _dedupe_preserve_order(values: Iterable[str]) -> List[str]:
    """Return a list with duplicates removed while preserving input order."""
    seen: Set[str] = set()
    ordered: List[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def get_configured_api_keys() -> List[str]:
    """Return the configured API keys in priority order (primary first)."""
    candidates: List[str] = []

    # 1. Explicit single-key overrides
    env_single = os.getenv("API_KEY")
    if env_single:
        candidates.append(env_single.strip())

    if settings.API_KEY and settings.API_KEY not in (PLACEHOLDER_API_KEY, ""):
        candidates.append(settings.API_KEY.strip())

    # 2. Comma-separated collections from environment
    for env_var in ("API_KEYS", "ALLOWED_API_KEYS"):
        raw_list = os.getenv(env_var)
        if not raw_list:
            continue
        parsed = [part.strip() for part in raw_list.split(",")]
        candidates.extend(filter(None, parsed))

    # 3. Fall back to placeholder only if no real keys were provided
    deduped = _dedupe_preserve_order(candidates)
    if deduped:
        return deduped

    return [PLACEHOLDER_API_KEY]


def load_allowed_api_keys(additional: Iterable[str] | None = None) -> Set[str]:
    """Return the full set of API keys the service should accept."""
    keys = set(get_configured_api_keys())

    if additional:
        for key in additional:
            if key:
                keys.add(key)

    return keys


def get_preferred_api_key() -> str:
    """Return the first configured API key (placeholder if none provided)."""
    return get_configured_api_keys()[0]
