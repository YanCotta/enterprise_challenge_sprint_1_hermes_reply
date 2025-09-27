import streamlit as st
import pandas as pd
from datetime import datetime, timezone
import uuid

# Import the centralized API client
from lib.api_client import make_api_request

def render_decision_log_page():
    """Renders the decision log page for viewing and submitting human decisions."""
    st.header("� Decision Audit Trail")
    st.caption("View and submit human decisions for audit and traceability.")

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

    # --- DISPLAY DECISION LOG ---
    st.subheader("Decision History")
    
    # --- CONTROLS ---
    page_size = 50 # Keep it simple for now

    # --- DATA FETCHING ---
    params = {"limit": page_size, "offset": st.session_state.decision_log_offset}
    with st.spinner("Fetching decision logs..."):
        log_result = make_api_request("GET", "/api/v1/decisions", params=params)

    # --- DISPLAY ---
    if log_result["success"]:
        rows = log_result["data"]
        if rows:
            df = pd.DataFrame(rows)
            # Display a curated set of columns
            display_cols = ["timestamp", "request_id", "operator_id", "decision", "justification"]
            df_display = df[[col for col in display_cols if col in df.columns]]
            st.dataframe(df_display, use_container_width=True)

            # --- PAGINATION ---
            pcol1, pcol2, pcol3 = st.columns([1, 1, 1])
            with pcol1:
                if st.button("⬅️ Previous", disabled=(st.session_state.decision_log_offset == 0)):
                    st.session_state.decision_log_offset -= page_size
                    st.experimental_rerun()
            with pcol2:
                st.write(f"Page {st.session_state.decision_log_offset // page_size + 1}")
            with pcol3:
                if st.button("Next ➡️", disabled=(len(rows) < page_size)):
                    st.session_state.decision_log_offset += page_size
                    st.experimental_rerun()
        else:
            st.info("No decision logs found.")
    else:
        st.error("Failed to load decision logs.")
        st.error(log_result.get("error"))


# Main entry point for the page
render_decision_log_page()
