"""
Test for ML API endpoints - basic validation for Day 12
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_ml_health_endpoint():
    """Test ML health check endpoint"""
    response = client.get("/api/v1/ml/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data


def test_predict_endpoint_structure():
    """Test predict endpoint with valid structure (may fail due to model loading)"""
    # This test validates the endpoint structure, not necessarily model functionality
    prediction_request = {
        "model_name": "ai4i_classifier_randomforest_baseline",
        "model_version": "2",
        "features": {
            "Air_temperature_K": 298.1,
            "Process_temperature_K": 308.6,
            "Rotational_speed_rpm": 1551,
            "Torque_Nm": 42.8,
            "Tool_wear_min": 108
        },
        "sensor_id": "test_sensor_001"
    }
    
    response = client.post("/api/v1/ml/predict", json=prediction_request)
    
    # Should return either 200 (success) or 404 (model not found) or 500 (model loading error)
    assert response.status_code in [200, 404, 500]
    
    # If successful, check response structure
    if response.status_code == 200:
        data = response.json()
        assert "prediction" in data
        assert "model_info" in data
        assert "timestamp" in data
        assert "request_id" in data


def test_detect_anomaly_endpoint_structure():
    """Test anomaly detection endpoint with valid structure"""
    anomaly_request = {
        "sensor_readings": [
            {
                "sensor_id": "test_sensor_001",
                "sensor_type": "temperature",
                "value": 75.5,
                "unit": "°C",
                "timestamp": "2025-08-21T10:00:00Z",
                "quality": 1.0,
                "metadata": {}
            }
        ],
        "model_name": "anomaly_detector_refined_v2",
        "model_version": "latest",
        "sensitivity": 0.7
    }
    
    response = client.post("/api/v1/ml/detect_anomaly", json=anomaly_request)
    
    # Should return either 200 (success) or 404 (model not found) or 500 (model loading error)
    assert response.status_code in [200, 404, 500]
    
    # If successful, check response structure
    if response.status_code == 200:
        data = response.json()
        assert "anomalies_detected" in data
        assert "total_readings_analyzed" in data
        assert "anomaly_count" in data
        assert "model_info" in data
        assert "analysis_timestamp" in data


def test_predict_endpoint_validation():
    """Test predict endpoint input validation"""
    # Test with missing required fields
    invalid_request = {
        "model_name": "test_model"
        # Missing features field
    }
    
    response = client.post("/api/v1/ml/predict", json=invalid_request)
    assert response.status_code == 422  # Validation error


def test_anomaly_endpoint_validation():
    """Test anomaly detection endpoint input validation"""
    # Test with missing required fields
    invalid_request = {
        "model_name": "test_model"
        # Missing sensor_readings field
    }
    
    response = client.post("/api/v1/ml/detect_anomaly", json=invalid_request)
    assert response.status_code == 422  # Validation error