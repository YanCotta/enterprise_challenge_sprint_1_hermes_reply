import streamlit as st
from ui.lib.api_client import get_current_api_config, probe_connectivity, make_api_request

st.set_page_config(page_title="Debug Panel", page_icon="🛠", layout="wide")

st.title("🛠 Debug & Diagnostics")

with st.expander("Resolved API Configuration", expanded=True):
    cfg = get_current_api_config()
    st.json(cfg)
    if st.button("Probe /health", use_container_width=True):
        res = probe_connectivity("/health")
        st.write(res)
    if st.button("Probe /api/v1/sensors/readings?limit=1", use_container_width=True):
        out = make_api_request("GET", "/api/v1/sensors/readings", params={"limit": 1})
        st.write(out)

with st.expander("Ad-hoc Endpoint Tester", expanded=False):
    col1, col2 = st.columns([1,3])
    with col1:
        method = st.selectbox("Method", ["GET", "POST", "DELETE", "PUT", "PATCH"], index=0)
        timeout = st.number_input("Timeout (s)", min_value=1, max_value=120, value=20)
    with col2:
        endpoint = st.text_input("Endpoint (relative or absolute)", value="/health")
        params_text = st.text_area("Query Params (key=value per line)", value="")
        json_text = st.text_area("JSON Body (optional)", value="")

    def parse_kv(text: str):
        result = {}
        for line in text.splitlines():
            if not line.strip():
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                result[k.strip()] = v.strip()
        return result

    params = parse_kv(params_text)
    json_data = None
    if json_text.strip():
        try:
            import json as _json
            json_data = _json.loads(json_text)
        except Exception as e:  # noqa: BLE001
            st.error(f"Invalid JSON body: {e}")

    if st.button("Send Request", type="primary"):
        with st.spinner("Sending..."):
            resp = make_api_request(method, endpoint, params=params or None, json_data=json_data, timeout=timeout)
        if resp.get("success"):
            st.success("Success")
            st.json(resp)
        else:
            st.error(resp.get("error"))
            st.json(resp)

st.caption("This page is temporary and should be removed or access-controlled before production release.")
