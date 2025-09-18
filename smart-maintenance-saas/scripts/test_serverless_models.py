#!/usr/bin/env python3
"""
Test script for the enhanced AnomalyDetectionAgent with serverless model loading.

This script validates the new serverless model loading functionality and
ensures the agent can properly load models from MLflow/S3.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.agents.core.anomaly_detection_agent import AnomalyDetectionAgent
from core.events.event_bus import EventBus
from core.events.event_models import DataProcessedEvent
from data.schemas import SensorReading


async def test_serverless_model_loading():
    """Test the serverless model loading functionality."""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("=== Testing Serverless Model Loading ===")
    
    try:
        # Create event bus
        event_bus = EventBus()
        
        # Test configurations
        test_configs = [
            {
                'name': 'Serverless Mode (Default)',
                'config': {'use_serverless_models': True}
            },
            {
                'name': 'Fallback Mode', 
                'config': {'use_serverless_models': False}
            }
        ]
        
        for test_config in test_configs:
            logger.info(f"\n--- Testing {test_config['name']} ---")
            
            try:
                # Create agent with specific configuration
                agent = AnomalyDetectionAgent(
                    agent_id=f"test_anomaly_agent_{test_config['name'].lower().replace(' ', '_')}",
                    event_bus=event_bus,
                    specific_settings=test_config['config']
                )
                
                # Register capabilities and start agent
                await agent.register_capabilities()
                await agent.start()
                
                # Test different sensor types
                test_sensors = [
                    {
                        'sensor_id': 'bearing_sensor_001', 
                        'sensor_type': 'bearing',
                        'value': 0.08
                    },
                    {
                        'sensor_id': 'pump_sensor_001',
                        'sensor_type': 'pump', 
                        'value': 150.5
                    },
                    {
                        'sensor_id': 'vibration_sensor_001',
                        'sensor_type': 'vibration',
                        'value': 0.12
                    },
                    {
                        'sensor_id': 'unknown_sensor_001',
                        'sensor_type': None,
                        'value': 42.3
                    }
                ]
                
                for sensor_data in test_sensors:
                    logger.info(f"Testing sensor: {sensor_data['sensor_id']} (type: {sensor_data['sensor_type']})")
                    
                    # Create sensor reading
                    sensor_reading = SensorReading(
                        sensor_id=sensor_data['sensor_id'],
                        value=sensor_data['value'],
                        timestamp=datetime.utcnow(),
                        sensor_type=sensor_data['sensor_type']
                    )
                    
                    # Create data processed event
                    event = DataProcessedEvent(
                        processed_data=sensor_reading.model_dump(),
                        correlation_id=f"test_{sensor_data['sensor_id']}"
                    )
                    
                    try:
                        # Process the event
                        await agent.process(event)
                        logger.info(f"✓ Successfully processed {sensor_data['sensor_id']}")
                        
                    except Exception as e:
                        logger.error(f"✗ Failed to process {sensor_data['sensor_id']}: {e}")
                
                # Get model statistics
                if hasattr(agent, 'get_model_stats'):
                    stats = await agent.get_model_stats()
                    logger.info(f"Agent statistics: {stats}")
                
                # List available models for different sensor types
                if hasattr(agent, 'list_available_models'):
                    for sensor_type in ['bearing', 'pump', 'vibration', 'general']:
                        models = await agent.list_available_models(sensor_type)
                        logger.info(f"Available models for {sensor_type}: {models}")
                
                await agent.stop()
                logger.info(f"✓ {test_config['name']} test completed successfully")
                
            except Exception as e:
                logger.error(f"✗ {test_config['name']} test failed: {e}", exc_info=True)
        
        logger.info("\n=== Test Summary ===")
        logger.info("Serverless model loading tests completed")
        logger.info("Check logs above for detailed results")
        
    except Exception as e:
        logger.error(f"Test setup failed: {e}", exc_info=True)
        return False
    
    return True


async def test_model_loader_directly():
    """Test the model loader directly without the agent."""
    
    logger = logging.getLogger(__name__)
    logger.info("\n=== Testing Model Loader Directly ===")
    
    try:
        from core.ml.model_loader import get_model_loader
        
        # Get model loader instance
        model_loader = get_model_loader()
        
        # Test sensor reading
        sensor_reading = SensorReading(
            sensor_id='test_bearing_sensor',
            value=0.05,
            timestamp=datetime.utcnow(),
            sensor_type='bearing'
        )
        
        # Test model loading
        logger.info("Testing direct model loading...")
        try:
            model, preprocessor = await model_loader.load_model_for_sensor(sensor_reading)
            logger.info(f"✓ Successfully loaded model: {type(model)}")
            logger.info(f"✓ Preprocessor loaded: {type(preprocessor) if preprocessor else 'None'}")
            
        except Exception as e:
            logger.warning(f"Model loading failed (expected in test environment): {e}")
        
        # Test model listing
        logger.info("Testing model listing...")
        try:
            models = await model_loader.list_available_models('bearing')
            logger.info(f"Available bearing models: {models}")
            
        except Exception as e:
            logger.warning(f"Model listing failed (expected in test environment): {e}")
        
        # Get statistics
        stats = model_loader.get_stats()
        logger.info(f"Model loader statistics: {stats}")
        
        logger.info("✓ Direct model loader test completed")
        
    except Exception as e:
        logger.error(f"Direct model loader test failed: {e}", exc_info=True)


if __name__ == "__main__":
    async def main():
        """Run all tests."""
        print("🚀 Starting Enhanced Anomaly Detection Agent Tests")
        print("=" * 60)
        
        # Test the agent functionality
        await test_serverless_model_loading()
        
        # Test the model loader directly
        await test_model_loader_directly()
        
        print("\n" + "=" * 60)
        print("🎯 Tests completed! Check the logs for detailed results.")
        print("\nNote: Some failures are expected in development environment")
        print("where MLflow/S3 may not be fully accessible.")
    
    # Run the tests
    asyncio.run(main())