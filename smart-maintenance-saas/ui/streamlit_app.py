"""Manual Sensor Ingestion page for Smart Maintenance SaaS UI.

This page provides manual sensor data ingestion with verification.
Other feature pages (explorer, decisions, prediction, metrics) live in `ui/pages/`.
"""

from datetime import datetime, timezone
import os
import uuid
import time
import streamlit as st

from lib.api_client import make_api_request, get_latency_samples
from lib.i18n_translations import get_translation, help_tooltip, bilingual_text

st.set_page_config(page_title="Manual Sensor Ingestion", page_icon="📡", layout="wide")


def _env_badge(env: str) -> str:
    color_map = {
        "LOCAL": "🟢",
        "CONTAINER": "🟦",
        "CLOUD": "☁️",
        "STAGING": "🟡",
        "PROD": "🔴",
    }
    return f"{color_map.get(env, '🔘')} {env}"

def render_sidebar() -> None:
    with st.sidebar:
        st.header("🔗 Status")
        raw_env = os.getenv("DEPLOYMENT_ENV", "local")
        env = raw_env.upper()
        st.markdown(f"**Environment:** {_env_badge(env)}")
        health = make_api_request("GET", "/health")
        if health.get("success"):
            st.success("Backend OK")
        else:
            st.error("Backend DOWN")
            st.caption(health.get("error", "unavailable"))
        st.markdown("---")
        st.caption("Pages load from ui/pages/. Refactor ongoing.")


def render_overview() -> None:
    st.title(get_translation("manual_ingestion", "page_title", "en"))
    st.caption(get_translation("manual_ingestion", "description", "en"))
    with st.expander("ℹ️ Ajuda / Help"):
        st.write(f"**🇧🇷 PT:** {get_translation('manual_ingestion', 'description', 'pt')}")
    st.subheader("📥 Manual Sensor Ingestion")
    with st.form("ingest_form"):
        c1, c2, c3, c4 = st.columns([1.4,1,1,1])
        with c1:
            sensor_id = st.text_input(
                get_translation("manual_ingestion", "sensor_id_label", "en"),
                value="SENSOR_001",
                help=bilingual_text("manual_ingestion", "sensor_id_help")
            )
        with c2:
            value = st.number_input(
                get_translation("manual_ingestion", "value_label", "en"),
                value=25.5,
                help=bilingual_text("manual_ingestion", "value_help")
            )
        with c3:
            sensor_type = st.selectbox(
                get_translation("manual_ingestion", "sensor_type_label", "en"),
                ["temperature","vibration","pressure"],
                index=0,
                help=bilingual_text("manual_ingestion", "sensor_type_help")
            )
        with c4:
            unit = st.text_input(
                get_translation("manual_ingestion", "unit_label", "en"),
                value="°C",
                help=bilingual_text("manual_ingestion", "unit_help")
            )
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
    with st.expander("Recent Latency Samples (last 10)", expanded=False):
        samples = get_latency_samples()[-10:]
        if not samples:
            st.write("No samples yet.")
        else:
            for s in reversed(samples):
                st.write(f"{s['label']} – {s['ms']:.0f} ms (status={s.get('status')})")
    st.caption("✅ Shell active. Additional capabilities moving to dedicated pages.")


def main() -> None:  # pragma: no cover
    render_sidebar()
    render_overview()


if __name__ == "__main__":  # pragma: no cover
    main()
