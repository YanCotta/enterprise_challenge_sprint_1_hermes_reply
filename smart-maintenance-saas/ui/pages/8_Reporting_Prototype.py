import json
from datetime import datetime, time

import streamlit as st

from lib.api_client import make_api_request

st.set_page_config(page_title="Reporting Prototype", page_icon="🧾")

st.header("🧾 Reporting Prototype")
st.warning("Prototype – JSON only; artifact downloads deferred (V1.5+).")
st.caption("Generate lightweight JSON summaries. Artifact persistence and streaming remain deferred.")

with st.form("report_form"):
    report_type = st.selectbox(
        "Report Type",
        [
            "system_health",
            "anomaly_summary",
            "ingestion_activity",
            "maintenance_decisions",
        ],
    )
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=None)
    with col2:
        end_date = st.date_input("End Date", value=None)
    include_charts = st.checkbox("Include charts metadata", value=False)
    submitted = st.form_submit_button("Generate", type="primary")

if submitted:
    payload = {
        "report_type": report_type,
        "format": "json",
        "parameters": {},
        "include_charts": include_charts,
    }
    if start_date:
        payload["time_range_start"] = datetime.combine(start_date, time.min).isoformat()
    if end_date:
        payload["time_range_end"] = datetime.combine(end_date, time.max).isoformat()

    with st.spinner("Generating report..."):
        resp = make_api_request("POST", "/api/v1/reports/generate", json_data=payload)

    if resp.get("success"):
        report = resp.get("data")
        st.success("Report generated")
        
        # Add download button for JSON
        st.download_button(
            "⬇️ Download JSON",
            data=json.dumps(report, indent=2),
            file_name=f"report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
        
        st.json(report)
        st.caption("JSON download available; PDF/CSV formats deferred to V1.5+.")
    else:
        st.error(resp.get("error", "Failed to generate report."))
        if resp.get("hint"):
            st.caption(f"Hint: {resp['hint']}")
else:
    st.info("Select parameters and click Generate to fetch a JSON-only prototype report.")
