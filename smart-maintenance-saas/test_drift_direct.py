#!/usr/bin/env python3
"""
Direct test of the drift detection endpoint
"""
import asyncio
import requests
import json
from datetime import datetime, timedelta

def test_drift_endpoint():
    """Test the drift detection endpoint directly"""
    base_url = "http://localhost:8000"
    
    # Prepare test data
    drift_data = {
        "sensor_id": "test_sensor_123",
        "window_minutes": 30,
        "p_value_threshold": 0.05,
        "min_samples": 10
    }
    
    print(f"Testing drift endpoint with payload: {json.dumps(drift_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/ml/check_drift",
            json=drift_data,
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Error response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_drift_endpoint()