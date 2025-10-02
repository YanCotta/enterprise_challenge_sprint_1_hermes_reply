import streamlit as st
import os
import pandas as pd
from datetime import datetime

from lib.api_client import make_api_request
from lib.rerun import safe_rerun
from lib.i18n_translations import get_translation, bilingual_text

st.set_page_config(page_title="Model Metadata", page_icon="🧬")


def _deprecated_local_rerun():  # retained temporarily in case of stray imports
    from lib.rerun import safe_rerun as _sr
    _sr()


@st.cache_data(ttl=300)
def _cached_registered_models():
    """Cache raw API response to preserve success/error context."""
    resp = make_api_request("GET", "/api/v1/ml/models")
    # API returns {"models": [...], "count": N} on success
    if resp.get("success") and resp.get("data"):
        # Extract the models array from the response
        data = resp["data"]
        if isinstance(data, dict) and "models" in data:
            return {"success": True, "data": data["models"], "error": None}
        # Fallback if data is already a list
        elif isinstance(data, list):
            return {"success": True, "data": data, "error": None}
    return resp


@st.cache_data(ttl=300)
def _cached_model_versions(model_name: str):
    """Cache raw API response for per-model versions."""
    return make_api_request("GET", f"/api/v1/ml/models/{model_name}/versions")


def _human_ts(ts):
    try:
        return datetime.fromtimestamp(int(ts)/1000).isoformat() if isinstance(ts, (int,float)) else str(ts)
    except Exception:
        return str(ts)


def render_model_metadata():
    st.header(get_translation("model_metadata", "page_title", "en"))
    st.caption(get_translation("model_metadata", "description", "en"))
    with st.expander("ℹ️ Ajuda / Help"):
        st.write(f"**🇧🇷 PT:** {get_translation('model_metadata', 'description', 'pt')}")

    # Feature flag / env guard for disabled MLflow
    state_box = st.container()
    mlflow_disabled = os.getenv("DISABLE_MLFLOW_MODEL_LOADING", "false").lower() in ("1", "true", "yes")
    if mlflow_disabled:
        state_box.info("Disabled – MLflow model loading is turned off via DISABLE_MLFLOW_MODEL_LOADING.")
        return

    col1, col2 = st.columns([2,1])
    with col2:
        if st.button("🔄 Refresh Cache", help="Clears local cache and refetches"):
            _cached_registered_models.clear()
            safe_rerun()

    response = _cached_registered_models()
    if not response.get("success"):
        error_msg = response.get("error", "Unknown error")
        hint = response.get("hint")
        details = f"Error – {error_msg}"
        if hint:
            details += f"\nHint: {hint}"
        state_box.error(details)
        return

    models = response.get("data") or []
    if not models:
        health_result = make_api_request("GET", "/api/v1/ml/health")
        if health_result.get("success"):
            state_box.warning("Empty Registry – No models found in MLflow. Add a model to populate this view.")
        else:
            err = health_result.get("error", "Unknown error")
            hint = health_result.get("hint")
            text = f"Error – Unable to reach MLflow: {err}"
            if hint:
                text += f"\nHint: {hint}"
            state_box.error(text)
        return

    state_box.success("Populated – Models available (cached for 5 minutes).")

    df = pd.DataFrame(models)
    # Normalize timestamps if present
    for col in [c for c in df.columns if 'timestamp' in c]:
        df[col] = df[col].apply(_human_ts)

    st.subheader("Registered Models")
    st.dataframe(df[[c for c in df.columns if c not in ('tags','version_tags')]], use_container_width=True, height=300)

    with st.expander("Raw Tags Table"):
        tag_rows = []
        for m in models:
            base_tags = m.get('tags', {}) or {}
            ver_tags = m.get('version_tags', {}) or {}
            tag_rows.append({
                'name': m.get('name'),
                'model_tags': base_tags,
                'version_tags': ver_tags,
            })
        st.dataframe(pd.DataFrame(tag_rows), use_container_width=True)

    st.subheader("Inspect Versions")
    mcol1, mcol2 = st.columns([2,3])
    with mcol1:
        model_names = sorted({m.get('name') for m in models if m.get('name')})
        selected_model = st.selectbox("Model", model_names)
        if st.button("Load Versions", type="primary"):
            st.session_state._selected_model_versions = _cached_model_versions(selected_model)
    with mcol2:
        versions_response = st.session_state.get('_selected_model_versions')
        if isinstance(versions_response, dict):
            if versions_response.get("success"):
                versions = versions_response.get("data") or []
                if versions:
                    vdf = pd.DataFrame(versions)
                    if 'creation_timestamp' in vdf.columns:
                        vdf['creation_timestamp'] = vdf['creation_timestamp'].apply(_human_ts)
                    st.dataframe(vdf, use_container_width=True, height=260)
                else:
                    st.warning("Selected model has no registered versions.")
            else:
                err = versions_response.get("error", "Unable to load versions.")
                hint = versions_response.get("hint")
                st.error(err)
                if hint:
                    st.caption(f"Hint: {hint}")
        else:
            st.info("Select a model and click 'Load Versions' to view details.")

    st.caption("Data cached client-side for 300s; Refresh Cache to force retrieval.")


render_model_metadata()