"""
Model utility functions for intelligent model selection and MLflow integration.

This module provides functionality to query MLflow models and recommend
suitable models based on sensor type and other criteria.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from mlflow.tracking import MlflowClient
from mlflow.exceptions import MlflowException

# Set up logging
logger = logging.getLogger(__name__)

# MLflow configuration
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")


def _get_mlflow_client():
    """Get a configured MLflow client."""
    import mlflow
    import os
    
    # Set environment variables for MLflow
    os.environ['MLFLOW_TRACKING_URI'] = MLFLOW_TRACKING_URI
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    return MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)


def get_all_registered_models() -> List[Dict[str, Any]]:
    """
    Fetch all registered models from MLflow registry.
    
    Returns:
        List of dictionaries containing model information including name, version, tags, etc.
    """
    try:
        client = _get_mlflow_client()
        models = client.search_registered_models()
        model_info = []
        
        for model in models:
            # Get the latest version for each model
            try:
                versions = client.search_model_versions(f"name='{model.name}'")
                if versions:
                    # Sort by version number and get the latest
                    latest_version = max(versions, key=lambda v: int(v.version))
                    
                    model_data = {
                        'name': model.name,
                        'description': model.description,
                        'latest_version': latest_version.version,
                        'creation_timestamp': model.creation_timestamp,
                        'last_updated_timestamp': model.last_updated_timestamp,
                        'tags': model.tags or {},
                        'version_tags': latest_version.tags or {},
                        'current_stage': latest_version.current_stage,
                        'run_id': latest_version.run_id
                    }
                    model_info.append(model_data)
                    
            except Exception as e:
                logger.warning(f"Failed to get versions for model {model.name}: {e}")
                # Add basic model info even if we can't get version details
                model_data = {
                    'name': model.name,
                    'description': model.description,
                    'tags': model.tags or {},
                    'latest_version': 'unknown',
                    'version_tags': {},
                    'current_stage': 'unknown',
                    'run_id': 'unknown'
                }
                model_info.append(model_data)
        
        logger.info(f"Found {len(model_info)} registered models")
        return model_info
        
    except MlflowException as e:
        logger.error(f"MLflow error while fetching registered models: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error while fetching registered models: {e}")
        return []


def get_models_by_sensor_type() -> Dict[str, List[str]]:
    """
    Get models organized by sensor type based on MLflow tags and model name analysis.
    
    This function looks for models with 'sensor_type' tags and also infers types
    from model names to ensure proper categorization. Models without clear sensor
    affinity are categorized more carefully to prevent mismatches.
    
    Returns:
        Dictionary mapping sensor types to lists of model names.
        Example: {'bearing': ['nasa_bearing_model'], 'temperature': ['temp_anomaly_detector']}
    """
    try:
        models = get_all_registered_models()
        sensor_type_mapping = {}
        
        for model in models:
            model_name = model['name'].lower()
            
            # Check both model-level tags and version-level tags for sensor_type
            sensor_type = None
            
            # First check version-level tags (most specific)
            if 'sensor_type' in model.get('version_tags', {}):
                sensor_type = model['version_tags']['sensor_type']
            # Fallback to model-level tags
            elif 'sensor_type' in model.get('tags', {}):
                sensor_type = model['tags']['sensor_type']
            # Infer from model name if no explicit tags
            else:
                sensor_type = _infer_sensor_type_from_name(model_name.lower())
                logger.info(f"DEBUG: Model {model_name} -> inferred sensor_type: {sensor_type}")
            
            if sensor_type:
                sensor_type = sensor_type.lower().strip()
                if sensor_type not in sensor_type_mapping:
                    sensor_type_mapping[sensor_type] = []
                sensor_type_mapping[sensor_type].append(model['name'])
                logger.debug(f"Model {model['name']} categorized for sensor type: {sensor_type}")
            else:
                # Only add to 'general' if it's truly a general-purpose anomaly detector
                if _is_general_purpose_model(model_name.lower()):
                    if 'general' not in sensor_type_mapping:
                        sensor_type_mapping['general'] = []
                    sensor_type_mapping['general'].append(model['name'])
                    logger.debug(f"Model {model['name']} added to general category")
                else:
                    logger.warning(f"DEBUG: Model {model['name']} could not be categorized and is NOT general-purpose - skipping to prevent mismatches")
        
        logger.info(f"Organized models by sensor type: {sensor_type_mapping}")
        return sensor_type_mapping
        
    except Exception as e:
        logger.error(f"Error organizing models by sensor type: {e}")
        return {}


def _infer_sensor_type_from_name(model_name: str) -> Optional[str]:
    """
    Infer sensor type from model name using keyword matching.
    
    Args:
        model_name: The lowercase model name to analyze
        
    Returns:
        Inferred sensor type or None if unclear
    """
    # Vibration/bearing patterns
    if any(keyword in model_name for keyword in ['bearing', 'vibration', 'nasa', 'xjtu']):
        return 'vibration'
    
    # Audio patterns
    if any(keyword in model_name for keyword in ['audio', 'mimii', 'sound']):
        return 'audio'
    
    # Manufacturing/industrial patterns  
    if any(keyword in model_name for keyword in ['ai4i', 'manufacturing', 'industrial']):
        return 'manufacturing'
    
    # Pump patterns
    if 'pump' in model_name:
        return 'pump'
    
    # Forecasting patterns
    if any(keyword in model_name for keyword in ['prophet', 'forecast', 'time_series', 'sensor-001']):
        return 'forecasting'
    
    # Temperature patterns (for future models)
    if any(keyword in model_name for keyword in ['temperature', 'temp', 'thermal']):
        return 'temperature'
    
    # Pressure patterns (for future models)
    if any(keyword in model_name for keyword in ['pressure', 'press']):
        return 'pressure'
    
    return None


def _is_general_purpose_model(model_name: str) -> bool:
    """
    Determine if a model is truly general-purpose for anomaly detection.
    
    Args:
        model_name: The lowercase model name to analyze
        
    Returns:
        True if the model appears to be general-purpose, False otherwise
    """
    # General anomaly detection patterns that work with single features
    general_patterns = [
        'anomaly_detector_refined',
        'synthetic_validation',
        'realistic_sensor_validation'
    ]
    
    return any(pattern in model_name for pattern in general_patterns)


def get_model_recommendations(sensor_type: str, include_general: bool = True) -> List[str]:
    """
    Get recommended models for a specific sensor type with intelligent filtering.
    
    Args:
        sensor_type: The type of sensor (e.g., 'temperature', 'vibration', 'pressure')
        include_general: Whether to include general-purpose models that can handle single features
        
    Returns:
        List of recommended model names, prioritized by compatibility
    """
    try:
        sensor_type_mapping = get_models_by_sensor_type()
        recommendations = []
        
        # Normalize sensor type input
        sensor_type_lower = sensor_type.lower().strip()
        
        # Handle SensorType enum string representation
        if sensor_type_lower.startswith('sensortype.'):
            sensor_type_lower = sensor_type_lower.replace('sensortype.', '')
        
        # First priority: exact sensor type matches
        if sensor_type_lower in sensor_type_mapping:
            recommendations.extend(sensor_type_mapping[sensor_type_lower])
            logger.info(f"Found {len(sensor_type_mapping[sensor_type_lower])} specific models for {sensor_type_lower}")
        
        # Second priority: compatible related types
        compatible_types = _get_compatible_sensor_types(sensor_type_lower)
        for compatible_type in compatible_types:
            if compatible_type in sensor_type_mapping:
                for model in sensor_type_mapping[compatible_type]:
                    if model not in recommendations:
                        recommendations.append(model)
                        logger.debug(f"Added compatible model {model} from {compatible_type} category")
        
        # Third priority: general-purpose models (only if specifically requested and safe)
        if include_general and 'general' in sensor_type_mapping:
            for model in sensor_type_mapping['general']:
                if model not in recommendations:
                    recommendations.append(model)
                    logger.debug(f"Added general-purpose model {model}")
        
        # If no specific models found, provide safe fallback recommendations
        if not recommendations:
            recommendations = _get_fallback_recommendations(sensor_type_lower)
            logger.warning(f"No specific models found for {sensor_type_lower}, using fallback recommendations")
        
        logger.info(f"Final recommendations for sensor type '{sensor_type}': {recommendations}")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error getting model recommendations for sensor type '{sensor_type}': {e}")
        return _get_fallback_recommendations(sensor_type.lower())


def _get_compatible_sensor_types(sensor_type: str) -> List[str]:
    """
    Get sensor types that have compatible models for the given sensor type.
    
    Args:
        sensor_type: The primary sensor type
        
    Returns:
        List of compatible sensor types
    """
    compatibility_map = {
        'temperature': ['general'],  # Only general anomaly detectors work with single temp values
        'pressure': ['general'],     # Only general anomaly detectors work with single pressure values  
        'vibration': ['bearing'],    # Vibration analysis models often work for bearing data
        'bearing': ['vibration'],    # Bearing models often work for vibration data
        'audio': [],                 # Audio models require specific feature engineering
        'manufacturing': [],         # Manufacturing models have specific feature requirements
        'pump': ['general'],         # Pump-specific or general models
        'forecasting': []            # Forecasting models are very specific
    }
    
    return compatibility_map.get(sensor_type, [])


def _get_fallback_recommendations(sensor_type: str) -> List[str]:
    """
    Provide safe fallback recommendations when no specific models are available.
    
    Args:
        sensor_type: The sensor type needing recommendations
        
    Returns:
        List of safe fallback model names
    """
    # For single-value sensor types, only recommend models that can handle single features
    single_value_types = ['temperature', 'pressure', 'humidity', 'voltage']
    
    if sensor_type in single_value_types:
        return [
            'anomaly_detector_refined_v2',
            'synthetic_validation_isolation_forest',
            'realistic_sensor_validation_isolation_forest'
        ]
    
    # For vibration/bearing, include vibration-specific models
    if sensor_type in ['vibration', 'bearing']:
        return [
            'vibration_anomaly_isolationforest',
            'xjtu_anomaly_isolation_forest',
            'anomaly_detector_refined_v2'
        ]
    
    # For other types, be conservative and only recommend general models
    return [
        'anomaly_detector_refined_v2',
        'synthetic_validation_isolation_forest'
    ]


def get_model_details(model_name: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific model.
    
    Args:
        model_name: Name of the model to get details for
        
    Returns:
        Dictionary containing detailed model information or None if not found
    """
    try:
        models = get_all_registered_models()
        for model in models:
            if model['name'] == model_name:
                return model
        
        logger.warning(f"Model '{model_name}' not found in registry")
        return None
        
    except Exception as e:
        logger.error(f"Error getting details for model '{model_name}': {e}")
        return None


def suggest_sensor_types() -> List[str]:
    """
    Get a list of available sensor types based on registered models.
    
    Returns:
        List of sensor types that have associated models
    """
    try:
        sensor_type_mapping = get_models_by_sensor_type()
        sensor_types = list(sensor_type_mapping.keys())
        
        # Remove 'general' from the list of specific sensor types
        if 'general' in sensor_types:
            sensor_types.remove('general')
        
        # Add some common sensor types that might not have models yet
        common_types = ['bearing', 'manufacturing', 'audio', 'forecasting', 'general', 'temperature', 'pressure', 'vibration', 'pump']
        for sensor_type in common_types:
            if sensor_type not in sensor_types:
                sensor_types.append(sensor_type)
        
        sensor_types.sort()
        logger.info(f"Available sensor types: {sensor_types}")
        return sensor_types
        
    except Exception as e:
        logger.error(f"Error getting sensor types: {e}")
        return ['bearing', 'manufacturing', 'audio', 'forecasting', 'general', 'temperature', 'pressure', 'vibration', 'pump']  # Fallback


def add_sensor_type_tag(model_name: str, version: str, sensor_type: str) -> bool:
    """
    Add a sensor_type tag to a model version.
    
    This is a utility function to help tag existing models with sensor types.
    
    Args:
        model_name: Name of the model
        version: Version of the model
        sensor_type: Sensor type to tag the model with
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = _get_mlflow_client()
        client.set_model_version_tag(model_name, version, "sensor_type", sensor_type)
        logger.info(f"Successfully tagged model {model_name} v{version} with sensor_type: {sensor_type}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to tag model {model_name} v{version} with sensor_type {sensor_type}: {e}")
        return False


if __name__ == "__main__":
    """Test the model utility functions."""
    print("=== Testing Model Utility Functions ===")
    
    print("\n1. Getting all registered models:")
    models = get_all_registered_models()
    for model in models:
        print(f"  - {model['name']} (v{model['latest_version']}) - Tags: {model.get('tags', {})}")
    
    print("\n2. Getting models by sensor type:")
    sensor_mapping = get_models_by_sensor_type()
    for sensor_type, model_list in sensor_mapping.items():
        print(f"  {sensor_type}: {model_list}")
    
    print("\n3. Getting sensor type suggestions:")
    sensor_types = suggest_sensor_types()
    print(f"  Available sensor types: {sensor_types}")
    
    print("\n4. Getting recommendations for 'bearing' sensor type:")
    recommendations = get_model_recommendations('bearing')
    print(f"  Recommendations: {recommendations}")
    
    print("\n=== Test Complete ===")