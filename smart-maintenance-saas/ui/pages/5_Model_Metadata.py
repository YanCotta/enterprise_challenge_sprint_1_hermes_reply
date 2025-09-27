import streamlit as st
import os
import pandas as pd
from datetime import datetime

from lib.api_client import make_api_request
from lib.rerun import safe_rerun

st.set_page_config(page_title="Model Metadata", page_icon="🧬")


def _deprecated_local_rerun():  # retained temporarily in case of stray imports
    from lib.rerun import safe_rerun as _sr
    _sr()


@st.cache_data(ttl=300)
def _cached_registered_models():
    resp = make_api_request("GET", "/api/v1/ml/models")  # Assuming endpoint listing models
    if resp.get("success"):
        return resp.get("data", [])
    return []


@st.cache_data(ttl=300)
def _cached_model_versions(model_name: str):
    resp = make_api_request("GET", f"/api/v1/ml/models/{model_name}/versions")
    if resp.get("success"):
        return resp.get("data", [])
    return []


def _human_ts(ts):
    try:
        return datetime.fromtimestamp(int(ts)/1000).isoformat() if isinstance(ts, (int,float)) else str(ts)
    except Exception:
        return str(ts)


def render_model_metadata():
    st.header("🧬 Model Metadata Explorer")
    st.caption("Browse registered MLflow models, versions, tags, and stages (cached 5m).")

    # Feature flag / env guard for disabled MLflow
    if os.getenv("DISABLE_MLFLOW_MODEL_LOADING", "false").lower() in ("1", "true", "yes"): 
        st.info("MLflow model loading disabled by environment flag DISABLE_MLFLOW_MODEL_LOADING. Enable it to view registry metadata.")
    col1, col2 = st.columns([2,1])
    with col2:
        if st.button("🔄 Refresh Cache", help="Clears local cache and refetches"):
            _cached_registered_models.clear()
            safe_rerun()

    models = _cached_registered_models()
    if not models:
        st.info("No models found or endpoint unavailable.")
        return

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
        versions = st.session_state.get('_selected_model_versions', [])
        if versions:
            vdf = pd.DataFrame(versions)
            if 'creation_timestamp' in vdf.columns:
                vdf['creation_timestamp'] = vdf['creation_timestamp'].apply(_human_ts)
            st.dataframe(vdf, use_container_width=True, height=260)
        else:
            st.info("Select a model and click 'Load Versions' to view details.")

    st.caption("Data cached client-side for 300s; Refresh Cache to force retrieval.")


render_model_metadata()