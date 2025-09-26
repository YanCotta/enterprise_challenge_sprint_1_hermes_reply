import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from lib.api_client import make_api_request

st.set_page_config(page_title="Decision Log", page_icon="📝", layout="wide")

def _safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()  # type: ignore[attr-defined]


def render_decision_log():
    st.header("📝 Decision Log")
    st.caption("Audit trail of maintenance / human / automated decisions.")

    with st.expander("➕ Create Human Decision", expanded=False):
        with st.form("create_decision_form"):
            c1, c2 = st.columns(2)
            with c1:
                request_id = st.text_input("Request ID", placeholder="e.g. maintenance_request_001", help="Links this decision to an originating request/event")
                operator_id = st.text_input("Operator ID", placeholder="operator_jane")
                decision_value = st.text_input("Decision", placeholder="approved / rejected / escalate")
                confidence = st.slider("Confidence", min_value=0.0, max_value=1.0, value=1.0, step=0.05)
            with c2:
                justification = st.text_area("Justification", placeholder="Why was this decision made?", height=120)
                additional_notes = st.text_area("Additional Notes", placeholder="Optional free-form notes", height=120)
                correlation_id = st.text_input("Correlation ID (optional)")
            submit_decision = st.form_submit_button("Submit Decision", type="primary")
        if submit_decision:
            if not (request_id and operator_id and decision_value):
                st.error("Request ID, Operator ID and Decision are required.")
            else:
                payload = {
                    "request_id": request_id.strip(),
                    "decision": decision_value.strip(),
                    "operator_id": operator_id.strip(),
                    "justification": justification.strip() if justification else None,
                    "confidence": confidence,
                    "additional_notes": additional_notes.strip() if additional_notes else None,
                    "correlation_id": correlation_id.strip() if correlation_id else None,
                }
                resp = make_api_request("POST", "/api/v1/decisions/submit", json_data=payload)
                if resp.get("success"):
                    st.success("Decision submitted.")
                    # After successful submission, reset offset and rerun to see latest entries
                    st.session_state.decision_log_offset = 0
                    _safe_rerun()
                else:
                    st.error("Submission failed")
                    st.caption(resp.get("error"))

    # State
    if "decision_log_offset" not in st.session_state:
        st.session_state.decision_log_offset = 0

    # Controls
    c1, c2, c3, c4 = st.columns([1,1,1,2])
    with c1:
        page_size = st.selectbox("Page Size", [25,50,100,250], index=0)
    with c2:
        equipment_filter = st.text_input("Equipment ID", value="")
    with c3:
        status_filter = st.selectbox("Status", ["(all)", "pending", "in_progress", "completed", "partially_completed", "failed", "cancelled"], index=0)
    with c4:
        task_id_filter = st.text_input("Task ID", value="")

    top_bar = st.columns([1,3,3,3])[0]
    with top_bar:
        if st.button("↻ Refresh"):
            st.session_state.decision_log_offset = 0
            _safe_rerun()

    params = {"limit": page_size, "offset": st.session_state.decision_log_offset}
    if equipment_filter.strip():
        params["equipment_id"] = equipment_filter.strip()
    if task_id_filter.strip():
        params["task_id"] = task_id_filter.strip()
    if status_filter != "(all)":
        params["status"] = status_filter

    with st.spinner("Fetching decision log entries..."):
        resp = make_api_request("GET", "/api/v1/decisions", params=params)

    if not resp.get("success"):
        st.error("Failed to load decisions")
        st.caption(resp.get("error"))
        return

    rows = resp.get("data", [])
    if not rows:
        st.info("No decision entries found for current filters.")
        return

    # Normalize / convert to DataFrame
    df = pd.DataFrame(rows)
    # Convert datetime columns to string for nicer display
    for col in [c for c in ["completion_date", "created_at"] if c in df.columns]:
        df[col] = pd.to_datetime(df[col]).dt.tz_convert("UTC").dt.strftime("%Y-%m-%d %H:%M:%S %Z")

    st.dataframe(df, use_container_width=True)

    # Pagination controls
    p1, p2, p3 = st.columns([1,1,1])
    with p1:
        if st.button("⬅️ Previous", disabled=st.session_state.decision_log_offset == 0):
            st.session_state.decision_log_offset -= page_size
            _safe_rerun()
    with p2:
        st.write(f"Page {st.session_state.decision_log_offset // page_size + 1}")
    with p3:
        if st.button("Next ➡️", disabled=len(rows) < page_size):
            st.session_state.decision_log_offset += page_size
            _safe_rerun()

    with st.expander("Raw JSON (first 5)"):
        st.json(rows[:5])

if __name__ == "__main__":  # pragma: no cover
    render_decision_log()
