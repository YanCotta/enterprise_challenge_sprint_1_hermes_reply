import time
from datetime import datetime, timezone
import streamlit as st

from lib.api_client import make_api_request

st.set_page_config(page_title="Prediction", page_icon="🤖")


def _auto_resolve_version(model_name: str) -> str | None:
    """Attempt to resolve latest version for a model.
    Tries explicit latest endpoint first; falls back to versions list.
    Returns version string or None if not resolvable.
    """
    if not model_name:
        return None
    latest = make_api_request("GET", f"/api/v1/ml/models/{model_name}/latest")
    if latest.get("success") and latest.get("data"):
        data = latest["data"]
        version = data.get("version") or data.get("latest_version")
        if version:
            return str(version)
    versions = make_api_request("GET", f"/api/v1/ml/models/{model_name}/versions")
    if versions.get("success") and versions.get("data"):
        try:
            vs = versions["data"]
            # Expect list of dicts with 'version' key
            parsed = [int(v.get("version")) for v in vs if str(v.get("version", "")).isdigit()]
            if parsed:
                return str(max(parsed))
        except Exception:
            pass
    return None


def render_prediction_page():
    st.header("🤖 Model Prediction")
    st.caption("Supply features and optionally leave version blank for auto-resolution.")

    with st.form("prediction_form"):
        model_name = st.text_input("Model Name", value="ai4i_classifier_randomforest_baseline")
        version = st.text_input("Version (blank = auto)", value="")
        explain = st.checkbox("Include SHAP Explainability", value=False, help="May increase latency")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            air_temp = st.number_input("Air_temperature_K", value=298.1)
        with col2:
            proc_temp = st.number_input("Process_temperature_K", value=308.6)
        with col3:
            rpm = st.number_input("Rotational_speed_rpm", value=1551)
        with col4:
            torque = st.number_input("Torque_Nm", value=42.8)
        with col5:
            wear = st.number_input("Tool_wear_min", value=108)
        submitted = st.form_submit_button("⚡ Predict", use_container_width=True)

    if submitted:
        resolved_version = version.strip() or _auto_resolve_version(model_name)
        if not resolved_version:
            st.error("Could not resolve model version. Please specify explicitly.")
            return
        st.info(f"Using version: {resolved_version}")
        payload = {
            "model_name": model_name,
            "model_version": resolved_version,
            "features": {
                "Air_temperature_K": air_temp,
                "Process_temperature_K": proc_temp,
                "Rotational_speed_rpm": rpm,
                "Torque_Nm": torque,
                "Tool_wear_min": wear,
            },
            "sensor_id": "prediction_demo_sensor_001",
            "include_explainability": explain,
        }
        t0 = time.perf_counter()
        resp = make_api_request("POST", "/api/v1/ml/predict", json_data=payload)
        latency_ms = (time.perf_counter() - t0) * 1000
        if resp.get("success"):
            data = resp["data"]
            st.success(f"Prediction completed in {latency_ms:.0f} ms")
            colA, colB = st.columns([1,2])
            with colA:
                st.metric("Prediction", data.get("prediction"))
                st.metric("Confidence", f"{data.get('confidence', data.get('prediction_confidence','?'))}")
                st.caption(f"Model: {model_name} v{resolved_version}")
            with colB:
                with st.expander("Raw Response", expanded=False):
                    st.json(data)
            if explain and "explainability" in data:
                with st.expander("Explainability (SHAP)"):
                    st.json(data["explainability"])
        else:
            st.error("Prediction failed")
            st.caption(resp.get("error", "Unknown error"))


render_prediction_page()