import streamlit as st
import time
import logging
from datetime import datetime, timedelta

from lib.api_client import make_api_request
from lib.rerun import safe_rerun

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
    if "demo_start_time" not in st.session_state:
        st.session_state.demo_start_time = None
    if "demo_terminal_state" not in st.session_state:
        st.session_state.demo_terminal_state = None
    if "demo_terminal_reason" not in st.session_state:
        st.session_state.demo_terminal_reason = None

    # Demo timeout configuration (90 seconds max runtime)
    MAX_DEMO_RUNTIME_SECONDS = 90

    if st.session_state.demo_terminal_state and not st.session_state.demo_running:
        cid = st.session_state.get("correlation_id") or "unknown"
        reason = st.session_state.get("demo_terminal_reason")
        state = st.session_state.demo_terminal_state
        if state == "success":
            st.success(f"Completed Successfully – correlation_id={cid}")
        elif state == "timeout":
            detail = reason or f"Demo exceeded {MAX_DEMO_RUNTIME_SECONDS}s. Retry or inspect event bus." 
            st.warning(f"Timed Out – correlation_id={cid}. {detail}")
        elif state == "failed":
            message = f"Failed – correlation_id={cid}"
            if reason:
                message += f" (reason: {reason})"
            st.error(message)

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
                    st.session_state.demo_start_time = datetime.now()
                    st.session_state.demo_terminal_state = None
                    st.session_state.demo_terminal_reason = None
                    safe_rerun()
                else:
                    st.error("Failed to start the demo.")
                    st.error(start_result.get("error", "Unknown error."))

    if not st.session_state.demo_running and st.session_state.correlation_id:
        st.info("Previous demo complete. Start a new one to see live updates.")

    if st.session_state.demo_running and st.session_state.correlation_id:
        status_url = f"/api/v1/demo/golden-path/status/{st.session_state.correlation_id}"
        status_result = make_api_request("GET", status_url)
        if not status_result.get("success"):
            error_msg = status_result.get("error", "Status endpoint unavailable")
            st.session_state.demo_running = False
            st.session_state.demo_terminal_state = "failed"
            st.session_state.demo_terminal_reason = error_msg
            st.error("Failed to fetch demo status. It may have expired or the backend is unavailable.")
            st.error(error_msg)
            return
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
                st.success(f"Completed Successfully – correlation_id={st.session_state.correlation_id}")
                st.session_state.demo_terminal_state = "success"
                st.session_state.demo_terminal_reason = None
            elif overall == "failed":
                failure_reason = None
                if data.get("errors"):
                    failure_reason = data["errors"]
                    if isinstance(failure_reason, list):
                        failure_reason = "; ".join(str(e) for e in failure_reason[:3])
                st.error(f"Failed – correlation_id={st.session_state.correlation_id}")
                if failure_reason:
                    st.caption(f"Reason: {failure_reason}")
                st.session_state.demo_terminal_state = "failed"
                st.session_state.demo_terminal_reason = failure_reason

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

            st.markdown("**Maintenance Schedule Feed**")
            feed_resp = make_api_request(
                "GET",
                "/api/v1/maintenance/scheduled",
                params={
                    "limit": 5,
                    "correlation_id": st.session_state.correlation_id,
                },
            )
            if feed_resp.get("success"):
                schedules = feed_resp.get("data") or []
                if schedules:
                    for record in schedules:
                        header = (
                            f"{record.get('status', 'Scheduled')} – Start: {record.get('scheduled_start_time', 'pending')}"
                        )
                        with st.expander(header):
                            st.json(record)
                else:
                    st.info("No maintenance schedules recorded yet for this run.")
            else:
                st.warning("Unable to load maintenance schedule feed for this correlation ID.")

        # Auto refresh while running with timeout protection
        current_status = data.get("status")
        if current_status not in ("complete", "failed"):
            # Check for stale timeout
            if st.session_state.demo_start_time:
                elapsed = datetime.now() - st.session_state.demo_start_time
                elapsed_seconds = elapsed.total_seconds()
                
                if elapsed_seconds > MAX_DEMO_RUNTIME_SECONDS:
                    st.warning(f"Timed Out – correlation_id={st.session_state.correlation_id}. Demo exceeded {MAX_DEMO_RUNTIME_SECONDS}s; status may be stale or incomplete.")
                    st.session_state.demo_terminal_state = "timeout"
                    st.session_state.demo_terminal_reason = None
                    st.session_state.demo_running = False
                    st.session_state.correlation_id = st.session_state.correlation_id  # keep for viewing
                else:
                    # Continue polling - show progress
                    remaining = MAX_DEMO_RUNTIME_SECONDS - int(elapsed_seconds)
                    progress_value = elapsed_seconds / MAX_DEMO_RUNTIME_SECONDS
                    
                    # Display progress bar and time remaining
                    st.progress(progress_value, text=f"Demo in progress... ({int(elapsed_seconds)}s / {MAX_DEMO_RUNTIME_SECONDS}s)")
                    st.caption(f"⏱ Elapsed: {int(elapsed_seconds)}s | Timeout in: {remaining}s | Auto-refreshing every 2s...")
                    
                    time.sleep(2)
                    safe_rerun()
            else:
                # Fallback: no start time recorded, continue with limited retries
                time.sleep(2)
                safe_rerun()
        else:
            st.session_state.demo_running = False
            st.session_state.correlation_id = st.session_state.correlation_id  # keep for viewing


render_golden_path_page()