"""Minimal app shell for Smart Maintenance SaaS UI.

Previous monolith removed. Feature pages (explorer, decisions, prediction, metrics)
will live in `ui/pages/`.
"""

from datetime import datetime, timezone
import os
import uuid
import time
import streamlit as st

from lib.api_client import make_api_request

st.set_page_config(page_title="Smart Maintenance SaaS", page_icon="🔧", layout="wide")


def render_sidebar() -> None:
    with st.sidebar:
        st.header("🔗 Status")
        env = os.getenv("DEPLOYMENT_ENV", "local").upper()
        st.caption(f"Environment: {env}")
        health = make_api_request("GET", "/health")
        if health.get("success"):
            st.success("Backend OK")
        else:
            st.error("Backend DOWN")
            st.caption(health.get("error", "unavailable"))
        st.markdown("---")
        st.caption("Pages load from ui/pages/. Refactor ongoing.")


def render_overview() -> None:
    st.title("🔧 Smart Maintenance SaaS – Overview")
    st.write("Lean shell. Use sidebar to navigate feature pages as they arrive.")
    st.subheader("📥 Manual Sensor Ingestion")
    with st.form("ingest_form"):
        c1, c2, c3, c4 = st.columns([1.4,1,1,1])
        with c1:
            sensor_id = st.text_input("Sensor ID", value="SENSOR_001")
        with c2:
            value = st.number_input("Value", value=25.5)
        with c3:
            sensor_type = st.selectbox("Type", ["temperature","vibration","pressure"], index=0)
        with c4:
            unit = st.text_input("Unit", value="°C")
        submit = st.form_submit_button("📤 Submit", use_container_width=True)
    if submit:
        wall_start = time.perf_counter()
        start = datetime.now(timezone.utc)
        payload = {
            "sensor_id": sensor_id,
            "value": value,
            "timestamp": start.isoformat(),
            "sensor_type": sensor_type,
            "unit": unit,
            "correlation_id": str(uuid.uuid4()),
        }
        resp = make_api_request("POST", "/api/v1/data/ingest", json_data=payload)
        post_latency_ms = (time.perf_counter() - wall_start) * 1000
        if resp.get("success"):
            verify_start = time.perf_counter()
            verify = make_api_request("GET", "/api/v1/sensors/readings", params={"limit":1, "sensor_id": sensor_id})
            verify_latency_ms = (time.perf_counter() - verify_start) * 1000
            end_to_end_ms = (time.perf_counter() - wall_start) * 1000
            st.success(f"Accepted • POST {post_latency_ms:.0f} ms • Verify {verify_latency_ms:.0f} ms • E2E {end_to_end_ms:.0f} ms")
            if verify.get("success") and verify.get("data"):
                with st.expander("Latest Persisted Reading", expanded=True):
                    st.json(verify["data"][0])
            else:
                st.warning("Verification returned no row yet (eventual consistency).")
        else:
            st.error("Ingestion failed")
            st.caption(resp.get("error", "Unknown error"))
    st.caption("✅ Shell active. Additional capabilities moving to dedicated pages.")


def main() -> None:  # pragma: no cover
    render_sidebar()
    render_overview()


if __name__ == "__main__":  # pragma: no cover
    main()
