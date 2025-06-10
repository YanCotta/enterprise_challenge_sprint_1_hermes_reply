#!/usr/bin/env python3
"""
Test script to verify all Streamlit UI functionality
Tests all major functions of the Smart Maintenance SaaS UI
"""

import requests
import json
import time
from datetime import datetime, timezone

# Configuration
API_BASE_URL = "http://localhost:8000"  # External access for testing
API_KEY = "your_default_api_key"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_api_connection():
    """Test basic API connectivity"""
    print("🔧 Testing API Connection...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            print("✅ API Health Check: PASSED")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ API Health Check: FAILED (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ API Health Check: FAILED (Error: {e})")
        return False

def test_equipment_operations():
    """Test equipment CRUD operations"""
    print("\n🏭 Testing Equipment Operations...")
    
    # Test equipment creation
    equipment_data = {
        "name": "Test Pump",
        "type": "Centrifugal Pump",
        "model": "CP-100",
        "manufacturer": "Test Manufacturer",
        "installation_date": "2024-01-01",
        "location": "Building A - Floor 1",
        "specifications": {"power": "100kW", "flow_rate": "500L/min"}
    }
    
    try:
        # Create equipment
        response = requests.post(f"{API_BASE_URL}/equipment", headers=HEADERS, json=equipment_data, timeout=10)
        if response.status_code == 200:
            equipment = response.json()
            equipment_id = equipment["id"]
            print(f"✅ Equipment Creation: PASSED (ID: {equipment_id})")
            
            # Get equipment
            response = requests.get(f"{API_BASE_URL}/equipment/{equipment_id}", headers=HEADERS, timeout=10)
            if response.status_code == 200:
                print("✅ Equipment Retrieval: PASSED")
            else:
                print(f"❌ Equipment Retrieval: FAILED (Status: {response.status_code})")
                
            # List equipment
            response = requests.get(f"{API_BASE_URL}/equipment", headers=HEADERS, timeout=10)
            if response.status_code == 200:
                equipment_list = response.json()
                print(f"✅ Equipment List: PASSED ({len(equipment_list)} items)")
            else:
                print(f"❌ Equipment List: FAILED (Status: {response.status_code})")
                
            return equipment_id
        else:
            print(f"❌ Equipment Creation: FAILED (Status: {response.status_code})")
            return None
    except Exception as e:
        print(f"❌ Equipment Operations: FAILED (Error: {e})")
        return None

def test_maintenance_logs(equipment_id):
    """Test maintenance log operations"""
    print("\n📋 Testing Maintenance Log Operations...")
    
    if not equipment_id:
        print("❌ Skipping maintenance logs test (no equipment ID)")
        return None
        
    log_data = {
        "equipment_id": equipment_id,
        "maintenance_type": "preventive",
        "description": "Routine inspection and lubrication",
        "performed_by": "John Doe",
        "performed_at": datetime.now(timezone.utc).isoformat(),
        "duration_minutes": 60,
        "cost": 150.00,
        "parts_used": ["Oil filter", "Lubricant"],
        "notes": "All systems functioning normally"
    }
    
    try:
        # Create maintenance log
        response = requests.post(f"{API_BASE_URL}/maintenance-logs", headers=HEADERS, json=log_data, timeout=10)
        if response.status_code == 200:
            log = response.json()
            log_id = log["id"]
            print(f"✅ Maintenance Log Creation: PASSED (ID: {log_id})")
            
            # Get maintenance logs for equipment
            response = requests.get(f"{API_BASE_URL}/equipment/{equipment_id}/maintenance-logs", headers=HEADERS, timeout=10)
            if response.status_code == 200:
                logs = response.json()
                print(f"✅ Maintenance Log Retrieval: PASSED ({len(logs)} logs)")
            else:
                print(f"❌ Maintenance Log Retrieval: FAILED (Status: {response.status_code})")
                
            return log_id
        else:
            print(f"❌ Maintenance Log Creation: FAILED (Status: {response.status_code})")
            return None
    except Exception as e:
        print(f"❌ Maintenance Log Operations: FAILED (Error: {e})")
        return None

def test_sensor_data(equipment_id):
    """Test sensor data operations"""
    print("\n📊 Testing Sensor Data Operations...")
    
    if not equipment_id:
        print("❌ Skipping sensor data test (no equipment ID)")
        return
        
    sensor_data = {
        "equipment_id": equipment_id,
        "sensor_type": "temperature",
        "value": 75.5,
        "unit": "celsius",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": {"location": "bearing_1", "calibration_date": "2024-01-01"}
    }
    
    try:
        # Submit sensor data
        response = requests.post(f"{API_BASE_URL}/sensor-data", headers=HEADERS, json=sensor_data, timeout=10)
        if response.status_code == 200:
            print("✅ Sensor Data Submission: PASSED")
            
            # Get sensor data for equipment
            response = requests.get(f"{API_BASE_URL}/equipment/{equipment_id}/sensor-data", headers=HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Sensor Data Retrieval: PASSED ({len(data)} readings)")
            else:
                print(f"❌ Sensor Data Retrieval: FAILED (Status: {response.status_code})")
        else:
            print(f"❌ Sensor Data Submission: FAILED (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Sensor Data Operations: FAILED (Error: {e})")

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
            
        # Test docs UI (this will return HTML)
        response = requests.get(f"{API_BASE_URL}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ Swagger UI: ACCESSIBLE")
        else:
            print(f"❌ Swagger UI: FAILED (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ API Documentation: FAILED (Error: {e})")

def main():
    """Run all tests"""
    print("🚀 Starting Smart Maintenance SaaS UI Functionality Tests")
    print("=" * 60)
    
    # Test API connection
    if not test_api_connection():
        print("\n❌ API connection failed. Exiting tests.")
        return
    
    # Test equipment operations
    equipment_id = test_equipment_operations()
    
    # Test maintenance logs
    log_id = test_maintenance_logs(equipment_id)
    
    # Test sensor data
    test_sensor_data(equipment_id)
    
    # Test API documentation
    test_api_docs()
    
    print("\n" + "=" * 60)
    print("🏁 Test Suite Completed!")
    print("\n✨ Next steps:")
    print("   1. Open http://localhost:8501 to access the Streamlit UI")
    print("   2. Test the UI functionality manually")
    print("   3. Check http://localhost:8000/docs for API documentation")

if __name__ == "__main__":
    main()
