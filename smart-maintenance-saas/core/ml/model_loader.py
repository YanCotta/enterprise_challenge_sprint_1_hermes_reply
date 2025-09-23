"""
MLflow Model Loader for Smart Maintenance SaaS.

This module provides "serverless" model loading capabilities that dynamically
load pre-trained models from MLflow/S3 based on sensor types and requirements.
"""

import os
import logging
import pickle
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

import mlflow
import mlflow.pyfunc
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from mlflow.exceptions import MlflowException

# Configure S3 connection pooling for MLflow
import urllib3
from botocore.config import Config
import boto3

from apps.ml.model_utils import (
    get_model_recommendations, 
    get_model_details, 
    get_all_registered_models
)
from data.exceptions import MLModelError, ConfigurationError
from data.schemas import SensorReading


class ModelCache:
    """Simple in-memory model cache with TTL support."""
    
    def __init__(self, ttl_minutes: int = 60):
        self.cache = {}
        self.timestamps = {}
        self.ttl_minutes = ttl_minutes
        self.logger = logging.getLogger(f"{__name__}.ModelCache")
    
    def get(self, key: str) -> Optional[Any]:
        """Get a cached model if it exists and hasn't expired."""
        if key not in self.cache:
            return None
        
        # Check if cache entry has expired
        if datetime.utcnow() - self.timestamps[key] > timedelta(minutes=self.ttl_minutes):
            self.logger.debug(f"Cache entry for {key} has expired, removing")
            del self.cache[key]
            del self.timestamps[key]
            return None
        
        self.logger.debug(f"Cache hit for {key}")
        return self.cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """Store a model in cache."""
        self.cache[key] = value
        self.timestamps[key] = datetime.utcnow()
        self.logger.debug(f"Cached model for {key}")
    
    def clear(self) -> None:
        """Clear all cached models."""
        self.cache.clear()
        self.timestamps.clear()
        self.logger.info("Model cache cleared")


class MLflowModelLoader:
    """
    Production-ready MLflow model loader with caching and error handling.
    
    Features:
    - Dynamic model loading based on sensor type
    - Intelligent model selection using MLflow registry
    - In-memory caching with TTL
    - Graceful fallbacks and error handling
    - Async-friendly design for high-performance loading
    """
    
    def __init__(self, 
                 mlflow_uri: Optional[str] = None,
                 cache_ttl_minutes: int = 60,
                 max_concurrent_loads: int = 3,
                 enable_fallback: bool = True):
        """
        Initialize the MLflow model loader.
        
        Args:
            mlflow_uri: MLflow tracking URI (defaults to env var)
            cache_ttl_minutes: Time-to-live for cached models in minutes
            max_concurrent_loads: Maximum concurrent model loading operations
            enable_fallback: Whether to enable fallback to general models
        """
        self.mlflow_uri = mlflow_uri or os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
        self.enable_fallback = enable_fallback
        self.cache = ModelCache(ttl_minutes=cache_ttl_minutes)
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_loads)
        self.logger = logging.getLogger(f"{__name__}.MLflowModelLoader")
        
        # Initialize MLflow client
        self._initialize_mlflow()
        
        # Track loading statistics
        self.stats = {
            'models_loaded': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'load_failures': 0,
            'fallback_uses': 0
        }
        
        self.logger.info(f"MLflowModelLoader initialized with URI: {self.mlflow_uri}")
    
    def _initialize_mlflow(self) -> None:
        """Initialize MLflow tracking configuration with optimized S3 connection pooling."""
        try:
            # Configure S3 connection pooling to prevent connection pool exhaustion
            s3_config = Config(
                max_pool_connections=50,  # Increase connection pool size
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-2')
            )
            
            # Set environment variables for boto3/S3 optimization
            os.environ['AWS_MAX_ATTEMPTS'] = '3'
            os.environ['AWS_RETRY_MODE'] = 'adaptive'
            
            # Configure urllib3 connection pooling
            urllib3.util.connection.HAS_IPV6 = False  # Disable IPv6 if not needed
            
            # Initialize MLflow with S3 optimizations
            os.environ['MLFLOW_TRACKING_URI'] = self.mlflow_uri
            os.environ['MLFLOW_S3_ENDPOINT_URL'] = os.getenv('MLFLOW_S3_ENDPOINT_URL', '')
            
            mlflow.set_tracking_uri(self.mlflow_uri)
            self.client = MlflowClient(tracking_uri=self.mlflow_uri)
            
            self.logger.info(f"MLflow client initialized successfully with S3 connection pooling optimization")
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize MLflow client: {e}") from e
    
    async def load_model_for_sensor(self, 
                                  sensor_reading: SensorReading,
                                  model_name: Optional[str] = None,
                                  include_preprocessor: bool = True) -> Tuple[Any, Optional[Any]]:
        """
        Load the best model for a given sensor reading.
        
        Args:
            sensor_reading: The sensor reading to find a model for
            model_name: Specific model name (overrides automatic selection)
            include_preprocessor: Whether to load associated preprocessors/scalers
            
        Returns:
            Tuple of (model, preprocessor) or (model, None)
            
        Raises:
            MLModelError: If no suitable model can be loaded
        """
        try:
            # Determine sensor type from reading
            sensor_type = self._infer_sensor_type(sensor_reading)
            
            # Use specific model or auto-select
            if model_name:
                selected_models = [model_name]
                self.logger.info(f"Using specified model: {model_name}")
            else:
                selected_models = get_model_recommendations(
                    sensor_type, 
                    include_general=self.enable_fallback
                )
                self.logger.info(f"Auto-selected models for {sensor_type}: {selected_models}")
            
            if not selected_models:
                raise MLModelError(f"No models available for sensor type: {sensor_type}")
            
            # Try to load models in priority order
            for model_name in selected_models:
                try:
                    return await self._load_model_with_cache(
                        model_name, 
                        include_preprocessor=include_preprocessor
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to load model {model_name}: {e}")
                    continue
            
            # If we get here, all models failed to load
            self.stats['load_failures'] += 1
            raise MLModelError(f"Failed to load any suitable model for sensor type: {sensor_type}")
            
        except MLModelError:
            raise
        except Exception as e:
            self.stats['load_failures'] += 1
            raise MLModelError(f"Error loading model for sensor {sensor_reading.sensor_id}: {e}") from e
    
    async def _load_model_with_cache(self, 
                                   model_name: str,
                                   version: Optional[str] = None,
                                   include_preprocessor: bool = True) -> Tuple[Any, Optional[Any]]:
        """
        Load a model with caching support.
        
        Args:
            model_name: Name of the model in MLflow registry
            version: Specific version (defaults to latest)
            include_preprocessor: Whether to load preprocessors
            
        Returns:
            Tuple of (model, preprocessor)
        """
        # Create cache key
        version_str = version or "latest"
        cache_key = f"{model_name}:{version_str}:preprocessor={include_preprocessor}"
        
        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            self.stats['cache_hits'] += 1
            self.logger.debug(f"Loaded {model_name} from cache")
            return cached_result
        
        self.stats['cache_misses'] += 1
        
        # Load model in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            self._load_model_sync,
            model_name,
            version,
            include_preprocessor
        )
        
        # Cache the result
        self.cache.set(cache_key, result)
        self.stats['models_loaded'] += 1
        
        return result
    
    def _load_model_sync(self, 
                        model_name: str,
                        version: Optional[str] = None,
                        include_preprocessor: bool = True) -> Tuple[Any, Optional[Any]]:
        """
        Synchronous model loading (runs in thread pool).
        
        Args:
            model_name: Name of the model in MLflow registry
            version: Specific version (defaults to latest)
            include_preprocessor: Whether to load preprocessors
            
        Returns:
            Tuple of (model, preprocessor)
        """
        try:
            # Construct model URI
            if version:
                model_uri = f"models:/{model_name}/{version}"
            else:
                model_uri = f"models:/{model_name}/latest"
            
            self.logger.info(f"Loading model from URI: {model_uri}")
            
            # Load the main model
            model = mlflow.pyfunc.load_model(model_uri)
            
            preprocessor = None
            if include_preprocessor:
                # Try to load associated preprocessor/scaler
                preprocessor = self._load_preprocessor(model_name, version)
            
            self.logger.info(f"Successfully loaded model: {model_name}")
            return model, preprocessor
            
        except MlflowException as e:
            raise MLModelError(f"MLflow error loading model {model_name}: {e}") from e
        except Exception as e:
            raise MLModelError(f"Unexpected error loading model {model_name}: {e}") from e
    
    def _load_preprocessor(self, 
                          model_name: str, 
                          version: Optional[str] = None) -> Optional[Any]:
        """
        Load associated preprocessor (e.g., scaler) for a model.
        
        Args:
            model_name: Name of the model
            version: Version of the model
            
        Returns:
            Preprocessor object or None if not found
        """
        try:
            # Common preprocessor naming patterns
            preprocessor_patterns = [
                f"{model_name}_scaler",
                f"{model_name.replace('_', ' ').title().replace(' ', '_')}_Scaler",
                f"scaler_{model_name}",
                # Add more patterns as needed based on your naming conventions
            ]
            
            for pattern in preprocessor_patterns:
                try:
                    if version:
                        preprocessor_uri = f"models:/{pattern}/{version}"
                    else:
                        preprocessor_uri = f"models:/{pattern}/latest"
                    
                    preprocessor = mlflow.pyfunc.load_model(preprocessor_uri)
                    self.logger.info(f"Loaded preprocessor: {pattern}")
                    return preprocessor
                    
                except MlflowException:
                    continue  # Try next pattern
            
            # Try to load as artifacts from the main model's run
            return self._load_preprocessor_from_artifacts(model_name, version)
            
        except Exception as e:
            self.logger.warning(f"Could not load preprocessor for {model_name}: {e}")
            return None
    
    def _load_preprocessor_from_artifacts(self, 
                                        model_name: str, 
                                        version: Optional[str] = None) -> Optional[Any]:
        """
        Try to load preprocessor from model run artifacts.
        
        Args:
            model_name: Name of the model
            version: Version of the model
            
        Returns:
            Preprocessor object or None if not found
        """
        try:
            # Get model version details to find run_id
            if version:
                model_version = self.client.get_model_version(model_name, version)
            else:
                versions = self.client.search_model_versions(f"name='{model_name}'")
                if not versions:
                    return None
                model_version = max(versions, key=lambda v: int(v.version))
            
            run_id = model_version.run_id
            
            # Common artifact paths for preprocessors
            artifact_patterns = [
                "scaler.pkl",
                "preprocessor.pkl", 
                "scaler/model.pkl",
                "preprocessor/model.pkl"
            ]
            
            for artifact_path in artifact_patterns:
                try:
                    artifact_uri = f"runs:/{run_id}/{artifact_path}"
                    # Try to download and load the artifact
                    local_path = mlflow.artifacts.download_artifacts(artifact_uri)
                    
                    with open(local_path, 'rb') as f:
                        preprocessor = pickle.load(f)
                    
                    self.logger.info(f"Loaded preprocessor from artifacts: {artifact_path}")
                    return preprocessor
                    
                except Exception:
                    continue  # Try next pattern
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Could not load preprocessor from artifacts for {model_name}: {e}")
            return None
    
    def _infer_sensor_type(self, sensor_reading: SensorReading) -> str:
        """
        Infer sensor type from sensor reading.
        
        Args:
            sensor_reading: The sensor reading to analyze
            
        Returns:
            Inferred sensor type string
        """
        sensor_id = sensor_reading.sensor_id.lower()
        sensor_type = str(getattr(sensor_reading, 'sensor_type', '')).lower() if hasattr(sensor_reading, 'sensor_type') else ''
        
        # Direct sensor type mapping
        if sensor_type:
            return sensor_type
        
        # Infer from sensor ID patterns
        if any(keyword in sensor_id for keyword in ['bearing', 'bear']):
            return 'bearing'
        elif any(keyword in sensor_id for keyword in ['pump', 'flow']):
            return 'pump' 
        elif any(keyword in sensor_id for keyword in ['vibr', 'vib', 'accel']):
            return 'vibration'
        elif any(keyword in sensor_id for keyword in ['temp', 'temperature']):
            return 'temperature'
        elif any(keyword in sensor_id for keyword in ['press', 'pressure']):
            return 'pressure'
        elif any(keyword in sensor_id for keyword in ['audio', 'sound', 'mic']):
            return 'audio'
        else:
            return 'general'
    
    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a model without loading it.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model information dictionary or None if not found
        """
        try:
            return get_model_details(model_name)
        except Exception as e:
            self.logger.error(f"Error getting model info for {model_name}: {e}")
            return None
    
    async def list_available_models(self, sensor_type: Optional[str] = None) -> List[str]:
        """
        List available models, optionally filtered by sensor type.
        
        Args:
            sensor_type: Optional sensor type filter
            
        Returns:
            List of available model names
        """
        try:
            if sensor_type:
                return get_model_recommendations(sensor_type, include_general=True)
            else:
                models = get_all_registered_models()
                return [model['name'] for model in models]
        except Exception as e:
            self.logger.error(f"Error listing models: {e}")
            return []
    
    def clear_cache(self) -> None:
        """Clear the model cache."""
        self.cache.clear()
        self.logger.info("Model cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get loader statistics."""
        return {
            **self.stats,
            'cache_size': len(self.cache.cache),
            'cache_hit_rate': (
                self.stats['cache_hits'] / max(1, self.stats['cache_hits'] + self.stats['cache_misses'])
            ) * 100
        }
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


# Global model loader instance (singleton pattern)
_model_loader = None


def get_model_loader(**kwargs) -> MLflowModelLoader:
    """
    Get the global model loader instance (singleton).
    
    Args:
        **kwargs: Configuration parameters for first-time initialization
        
    Returns:
        Global MLflowModelLoader instance
    """
    global _model_loader
    if _model_loader is None:
        _model_loader = MLflowModelLoader(**kwargs)
    return _model_loader


async def load_model_for_sensor(sensor_reading: SensorReading, 
                              model_name: Optional[str] = None) -> Tuple[Any, Optional[Any]]:
    """
    Convenience function to load a model for a sensor reading.
    
    Args:
        sensor_reading: The sensor reading to find a model for
        model_name: Optional specific model name
        
    Returns:
        Tuple of (model, preprocessor)
    """
    loader = get_model_loader()
    return await loader.load_model_for_sensor(sensor_reading, model_name)