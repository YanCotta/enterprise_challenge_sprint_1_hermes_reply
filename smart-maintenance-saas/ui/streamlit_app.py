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

# Import our new model utility functions
try:
    from apps.ml.model_utils import (
        get_models_by_sensor_type,
        get_model_recommendations,
        suggest_sensor_types,
        get_all_registered_models
    )
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    st.warning("⚠️ MLflow model utilities not available. Model selection features will be limited.")

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "dev_api_key_123")
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
        
        if response.status_code in [200, 201]:
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
    
    # === INTELLIGENT MODEL SELECTION SECTION ===
    st.header("🤖 Intelligent Model Selection")
    
    if MLFLOW_AVAILABLE:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Model Recommendations")
            
            # Sensor type selection with fallback
            try:
                sensor_types = suggest_sensor_types()
            except Exception as e:
                st.warning(f"⚠️ Could not fetch sensor types from MLflow: {str(e)}")
                sensor_types = ['bearing', 'manufacturing', 'audio', 'forecasting', 'general', 'temperature', 'pressure', 'vibration', 'pump']
            
            selected_sensor_type = st.selectbox(
                "Select Sensor Type",
                sensor_types,
                help="Choose the type of sensor data you want to analyze"
            )
            
            # Get recommended models
            if st.button("🔍 Get Model Recommendations", key="get_recommendations"):
                with st.spinner("Fetching model recommendations..."):
                    try:
                        recommendations = get_model_recommendations(selected_sensor_type)
                        
                        if recommendations:
                            st.success(f"✅ Found {len(recommendations)} recommended models for {selected_sensor_type} sensors:")
                            
                            # Display recommendations in a nice format
                            for i, model_name in enumerate(recommendations, 1):
                                st.write(f"{i}. **{model_name}**")
                            
                            # Store recommendations in session state for use in prediction
                            st.session_state['recommended_models'] = recommendations
                            st.session_state['selected_sensor_type'] = selected_sensor_type
                            
                        else:
                            st.warning(f"No specific models found for {selected_sensor_type} sensors.")
                            st.info("💡 **Tip**: Models have been tagged with sensor types. Available types: bearing, manufacturing, audio, forecasting, general")
                    
                    except Exception as e:
                        st.error(f"❌ Failed to get model recommendations: {str(e)}")
                        # Provide fallback recommendations
                        fallback_models = {
                            'bearing': ['vibration_anomaly_isolationforest', 'xjtu_anomaly_isolation_forest'],
                            'manufacturing': ['ai4i_classifier_randomforest_baseline', 'ai4i_classifier_lightgbm_baseline'],
                            'audio': ['RandomForest_MIMII_Audio_Benchmark', 'MIMII_Audio_Scaler'],
                            'forecasting': ['prophet_forecaster_enhanced_sensor-001', 'lightgbm_forecaster_challenger'],
                            'general': ['anomaly_detector_refined_v2', 'synthetic_validation_isolation_forest'],
                            'temperature': ['anomaly_detector_refined_v2', 'synthetic_validation_isolation_forest'],
                            'pressure': ['anomaly_detector_refined_v2', 'synthetic_validation_isolation_forest'],
                            'vibration': ['vibration_anomaly_isolationforest', 'xjtu_anomaly_isolation_forest'],
                            'pump': ['anomaly_detector_refined_v2', 'synthetic_validation_isolation_forest']
                        }
                        
                        if selected_sensor_type in fallback_models:
                            st.info(f"🔄 Using fallback recommendations for {selected_sensor_type}:")
                            for i, model_name in enumerate(fallback_models[selected_sensor_type], 1):
                                st.write(f"{i}. **{model_name}**")
                            st.session_state['recommended_models'] = fallback_models[selected_sensor_type]
                            st.session_state['selected_sensor_type'] = selected_sensor_type
            
            # Manual model selection option
            st.markdown("---")
            allow_manual = st.checkbox("🔧 Allow Manual Model Selection", help="Show all available models for manual selection")
            
            if allow_manual:
                try:
                    all_models = get_all_registered_models()
                    if all_models:
                        model_names = [model['name'] for model in all_models]
                        selected_manual_model = st.selectbox(
                            "Manual Model Selection",
                            model_names,
                            help="Choose any available model manually"
                        )
                        
                        if st.button("📋 Get Model Details", key="get_model_details"):
                            model_details = next((model for model in all_models if model['name'] == selected_manual_model), None)
                            if model_details:
                                st.json(model_details)
                            else:
                                st.error("Model details not found")
                    else:
                        st.warning("No registered models found in MLflow.")
                except Exception as e:
                    st.error(f"Failed to load model list: {str(e)}")
                    # Fallback manual model list
                    st.info("🔄 Using fallback model list:")
                    fallback_models = [
                        'vibration_anomaly_isolationforest',
                        'ai4i_classifier_randomforest_baseline', 
                        'RandomForest_MIMII_Audio_Benchmark',
                        'xjtu_anomaly_isolation_forest',
                        'anomaly_detector_refined_v2'
                    ]
                    selected_manual_model = st.selectbox(
                        "Fallback Model Selection",
                        fallback_models,
                        help="Choose from known models"
                    )
        
        with col2:
            st.subheader("🎯 Model Prediction Interface")
            
            # Model selection for prediction
            prediction_model = None
            
            # Use recommended models if available
            if 'recommended_models' in st.session_state and st.session_state['recommended_models']:
                st.write("**Recommended Models:**")
                prediction_model = st.selectbox(
                    "Select Recommended Model",
                    st.session_state['recommended_models'],
                    help="Choose from models recommended for your sensor type",
                    key="recommended_model_select"
                )
            else:
                # Fallback to manual selection
                st.write("**Available Models:**")
                fallback_models = [
                    'vibration_anomaly_isolationforest',
                    'ai4i_classifier_randomforest_baseline', 
                    'RandomForest_MIMII_Audio_Benchmark',
                    'xjtu_anomaly_isolation_forest',
                    'anomaly_detector_refined_v2'
                ]
                prediction_model = st.selectbox(
                    "Select Any Available Model",
                    fallback_models,
                    help="Choose from available models",
                    key="fallback_model_select"
                )
            
            # Prediction interface
            if prediction_model:
                st.write(f"**Selected Model:** {prediction_model}")
                
                with st.form("prediction_form"):
                    st.write("**Input Sensor Data for Prediction:**")
                    
                    pred_sensor_id = st.text_input("Sensor ID", value="PRED_SENSOR_001")
                    pred_value = st.number_input("Sensor Value", value=42.5)
                    pred_timestamp = st.text_input(
                        "Timestamp (ISO format)", 
                        value=datetime.now(timezone.utc).isoformat()
                    )
                    
                    submit_prediction = st.form_submit_button("🔮 Get Prediction")
                    
                    if submit_prediction:
                        # Prepare prediction payload
                        prediction_payload = {
                            "model_name": prediction_model,
                            "sensor_data": {
                                "sensor_id": pred_sensor_id,
                                "value": pred_value,
                                "timestamp": pred_timestamp,
                                "sensor_type": st.session_state.get('selected_sensor_type', 'unknown')
                            }
                        }
                        
                        # Make prediction API call (placeholder for now)
                        st.success(f"🚀 Prediction request prepared for model: {prediction_model}")
                        with st.expander("📋 View Prediction Payload"):
                            st.json(prediction_payload)
                        
                        st.info("ℹ️ **Note**: This demonstrates the payload that would be sent to a prediction endpoint. The actual prediction API is not yet implemented.")
    
    else:
        st.warning("🔧 MLflow integration not available. Model selection features are limited.")
        st.info("📝 **Available features**: You can still use the basic data ingestion, report generation, and decision submission functionality above.")
        
        # Show fallback model information
        st.subheader("📊 Available Model Types")
        model_info = {
            "Bearing Analysis": ["vibration_anomaly_isolationforest", "xjtu_anomaly_isolation_forest"],
            "Manufacturing Equipment": ["ai4i_classifier_randomforest_baseline", "ai4i_classifier_lightgbm_baseline"],
            "Audio Analysis": ["RandomForest_MIMII_Audio_Benchmark"],
            "Forecasting": ["prophet_forecaster_enhanced_sensor-001", "lightgbm_forecaster_challenger"],
            "General Purpose": ["anomaly_detector_refined_v2", "synthetic_validation_isolation_forest"]
        }
        
        for category, models in model_info.items():
            with st.expander(f"🔧 {category}"):
                for model in models:
                    st.write(f"• **{model}**")
    
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
