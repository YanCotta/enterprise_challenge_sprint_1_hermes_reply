"""
Smart Maintenance SaaS - Hermes Control Panel
Streamlit dashboard for interacting with the Smart Maintenance backend API.
"""

import streamlit as st
import requests
import json
import base64
import os
import uuid
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = "your_default_api_key"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Page configuration
st.set_page_config(
    page_title="Smart Maintenance SaaS - Hermes Control Panel",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

def make_api_request(method: str, endpoint: str, data: Dict[Any, Any] = None) -> Dict[Any, Any]:
    """Make an API request to the backend."""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "POST":
            response = requests.post(url, headers=HEADERS, json=data, timeout=10)
        elif method.upper() == "GET":
            response = requests.get(url, headers=HEADERS, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {
                "success": False, 
                "error": f"HTTP {response.status_code}: {response.text}"
            }
    except requests.exceptions.ConnectionError:
        return {
            "success": False, 
            "error": f"Connection failed. Make sure the backend server is running on {API_BASE_URL}"
        }
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

def main():
    # Main title
    st.title("🔧 Smart Maintenance SaaS - Hermes Control Panel")
    st.markdown("---")
    
    # Check backend connectivity
    with st.sidebar:
        st.header("🔗 System Status")
        health_check = make_api_request("GET", "/health")
        if health_check["success"]:
            st.success("✅ Backend Connected")
            st.json(health_check["data"])
        else:
            st.error("❌ Backend Disconnected")
            st.error(health_check["error"])
    
    # Create three columns for the main sections
    col1, col2, col3 = st.columns(3)
    
    # === SECTION 1: Manual Data Ingestion ===
    with col1:
        st.subheader("📊 Manual Sensor Data Ingestion")
        
        with st.form("data_ingestion_form"):
            sensor_id = st.text_input("Sensor ID", value="SENSOR_001", help="Unique identifier for the sensor")
            value = st.number_input("Value", value=25.5, help="Sensor reading value")
            sensor_type = st.selectbox(
                "Sensor Type", 
                ["temperature", "vibration", "pressure"],
                help="Type of sensor measurement"
            )
            unit = st.text_input("Unit", value="°C", help="Unit of measurement")
            
            submit_data = st.form_submit_button("📤 Submit Data", use_container_width=True)
            
            if submit_data:
                # Prepare the data payload with correct schema
                payload = {
                    "sensor_id": sensor_id,  # Required
                    "value": value,  # Required
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "sensor_type": sensor_type,
                    "unit": unit,
                    "quality": 0.95,  # Default quality value
                    "correlation_id": str(uuid.uuid4()),  # Generate UUID
                    "metadata": {
                        "source": "hermes_control_panel",
                        "operator": "manual_input"
                    }
                }
                
                # Make the API request
                result = make_api_request("POST", "/api/v1/data/ingest", payload)
                
                if result["success"]:
                    st.success("✅ Data ingested successfully!")
                    st.json(result["data"])
                else:
                    st.error("❌ Data ingestion failed!")
                    st.error(result["error"])
    
    # === SECTION 2: Report Generation ===
    with col2:
        st.subheader("📈 Generate System Report")
        
        with st.form("report_generation_form"):
            report_type = st.selectbox(
                "Report Type",
                ["performance_summary", "anomaly_summary", "maintenance_summary", "system_health"],
                help="Type of report to generate"
            )
            
            report_format = st.selectbox(
                "Report Format",
                ["json", "text"],
                help="Output format for the report"
            )
            
            include_charts = st.checkbox(
                "Include Charts",
                value=True,
                help="Generate visual charts with the report"
            )
            
            # Date range selection
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                start_date = st.date_input("Start Date", value=datetime.now(timezone.utc).date() - timedelta(days=30))
            with col_date2:
                end_date = st.date_input("End Date", value=datetime.now(timezone.utc).date())
            
            generate_report = st.form_submit_button("📊 Generate Report", use_container_width=True)
            
            if generate_report:
                # Prepare the report request payload
                start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
                
                payload = {
                    "report_type": report_type,
                    "format": report_format,
                    "parameters": {"include_details": True},
                    "time_range_start": start_datetime.isoformat(),
                    "time_range_end": end_datetime.isoformat(),
                    "include_charts": include_charts
                }
                
                # Make the API request
                result = make_api_request("POST", "/api/v1/reports/generate", payload)
                
                if result["success"]:
                    st.success("✅ Report generated successfully!")
                    
                    report_data = result["data"]
                    
                    # Display report metadata in a nice layout
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Report ID:** `{report_data.get('report_id', 'N/A')}`")
                        st.write(f"**Type:** {report_data.get('report_type', 'N/A')}")
                    with col_b:
                        st.write(f"**Format:** {report_data.get('format', 'N/A')}")
                        if report_data.get('generated_at'):
                            st.write(f"**Generated:** {report_data['generated_at'][:19]}")
                    
                    # Display report content
                    st.subheader("📊 Report Content")
                    if report_data.get("format") == "json":
                        try:
                            content = json.loads(report_data.get("content", "{}"))
                            st.json(content)
                        except json.JSONDecodeError:
                            st.code(report_data.get("content", "No content available"), language="json")
                    else:
                        st.text_area("Content:", value=report_data.get("content", "No content available"), height=150, disabled=True)
                    
                    # Display charts if available
                    if "charts_encoded" in report_data and report_data["charts_encoded"]:
                        st.subheader("📈 Charts")
                        charts = report_data["charts_encoded"]
                        for chart_name, chart_data in charts.items():
                            try:
                                chart_bytes = base64.b64decode(chart_data)
                                st.image(chart_bytes, caption=chart_name.replace("_", " ").title())
                            except Exception as e:
                                st.warning(f"Could not display chart {chart_name}: {str(e)}")
                    
                    # Show metadata
                    with st.expander("📋 Report Metadata"):
                        st.json(report_data.get("metadata", {}))
                else:
                    st.error("❌ Report generation failed!")
                    st.error(result["error"])
    
    # === SECTION 3: Human Decision Simulation ===
    with col3:
        st.subheader("👤 Submit Human Decision")
        
        with st.form("decision_submission_form"):
            request_id = st.text_input(
                "Request ID", 
                value="REQ_001", 
                help="ID of the maintenance request to decide on"
            )
            decision = st.selectbox(
                "Decision",
                ["approve", "reject"],
                help="Your decision on the maintenance request"
            )
            justification = st.text_area(
                "Justification",
                value="Reviewed by maintenance supervisor. Equipment condition assessment completed.",
                help="Explanation for your decision"
            )
            
            submit_decision = st.form_submit_button("✅ Submit Decision", use_container_width=True)
            
            if submit_decision:
                # Prepare the decision payload with correct schema
                payload = {
                    "request_id": request_id,  # Required
                    "decision": decision,  # Required
                    "operator_id": "hermes_control_panel_user",  # Required
                    "justification": justification,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "confidence": 0.9,  # Default confidence
                    "additional_notes": f"Submitted via Hermes Control Panel at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "correlation_id": str(uuid.uuid4())
                }
                
                # Make the API request
                result = make_api_request("POST", "/api/v1/decisions/submit", payload)
                
                if result["success"]:
                    st.success("✅ Decision submitted successfully!")
                    st.json(result["data"])
                else:
                    st.error("❌ Decision submission failed!")
                    st.error(result["error"])
    
    # === ADDITIONAL SECTIONS ===
    st.markdown("---")
    
    # Master Dataset Preview Section
    st.header("Master Dataset Preview")
    
    if st.button("Load and Preview Sensor Data"):
        data_path = 'data/sensor_data.csv'
        if os.path.exists(data_path):
            try:
                df = pd.read_csv(data_path, parse_dates=['timestamp'])
                st.success(f"Successfully loaded {len(df)} readings from {data_path}")
                
                st.subheader("Raw Data Sample")
                st.dataframe(df.head())

                st.subheader("Time-Series Preview (first 1000 readings)")
                preview_df = df.head(1000).set_index('timestamp')
                st.line_chart(preview_df[['value']])
                
            except Exception as e:
                st.error(f"Failed to load or parse the dataset: {e}")
        else:
            st.warning(f"Dataset not found at {data_path}. Please ensure Day 5 tasks (seeding/export) were completed.")

    st.markdown("---")
    
    # Recent Activity Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 System Information")
        with st.expander("🔧 API Endpoints Available"):
            st.markdown("""
            **Data Management:**
            - `POST /api/v1/data/ingest` - Ingest sensor data
            - `GET /health` - System health check
            
            **Report Generation:**
            - `POST /api/v1/reports/generate` - Generate system reports
            
            **Decision Management:**
            - `POST /api/v1/decisions/submit` - Submit human decisions
            
            **Authentication:**
            - All endpoints require `X-API-Key: your_default_api_key`
            """)
    
    with col2:
        st.subheader("🚀 Quick Actions")
        
        # Quick test data button
        if st.button("🧪 Send Test Data", help="Send sample sensor data for testing"):
            test_payload = {
                "sensor_id": f"TEST_SENSOR_{datetime.now().strftime('%H%M%S')}",
                "value": 42.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sensor_type": "temperature",
                "unit": "°C",
                "quality": 0.95,
                "correlation_id": str(uuid.uuid4()),
                "metadata": {"source": "test_button"}
            }
            
            result = make_api_request("POST", "/api/v1/data/ingest", test_payload)
            if result["success"]:
                st.success("✅ Test data sent successfully!")
            else:
                st.error(f"❌ Test data failed: {result['error']}")
        
        # Quick health check button
        if st.button("🔍 Check System Health", help="Verify backend connectivity"):
            result = make_api_request("GET", "/health")
            if result["success"]:
                st.success("✅ System is healthy!")
                st.json(result["data"])
            else:
                st.error(f"❌ System health check failed: {result['error']}")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center'>"
        "<small>Smart Maintenance SaaS - Hermes Control Panel | "
        f"Connected to: {API_BASE_URL} | "
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
