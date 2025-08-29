"""
ML module for Smart Maintenance SaaS.

This module contains machine learning utilities, feature engineering,
model training/inference code, and intelligent model selection.
"""

from .features import SensorFeatureTransformer
from .model_utils import (
    get_all_registered_models,
    get_models_by_sensor_type,
    get_model_recommendations,
    suggest_sensor_types,
    get_model_details
)

__all__ = [
    'SensorFeatureTransformer',
    'get_all_registered_models',
    'get_models_by_sensor_type', 
    'get_model_recommendations',
    'suggest_sensor_types',
    'get_model_details'
]
