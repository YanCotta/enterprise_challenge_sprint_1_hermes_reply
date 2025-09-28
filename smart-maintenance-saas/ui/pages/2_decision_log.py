import streamlit as st
import pandas as pd
from datetime import datetime, timezone, date
import uuid

from lib.api_client import make_api_request
from lib.rerun import safe_rerun


def _fetch_human_decisions(limit: int, offset: int, operator_id: str | None, request_id: str | None, correlation_id: str | None, start_dt: date | None, end_dt: date | None):
    params = {"limit": limit, "offset": offset}
    if operator_id:
        params["operator_id"] = operator_id
    if request_id:
        params["request_id"] = request_id
    if correlation_id:
        params["correlation_id"] = correlation_id
    if start_dt:
        params["start_date"] = start_dt.isoformat()
    if end_dt:
        params["end_date"] = end_dt.isoformat()
    return make_api_request("GET", "/api/v1/decisions", params=params)


def render_decision_log_page():
    """Renders the decision log page for viewing and submitting human decisions."""
    st.header("📋 Decision Audit Trail")
    st.caption("Filter, inspect, and record human decisions. Maintenance logs tab reserved for future integration.")
    st.caption("Create/List only (update/delete deferred to V1.5+).")

    # --- STATE MANAGEMENT FOR PAGINATION ---
    if 'decision_log_offset' not in st.session_state:
        st.session_state.decision_log_offset = 0

    # --- SUBMIT NEW DECISION ---
    with st.expander("➕ Create Human Decision"):
        with st.form("new_decision_form", clear_on_submit=True):
            st.subheader("Submit New Decision")
            req_id = st.text_input("Request ID*", help="The maintenance or analysis request ID.")
            op_id = st.text_input("Operator ID*", value="log_op_01", help="The ID of the user making the decision.")
            decision = st.selectbox("Decision*", ["approved", "rejected", "escalated"], help="The outcome of the decision.")
            justification = st.text_area("Justification", help="Reasoning behind the decision.")
            
            submit_button = st.form_submit_button("✅ Submit Decision")

            if submit_button:
                if not req_id or not op_id or not decision:
                    st.warning("Please fill in all required fields (*).")
                else:
                    payload = {
                        "request_id": req_id,
                        "operator_id": op_id,
                        "decision": decision,
                        "justification": justification,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "confidence": 1.0,
                        "additional_notes": "Submitted via UI form.",
                        "correlation_id": str(uuid.uuid4())
                    }
                    with st.spinner("Submitting decision..."):
                        result = make_api_request("POST", "/api/v1/decisions/submit", json_data=payload)

                    if result["success"]:
                        st.success("Decision submitted successfully!")
                        st.session_state.decision_log_offset = 0 # Reset to first page to see new entry
                        # No need to rerun here, Streamlit's form submission handles the refresh.
                    else:
                        st.error("Failed to submit decision.")
                        st.error(result.get("error"))

    st.markdown("---")

    tabs = st.tabs(["Human Decisions", "Maintenance Logs (Future)"])

    with tabs[0]:
        st.subheader("Human Decision History")
        filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns([1,1,1,1,1])
        with filter_col1:
            filt_operator = st.text_input("Filter Operator")
        with filter_col2:
            filt_request = st.text_input("Filter Request ID")
        with filter_col3:
            filt_corr = st.text_input("Correlation ID")
        with filter_col4:
            start_date = st.date_input("Start Date", value=None, key="dec_start", help="Inclusive")
        with filter_col5:
            end_date = st.date_input("End Date", value=None, key="dec_end", help="Inclusive")

        ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([1,1,1,2])
        with ctrl_col1:
            page_size = st.selectbox("Page Size", [25, 50, 100], index=1)
        with ctrl_col2:
            if st.button("🔄 Refresh"):
                safe_rerun()
        with ctrl_col3:
            if st.button("⏱ Reset Offset"):
                st.session_state.decision_log_offset = 0
                safe_rerun()
        with ctrl_col4:
            st.caption("Use filters then Refresh. Date filters optional.")

        with st.spinner("Fetching decisions..."):
            log_result = _fetch_human_decisions(
                limit=page_size,
                offset=st.session_state.decision_log_offset,
                operator_id=filt_operator.strip() or None,
                request_id=filt_request.strip() or None,
                correlation_id=filt_corr.strip() or None,
                start_dt=start_date if isinstance(start_date, date) else None,
                end_dt=end_date if isinstance(end_date, date) else None,
            )

        if log_result["success"]:
            rows = log_result["data"]
            if rows:
                df = pd.DataFrame(rows)
                display_cols = ["timestamp", "request_id", "operator_id", "decision", "justification", "correlation_id"]
                df_display = df[[c for c in display_cols if c in df.columns]]
                st.dataframe(df_display, use_container_width=True, height=400)

                exp_cols = st.columns([1,1,2])
                with exp_cols[0]:
                    if st.button("⬅️ Previous", disabled=(st.session_state.decision_log_offset == 0)):
                        st.session_state.decision_log_offset -= page_size
                        safe_rerun()
                with exp_cols[1]:
                    if st.button("Next ➡️", disabled=(len(rows) < page_size)):
                        st.session_state.decision_log_offset += page_size
                        safe_rerun()
                with exp_cols[2]:
                    csv_name = f"human_decisions_page_{st.session_state.decision_log_offset // page_size + 1}.csv"
                    st.download_button(
                        "⬇️ Export CSV",
                        data=df_display.to_csv(index=False).encode("utf-8"),
                        file_name=csv_name,
                        mime="text/csv",
                        use_container_width=True,
                    )
            else:
                st.info("No decisions match current filters.")
        else:
            st.error("Failed to load decisions")
            st.error(log_result.get("error"))

    with tabs[1]:
        st.subheader("Maintenance Logs (Planned)")
        st.info("This tab will surface historical maintenance execution logs in a future iteration.")


# Main entry point for the page
render_decision_log_page()
