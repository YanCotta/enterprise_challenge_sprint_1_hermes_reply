#!/usr/bin/env python3
"""
Script to tag MLflow models with appropriate sensor types based on their dataset and purpose.

This script analyzes the registered models and adds 'sensor_type' tags to help with
intelligent model selection in the UI.
"""

import mlflow
import os
from mlflow.tracking import MlflowClient

# MLflow configuration
tracking_uri = "http://mlflow:5000" if os.getenv("DOCKER_ENV") == "true" else "http://localhost:5000"
mlflow.set_tracking_uri(tracking_uri)
client = MlflowClient()

# Model to sensor type mapping based on the notebook analysis
MODEL_SENSOR_MAPPINGS = {
    # AI4I Dataset - Industrial machine classification (general manufacturing equipment)
    "ai4i_classifier_lightgbm_baseline": "manufacturing",
    "ai4i_classifier_lightgbm_engineered": "manufacturing", 
    "ai4i_classifier_randomforest_baseline": "manufacturing",
    "ai4i_classifier_randomforest_engineered": "manufacturing",
    "ai4i_classifier_svc_baseline": "manufacturing",
    "ai4i_classifier_svc_engineered": "manufacturing",
    
    # NASA Bearing Dataset - Vibration analysis for bearing health
    "vibration_anomaly_isolationforest": "bearing",
    "vibration_anomaly_oneclasssvm": "bearing",
    
    # XJTU Bearing Dataset - Advanced bearing vibration analysis
    "xjtu_anomaly_isolation_forest": "bearing",
    "xjtu_feature_scaler": "bearing",
    
    # MIMII Audio Dataset - Industrial equipment sound analysis
    "RandomForest_MIMII_Audio_Benchmark": "audio",
    "MIMII_Audio_Scaler": "audio",
    
    # Pump Classification - Kaggle pump sensor data
    # Note: Based on notebook 08, this uses pump maintenance sensor data
    # We'll need to check if any pump models were registered
    
    # Synthetic and validation models - General purpose
    "anomaly_detector_refined_v2": "general",
    "anomaly_detector_validation": "general",
    "synthetic_validation_isolation_forest": "general",
    
    # Forecasting models - Time series prediction (general)
    "lightgbm_forecaster_challenger": "forecasting",
    "prophet_forecaster_enhanced_sensor-001": "forecasting",
}

# Extended sensor type descriptions for UI display
SENSOR_TYPE_DESCRIPTIONS = {
    "bearing": "Bearing Vibration Analysis - Detects bearing degradation through vibration signals",
    "manufacturing": "Manufacturing Equipment - General industrial equipment failure prediction", 
    "audio": "Audio Analysis - Industrial equipment sound-based anomaly detection",
    "pump": "Pump Systems - Pump operational status and maintenance prediction",
    "forecasting": "Time Series Forecasting - Predictive analytics for sensor readings",
    "general": "General Purpose - Multi-purpose anomaly detection and validation"
}

def add_sensor_type_tags():
    """Add sensor_type tags to registered models."""
    print("🏷️  Starting model tagging process...")
    print("=" * 60)
    
    # Get all registered models
    models = client.search_registered_models()
    
    tagged_count = 0
    
    for model in models:
        model_name = model.name
        
        # Get the latest version
        try:
            versions = client.search_model_versions(f"name='{model_name}'")
            if not versions:
                print(f"⚠️  No versions found for model: {model_name}")
                continue
                
            latest_version = max(versions, key=lambda v: int(v.version))
            version_number = latest_version.version
            
            # Check if sensor_type tag already exists
            existing_tags = latest_version.tags or {}
            
            if 'sensor_type' in existing_tags:
                print(f"✅ Model {model_name} v{version_number} already tagged: {existing_tags['sensor_type']}")
                continue
            
            # Determine sensor type
            if model_name in MODEL_SENSOR_MAPPINGS:
                sensor_type = MODEL_SENSOR_MAPPINGS[model_name]
                
                # Add the tag
                client.set_model_version_tag(model_name, version_number, "sensor_type", sensor_type)
                
                # Also add a description tag
                if sensor_type in SENSOR_TYPE_DESCRIPTIONS:
                    client.set_model_version_tag(
                        model_name, 
                        version_number, 
                        "sensor_description", 
                        SENSOR_TYPE_DESCRIPTIONS[sensor_type]
                    )
                
                print(f"🏷️  Tagged {model_name} v{version_number} -> sensor_type: {sensor_type}")
                tagged_count += 1
                
            else:
                print(f"❓ Unknown model pattern: {model_name} (skipping)")
                
        except Exception as e:
            print(f"❌ Error processing model {model_name}: {e}")
    
    print("=" * 60)
    print(f"✨ Tagging complete! Tagged {tagged_count} models.")
    
    # Display final summary
    print("\n📊 Model Summary by Sensor Type:")
    sensor_counts = {}
    
    models = client.search_registered_models()
    for model in models:
        try:
            versions = client.search_model_versions(f"name='{model.name}'")
            if versions:
                latest_version = max(versions, key=lambda v: int(v.version))
                tags = latest_version.tags or {}
                sensor_type = tags.get('sensor_type', 'untagged')
                
                if sensor_type not in sensor_counts:
                    sensor_counts[sensor_type] = []
                sensor_counts[sensor_type].append(model.name)
        except:
            continue
    
    for sensor_type, models in sensor_counts.items():
        print(f"  {sensor_type}: {len(models)} models")
        for model_name in models[:3]:  # Show first 3
            print(f"    - {model_name}")
        if len(models) > 3:
            print(f"    ... and {len(models) - 3} more")

if __name__ == "__main__":
    add_sensor_type_tags()