"""Unified safe rerun helper for Streamlit versions.

Usage:
    from lib.rerun import safe_rerun
    safe_rerun()

Implements a no-op if neither st.rerun nor st.experimental_rerun is available,
preventing AttributeError crashes in stripped-down or future Streamlit builds.
"""
from __future__ import annotations

import streamlit as st  # type: ignore


def safe_rerun() -> None:
    """Attempt to trigger a rerun if the API supports it.

    Falls back gracefully (no exception) when running in an environment where
    both rerun mechanisms are unavailable.
    """
    if hasattr(st, "rerun"):
        try:
            st.rerun()  # type: ignore[attr-defined]
        except Exception:
            pass
    elif hasattr(st, "experimental_rerun"):
        try:
            st.experimental_rerun()  # type: ignore[attr-defined]
        except Exception:
            pass
    else:
        # No supported rerun API; silently ignore.
        return
