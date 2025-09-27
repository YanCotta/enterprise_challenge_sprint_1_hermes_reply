import streamlit as st
import time
import logging

from lib.api_client import make_api_request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _status_icon(step_status: str) -> str:
    return {
        "pending": "⏳",
        "running": "⚙️",
        "complete": "✅",
        "failed": "❌",
    }.get(step_status, "⏳")


def render_golden_path_page():
    """Renders the Golden Path Demo page with live multi-agent event stream."""
    st.header("🏆 Golden Path Demo – Live Multi-Agent Pipeline")
    st.caption("Shows real-time event bus activity across agents using a shared correlation ID.")

    if "demo_running" not in st.session_state:
        st.session_state.demo_running = False
    if "correlation_id" not in st.session_state:
        st.session_state.correlation_id = None

    col_launch, col_opts = st.columns([2, 3])
    with col_opts:
        sensor_events = st.slider("Sensor Events", 5, 100, 20, help="How many synthetic sensor events to seed")
        include_decision = st.checkbox("Include human decision stage", value=False)
    with col_launch:
        if st.button("🚀 Start Golden Path Demo", type="primary", disabled=st.session_state.demo_running):
            with st.spinner("Initiating demo..."):
                params = {"sensor_events": sensor_events, "include_decision": str(include_decision).lower()}
                start_result = make_api_request("POST", "/api/v1/demo/golden-path", params=params)
                if start_result.get("success"):
                    st.session_state.correlation_id = start_result["data"]["correlation_id"]
                    st.session_state.demo_running = True
                    st.experimental_rerun()
                else:
                    st.error("Failed to start the demo.")
                    st.error(start_result.get("error", "Unknown error."))

    if not st.session_state.demo_running and st.session_state.correlation_id:
        st.info("Previous demo complete. Start a new one to see live updates.")

    if st.session_state.demo_running and st.session_state.correlation_id:
        status_url = f"/api/v1/demo/golden-path/status/{st.session_state.correlation_id}"
        status_result = make_api_request("GET", status_url)
        if not status_result.get("success"):
            st.error("Could not fetch demo status. It may have expired.")
            st.session_state.demo_running = False
            st.stop()
        data = status_result["data"]

        tabs = st.tabs(["Pipeline", "Events", "Metrics"])

        # Pipeline Tab
        with tabs[0]:
            st.subheader("Pipeline Steps")
            steps = data.get("steps", [])
            for step in steps:
                icon = _status_icon(step["status"])
                dur = None
                if step.get("started_at") and step.get("completed_at"):
                    try:
                        from datetime import datetime as dt
                        dur = (dt.fromisoformat(step["completed_at"]) - dt.fromisoformat(step["started_at"]))
                    except Exception:
                        pass
                duration_str = f" – {dur.total_seconds():.2f}s" if dur else ""
                st.write(f"{icon} **{step['name'].replace('_',' ').title()}** — {step['status']}{duration_str} (events: {step['events']})\n> {step.get('message','')}")

            overall = data.get("status")
            if overall == "complete":
                st.success("🎉 Pipeline complete")
            elif overall == "failed":
                st.error("Pipeline failed – see Errors in Metrics tab")

        # Events Tab
        with tabs[1]:
            st.subheader("Event Stream (most recent)")
            events = data.get("events", [])
            if not events:
                st.info("No events yet.")
            else:
                # Reverse chronological for display
                for evt in reversed(events[-50:]):
                    with st.expander(f"{evt['event_type']} @ {evt['timestamp']}"):
                        st.json(evt)

        # Metrics Tab
        with tabs[2]:
            st.subheader("Run Metrics")
            metrics = data.get("metrics", {})
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Events", metrics.get("total_events", 0))
            lat = metrics.get("latency_ms_ingest_to_prediction")
            c2.metric("Ingest→Prediction Latency (ms)", lat if lat is not None else "–")
            c3.metric("Status", data.get("status"))
            if data.get("errors"):
                st.error("Errors detected:")
                st.json(data["errors"])

        # Auto refresh while running
        if data.get("status") not in ("complete", "failed"):
            time.sleep(2)
            st.experimental_rerun()
        else:
            st.session_state.demo_running = False
            st.session_state.correlation_id = st.session_state.correlation_id  # keep for viewing


render_golden_path_page()