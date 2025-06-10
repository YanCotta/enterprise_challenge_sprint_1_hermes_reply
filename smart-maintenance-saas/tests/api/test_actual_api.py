#!/usr/bin/env python3
"""
Test script to verify Smart Maintenance SaaS UI functionality
Tests the actual implemented API endpoints
"""

import requests
import json
import time
import uuid
from datetime import datetime, timezone

# Configuration
API_BASE_URL = "http://localhost:8000"  # External access for testing
API_KEY = "your_default_api_key"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_health_endpoints():
    """Test health check endpoints"""
    print("🔧 Testing Health Endpoints...")
    
    # Test basic health
    try:
        response = requests.get(f"{API_BASE_URL}/health", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            print("✅ Basic Health Check: PASSED")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Basic Health Check: FAILED (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Basic Health Check: FAILED (Error: {e})")
    
    # Test database health
    try:
        response = requests.get(f"{API_BASE_URL}/health/db", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            print("✅ Database Health Check: PASSED")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Database Health Check: FAILED (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Database Health Check: FAILED (Error: {e})")

def test_data_ingestion():
    """Test data ingestion endpoint"""
    print("\n📊 Testing Data Ingestion...")
    
    # Sample sensor data for ingestion - using correct schema
    sensor_data = {
        "sensor_id": "pump_001_temp_sensor",  # Required field
        "value": 75.5,  # Required field
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sensor_type": "temperature",
        "unit": "celsius",
        "quality": 0.95,
        "correlation_id": str(uuid.uuid4()),
        "metadata": {
            "location": "bearing_1",
            "calibration_date": "2024-01-01"
        }
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/data/ingest", 
            headers=HEADERS, 
            json=sensor_data, 
            timeout=10
        )
        if response.status_code == 200:
            print("✅ Data Ingestion: PASSED")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Data Ingestion: FAILED (Status: {response.status_code})")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Data Ingestion: FAILED (Error: {e})")

def test_reporting():
    """Test report generation endpoint"""
    print("\n📋 Testing Report Generation...")
    
    # Sample report request
    report_request = {
        "report_type": "maintenance_summary",
        "equipment_id": "pump_001",
        "date_range": {
            "start": "2024-01-01",
            "end": "2024-12-31"
        },
        "format": "json"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/reports/generate", 
            headers=HEADERS, 
            json=report_request, 
            timeout=10
        )
        if response.status_code == 200:
            print("✅ Report Generation: PASSED")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Report Generation: FAILED (Status: {response.status_code})")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Report Generation: FAILED (Error: {e})")

def test_human_decisions():
    """Test human decision endpoint"""
    print("\n🤔 Testing Human Decision Submission...")
    
    # Sample decision - using correct schema
    decision_data = {
        "request_id": "maintenance_request_001",  # Required field
        "decision": "approved",  # Required field
        "operator_id": "maintenance_manager_john",  # Required field
        "justification": "Equipment shows signs of wear, maintenance approved",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "confidence": 0.9,
        "additional_notes": "Schedule maintenance for next weekend",
        "correlation_id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/decisions/submit", 
            headers=HEADERS, 
            json=decision_data, 
            timeout=10
        )
        if response.status_code in [200, 201]:
            print("✅ Human Decision Submission: PASSED")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Human Decision Submission: FAILED (Status: {response.status_code})")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Human Decision Submission: FAILED (Error: {e})")

def test_api_docs():
    """Test API documentation endpoints"""
    print("\n📚 Testing API Documentation...")
    
    try:
        # Test OpenAPI schema
        response = requests.get(f"{API_BASE_URL}/openapi.json", timeout=10)
        if response.status_code == 200:
            print("✅ OpenAPI Schema: ACCESSIBLE")
        else:
            print(f"❌ OpenAPI Schema: FAILED (Status: {response.status_code})")
            
        # Test docs UI
        response = requests.get(f"{API_BASE_URL}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ Swagger UI: ACCESSIBLE")
        else:
            print(f"❌ Swagger UI: FAILED (Status: {response.status_code})")
            
        # Test root endpoint
        response = requests.get(f"{API_BASE_URL}/", timeout=10)
        if response.status_code == 200:
            print("✅ Root Endpoint: ACCESSIBLE")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Root Endpoint: FAILED (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ API Documentation: FAILED (Error: {e})")

def test_streamlit_ui():
    """Test if Streamlit UI is accessible"""
    print("\n🎨 Testing Streamlit UI...")
    
    try:
        response = requests.get("http://localhost:8501", timeout=10)
        if response.status_code == 200:
            print("✅ Streamlit UI: ACCESSIBLE")
            print("   UI should be available at http://localhost:8501")
        else:
            print(f"❌ Streamlit UI: FAILED (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Streamlit UI: FAILED (Error: {e})")

def main():
    """Run all tests"""
    print("🚀 Starting Smart Maintenance SaaS Comprehensive Tests")
    print("=" * 60)
    
    # Test health endpoints
    test_health_endpoints()
    
    # Test API functionality
    test_data_ingestion()
    test_reporting()
    test_human_decisions()
    
    # Test documentation
    test_api_docs()
    
    # Test Streamlit UI
    test_streamlit_ui()
    
    print("\n" + "=" * 60)
    print("🏁 Test Suite Completed!")
    print("\n✨ Summary:")
    print("   🔗 API Documentation: http://localhost:8000/docs")
    print("   🎯 Streamlit UI: http://localhost:8501")
    print("   📊 Health Check: http://localhost:8000/health")
    print("\n📝 Next Steps:")
    print("   1. Open the Streamlit UI and test manually")
    print("   2. Use the API documentation to explore endpoints")
    print("   3. Test data ingestion and reporting features")

if __name__ == "__main__":
    main()
