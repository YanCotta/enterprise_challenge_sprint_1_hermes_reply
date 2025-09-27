import time
from datetime import datetime, timezone
import streamlit as st
import requests

from lib.api_client import make_api_request, get_latency_samples
from lib.rerun import safe_rerun

st.set_page_config(page_title="Metrics Overview", page_icon="📊")

REFRESH_INTERVAL_SEC = 30

def _fetch_prometheus_metrics(raw_limit: int = 5000) -> str:
    resp = make_api_request("GET", "/metrics", timeout=10, retries=1)
    if resp.get("success") and isinstance(resp.get("data"), dict):
        # If API attempts JSON; convert to text lines
        return "\n".join(f"{k} {v}" for k, v in resp["data"].items())
    if resp.get("success") and isinstance(resp.get("data"), str):
        # Some setups may already return raw text; keep manageable length
        return resp["data"][:raw_limit]
    return f"ERROR: {resp.get('error')}" + (f"\nHINT: {resp.get('hint')}" if resp.get('hint') else "")


def render_metrics_overview():
    st.header("📊 Metrics Snapshot")
    if 'metrics_last_refresh' not in st.session_state:
        st.session_state.metrics_last_refresh = None

    top_col1, top_col2, top_col3 = st.columns([2,1,1])
    with top_col1:
        st.caption("Snapshot view. Not streaming; use Refresh or wait auto-update.")
    with top_col2:
        if st.button("🔄 Refresh Now"):
            st.session_state.metrics_last_refresh = None
    with top_col3:
        auto = st.toggle("Auto Refresh 30s", value=True, help="Periodically refresh this snapshot")

    need_fetch = st.session_state.metrics_last_refresh is None or (
        auto and (datetime.now(timezone.utc) - st.session_state.metrics_last_refresh).total_seconds() > REFRESH_INTERVAL_SEC
    )

    if need_fetch:
        with st.spinner("Loading metrics..."):
            metrics_text = _fetch_prometheus_metrics()
            st.session_state.metrics_cache = metrics_text
            st.session_state.metrics_last_refresh = datetime.now(timezone.utc)
    else:
        metrics_text = st.session_state.get('metrics_cache', 'No data yet.')

    ts = st.session_state.metrics_last_refresh.isoformat() if st.session_state.metrics_last_refresh else "—"
    st.write(f"**Last Updated:** {ts}")

    # Quick derived stats (rudimentary extraction)
    if isinstance(metrics_text, str):
        lines = [l for l in metrics_text.splitlines() if l and not l.startswith('#')]
        total_lines = len(lines)
        request_lines = [l for l in lines if 'http_requests_total' in l]
        st.metric("Metric Lines", total_lines)
        st.metric("HTTP Counters", len(request_lines))

    with st.expander("Raw Metrics (truncated)", expanded=False):
        st.text(metrics_text)

    st.subheader("Recent Request Latencies")
    samples = get_latency_samples()
    if not samples:
        st.write("No latency samples recorded yet.")
    else:
        last = samples[-50:]
        avg = sum(s['ms'] for s in last)/len(last)
        st.write(f"Last {len(last)} avg: {avg:.1f} ms")
        st.table([{"endpoint": s['label'], "ms": f"{s['ms']:.0f}", "status": s.get('status')} for s in reversed(last)])

    if auto:
        safe_rerun()


render_metrics_overview()