"""
Integration tests for PredictionAgent stateful logic.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from apps.agents.decision.prediction_agent import PredictionAgent
from core.database.crud.crud_sensor_reading import crud_sensor_reading
from core.events.event_bus import EventBus
from core.events.event_models import AnomalyValidatedEvent
from data.schemas import SensorReadingCreate, SensorType


@pytest.mark.asyncio
async def test_prediction_agent_fetches_real_historical_data(db_session: AsyncSession):
    """
    Test that PredictionAgent fetches real historical sensor data from the database
    when making predictions.
    """
    # Setup
    event_bus = EventBus()
    agent = PredictionAgent(
        agent_id="test_prediction_agent_stateful",
        event_bus=event_bus,
        crud_sensor_reading=crud_sensor_reading,
        db_session_factory=lambda: db_session,
        specific_settings={}
    )
    
    # Start the agent
    await agent.start()
    
    try:        # Create historical sensor data
        sensor_id = "temp_sensor_stateful_test"
        base_time = datetime.utcnow() - timedelta(days=15)  # Go back 15 days

        historical_readings = []
        for i in range(40):  # Create 40 historical readings (more than the minimum 30)
            reading_time = base_time + timedelta(hours=i * 8)  # Every 8 hours
            reading = SensorReadingCreate(
                sensor_id=sensor_id,
                value=25.0 + (i % 5),  # Values between 25-29
                timestamp=reading_time,
                sensor_type=SensorType.TEMPERATURE,
                unit="C",
                quality=1.0,
                metadata={"test": "historical_data"}
            )
            historical_readings.append(reading)
        
        # Insert historical data into the database
        for reading in historical_readings:
            await crud_sensor_reading.create_sensor_reading(db_session, obj_in=reading)
        
        # Mock the Prophet model to verify the data passed to it
        with patch('apps.agents.decision.prediction_agent.Prophet') as mock_prophet_class:
            import pandas as pd
            
            mock_prophet = Mock()
            mock_prophet_class.return_value = mock_prophet
            mock_prophet.fit.return_value = None
            
            # Create a mock DataFrame that behaves like a real Prophet forecast
            current_time = datetime.utcnow()
            forecast_data = []
            for i in range(100):  # 100 days of forecast
                date = current_time + timedelta(days=i)
                forecast_data.append({
                    'ds': date,
                    'yhat': 30.0 + i * 0.1,  # Gradually increasing values
                    'yhat_lower': 28.0 + i * 0.1,
                    'yhat_upper': 32.0 + i * 0.1
                })
            
            mock_forecast_df = pd.DataFrame(forecast_data)
            mock_prophet.predict.return_value = mock_forecast_df
            
            # Also mock make_future_dataframe
            future_data = []
            for i in range(130):  # Historical + future dates
                date = current_time - timedelta(days=30) + timedelta(days=i)
                future_data.append({'ds': date})
            mock_future_df = pd.DataFrame(future_data)
            mock_prophet.make_future_dataframe.return_value = mock_future_df
            
            # Create an AnomalyValidatedEvent to trigger prediction
            anomaly_event = AnomalyValidatedEvent(
                original_anomaly_alert_payload={
                    "id": str(uuid.uuid4()),
                    "sensor_id": sensor_id,
                    "anomaly_type": "temperature_spike",
                    "severity": 3,
                    "confidence": 0.85,
                    "description": "Temperature anomaly detected",
                    "evidence": {"threshold_exceeded": True},
                    "recommended_actions": ["inspect_sensor", "check_cooling_system"],
                    "status": "open"
                },
                triggering_reading_payload={
                    "sensor_id": sensor_id,
                    "value": 99.0,
                    "timestamp": datetime.utcnow().isoformat(),
                    "sensor_type": SensorType.TEMPERATURE.value,
                    "unit": "C"
                },
                validation_status="CONFIRMED",
                final_confidence=0.85,
                validation_reasons=["Threshold exceeded significantly"],
                agent_id="test_validation_agent"
            )
            
            # Publish the event
            await event_bus.publish(anomaly_event)
            
            # Wait for processing
            await asyncio.sleep(1.0)
            
            # Verify that Prophet was instantiated and used
            mock_prophet_class.assert_called_once()
            mock_prophet.fit.assert_called_once()
            
            # Get the data that was passed to fit()
            fit_call_args = mock_prophet.fit.call_args
            training_data = fit_call_args[0][0]  # First positional argument            # Verify that real historical data was used
            assert len(training_data) == 40, f"Expected 40 historical readings, got {len(training_data)}"
            assert 'ds' in training_data.columns, "Training data should have 'ds' (datetime) column"
            assert 'y' in training_data.columns, "Training data should have 'y' (value) column"
            
            # Verify the data values match our historical data
            values = training_data['y'].tolist()
            expected_values = [25.0 + (i % 5) for i in range(40)]  # 40 readings, not 20
            assert values == expected_values, f"Expected values {expected_values}, got {values}"
            
    finally:
        # Cleanup
        await agent.stop()


@pytest.mark.asyncio
async def test_prediction_agent_handles_no_historical_data(db_session: AsyncSession):
    """
    Test that PredictionAgent handles the case where no historical data is available.
    """
    # Setup
    event_bus = EventBus()
    agent = PredictionAgent(
        agent_id="test_prediction_agent_no_data",
        event_bus=event_bus,
        crud_sensor_reading=crud_sensor_reading,
        db_session_factory=lambda: db_session,
        specific_settings={}
    )
    
    # Start the agent
    await agent.start()
    
    try:
        # Create an AnomalyValidatedEvent for a sensor with no historical data
        sensor_id = "temp_sensor_no_history"
        anomaly_event = AnomalyValidatedEvent(
            original_anomaly_alert_payload={
                "id": str(uuid.uuid4()),
                "sensor_id": sensor_id,
                "anomaly_type": "temperature_spike",
                "severity": 3,
                "confidence": 0.85,
                "description": "Temperature anomaly detected",
                "evidence": {"threshold_exceeded": True},
                "recommended_actions": ["inspect_sensor"],
                "status": "open"
            },
            triggering_reading_payload={
                "sensor_id": sensor_id,
                "value": 99.0,
                "timestamp": datetime.utcnow().isoformat(),
                "sensor_type": SensorType.TEMPERATURE.value,
                "unit": "C"
            },
            validation_status="CONFIRMED",
            final_confidence=0.85,
            validation_reasons=["High temperature detected"],
            agent_id="test_validation_agent"
        )
        
        # Publish the event
        await event_bus.publish(anomaly_event)
        
        # Wait for processing
        await asyncio.sleep(1.0)
        
        # The agent should handle this gracefully without crashing
        # We can't easily verify the exact behavior without looking at logs,
        # but the test should complete without exceptions
        
    finally:
        # Cleanup
        await agent.stop()


@pytest.mark.asyncio
async def test_prediction_agent_uses_sufficient_historical_data(db_session: AsyncSession):
    """
    Test that PredictionAgent uses a sufficient amount of historical data for predictions.
    """
    # Setup
    event_bus = EventBus()
    agent = PredictionAgent(
        agent_id="test_prediction_agent_sufficient_data",
        event_bus=event_bus,
        crud_sensor_reading=crud_sensor_reading,
        db_session_factory=lambda: db_session,
        specific_settings={}
    )
    
    # Start the agent
    await agent.start()
    
    try:
        # Create a large amount of historical sensor data
        sensor_id = "temp_sensor_large_history"
        base_time = datetime.utcnow() - timedelta(days=30)
        
        historical_readings = []
        for i in range(100):  # Create 100 historical readings
            reading_time = base_time + timedelta(hours=i * 7.2)  # Every ~7 hours
            reading = SensorReadingCreate(
                sensor_id=sensor_id,
                value=20.0 + (i % 10),  # Values between 20-29
                timestamp=reading_time,
                sensor_type=SensorType.TEMPERATURE,
                unit="C",
                quality=1.0,
                metadata={"test": "large_dataset"}
            )
            historical_readings.append(reading)
        
        # Insert historical data into the database
        for reading in historical_readings:
            await crud_sensor_reading.create_sensor_reading(db_session, obj_in=reading)
        
        # Mock the Prophet model to verify the data passed to it
        with patch('apps.agents.decision.prediction_agent.Prophet') as mock_prophet_class:
            mock_prophet = Mock()
            mock_prophet_class.return_value = mock_prophet
            mock_prophet.fit.return_value = None
            mock_prophet.predict.return_value = Mock(
                to_dict=Mock(return_value={'yhat': [25.0], 'yhat_lower': [23.0], 'yhat_upper': [27.0]})
            )
            
            # Create an AnomalyValidatedEvent to trigger prediction
            anomaly_event = AnomalyValidatedEvent(
                original_anomaly_alert_payload={
                    "id": str(uuid.uuid4()),
                    "sensor_id": sensor_id,
                    "anomaly_type": "temperature_anomaly",
                    "severity": 2,
                    "confidence": 0.75,
                    "description": "Temperature pattern anomaly",
                    "evidence": {"pattern_deviation": True},
                    "recommended_actions": ["analyze_trend"],
                    "status": "open"
                },
                triggering_reading_payload={
                    "sensor_id": sensor_id,
                    "value": 45.0,
                    "timestamp": datetime.utcnow().isoformat(),
                    "sensor_type": SensorType.TEMPERATURE.value,
                    "unit": "C"
                },
                validation_status="CONFIRMED",
                final_confidence=0.75,
                validation_reasons=["Pattern deviation detected"],
                agent_id="test_validation_agent"
            )
            
            # Publish the event
            await event_bus.publish(anomaly_event)
            
            # Wait for processing
            await asyncio.sleep(1.0)
            
            # Verify that Prophet was used with the historical data
            mock_prophet_class.assert_called_once()
            mock_prophet.fit.assert_called_once()
            
            # Get the data that was passed to fit()
            fit_call_args = mock_prophet.fit.call_args
            training_data = fit_call_args[0][0]
            
            # Verify that a reasonable amount of historical data was used
            # (The agent might limit the data to avoid performance issues)
            assert len(training_data) >= 10, f"Expected at least 10 historical readings, got {len(training_data)}"
            assert len(training_data) <= 100, f"Expected at most 100 historical readings, got {len(training_data)}"
            
    finally:
        # Cleanup
        await agent.stop()
