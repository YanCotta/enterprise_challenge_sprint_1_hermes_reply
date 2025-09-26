# smart-maintenance-saas/ui/pages/1_data_explorer.py
"""Data Explorer page.

Provides a paginated, filterable view of sensor readings using the centralized
API client. Future enhancements: date range filters, server-side sorting, CSV
exports for full dataset, and cached sensor list retrieval.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timezone, time as dtime

from lib.api_client import make_api_request


def _safe_rerun():
    """Compatibility shim for Streamlit rerun across versions."""
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()  # type: ignore[attr-defined]


def render_data_explorer():
    """Render the data explorer page for viewing and filtering sensor readings."""
    st.header("📂 Data Explorer")
    st.caption("Paginated, filterable view over sensor readings.")

    # --- STATE MANAGEMENT ---
    if "data_explorer_offset" not in st.session_state:
        st.session_state.data_explorer_offset = 0
    if "data_explorer_sensors" not in st.session_state:
        st.session_state.data_explorer_sensors = []

    # --- CONTROLS ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        page_size = st.selectbox("Page Size", [25, 50, 100, 250], index=1)
    with c2:
        if not st.session_state.data_explorer_sensors:
            with st.spinner("Loading sensor list..."):
                sensors_resp = make_api_request("GET", "/api/v1/sensors/sensors")
                if sensors_resp["success"] and sensors_resp.get("data"):
                    st.session_state.data_explorer_sensors = ["(all)"] + [s['sensor_id'] for s in sensors_resp['data']]
                else:
                    st.session_state.data_explorer_sensors = ["(all)"]
        sensor_filter = st.selectbox("Filter by Sensor ID", st.session_state.data_explorer_sensors)
    with c3:
        start_date = st.date_input("Start Date", value=None)
    with c4:
        end_date = st.date_input("End Date", value=None)

    refresh_col = st.columns([1,3,3,3])[0]
    with refresh_col:
        if st.button("↻ Refresh"):
            st.session_state.data_explorer_offset = 0
            _safe_rerun()

    # --- DATA FETCHING ---
    params = {"limit": page_size, "offset": st.session_state.data_explorer_offset}
    if sensor_filter != "(all)":
        params["sensor_id"] = sensor_filter
    if start_date:
        start_ts = datetime.combine(start_date, dtime.min).replace(tzinfo=timezone.utc)
        params["start_ts"] = start_ts.isoformat()
    if end_date:
        end_ts = datetime.combine(end_date, dtime.max).replace(tzinfo=timezone.utc)
        params["end_ts"] = end_ts.isoformat()

    with st.spinner("Fetching sensor readings..."):
        readings_result = make_api_request("GET", "/api/v1/sensors/readings", params=params)

    # --- DISPLAY ---
    if readings_result["success"]:
        rows = readings_result["data"]
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)

            # --- PAGINATION ---
            pcol1, pcol2, pcol3 = st.columns([1, 1, 1])
            with pcol1:
                if st.button("⬅️ Previous", disabled=(st.session_state.data_explorer_offset == 0)):
                    st.session_state.data_explorer_offset -= page_size
                    _safe_rerun()
            with pcol2:
                st.write(f"Page {st.session_state.data_explorer_offset // page_size + 1}")
            with pcol3:
                if st.button("Next ➡️", disabled=(len(rows) < page_size)):
                    st.session_state.data_explorer_offset += page_size
                    _safe_rerun()
        else:
            st.info("No more data found for the current selection.")
    else:
        st.error("Failed to load sensor readings.")
        st.error(readings_result.get("error", "An unknown error occurred."))


if __name__ == "__main__":  # pragma: no cover
    st.set_page_config(layout="wide")
    render_data_explorer()
