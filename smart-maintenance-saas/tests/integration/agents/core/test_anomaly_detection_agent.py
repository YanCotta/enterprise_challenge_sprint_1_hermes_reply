"""Integration tests for AnomalyDetectionAgent."""

import asyncio
import logging
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.agents.core.anomaly_detection_agent import AnomalyDetectionAgent
from core.events.event_bus import EventBus
from core.events.event_models import DataProcessedEvent
from data.schemas import SensorReading, SensorType


class TestAnomalyDetectionAgentIntegration:
    """Integration tests for the AnomalyDetectionAgent."""

    @pytest.fixture
    async def event_bus(self):
        """Create a test EventBus instance."""
        return EventBus()

    @pytest.fixture
    async def agent(self, event_bus):
        """Create an AnomalyDetectionAgent instance for testing."""
        agent = AnomalyDetectionAgent(
            agent_id="test_anomaly_agent",
            event_bus=event_bus
        )
        return agent

    @pytest.fixture
    def sample_sensor_reading(self):
        """Create a sample sensor reading for testing."""
        return SensorReading(
            sensor_id="sensor_temp_001",
            value=25.3,
            timestamp=datetime.utcnow(),
            sensor_type=SensorType.TEMPERATURE,
            unit="celsius",
            quality=1.0,
            correlation_id=uuid.uuid4(),
            metadata={"location": "room_A", "building": "main"}
        )

    @pytest.fixture
    def sample_data_processed_event(self, sample_sensor_reading):
        """Create a sample DataProcessedEvent for testing."""
        return DataProcessedEvent(
            processed_data=sample_sensor_reading.dict(),
            original_event_id=uuid.uuid4(),
            source_sensor_id=sample_sensor_reading.sensor_id
        )

    async def test_agent_initialization(self, agent):
        """Test that the agent initializes correctly."""
        assert agent.agent_id == "test_anomaly_agent"
        assert agent.status == "initializing"
        assert len(agent.capabilities) == 0  # Before registration
        assert agent.isolation_forest_fitted is False
        assert agent.scaler is not None
        assert agent.isolation_forest is not None
        assert agent.statistical_detector is not None
        assert len(agent.historical_data_store) > 0

    async def test_agent_capability_registration(self, agent):
        """Test that the agent registers its capabilities correctly."""
        await agent.register_capabilities()
        
        assert len(agent.capabilities) == 1
        capability = agent.capabilities[0]
        assert capability.name == "detect_anomalies"
        assert capability.description == "Detects anomalies in processed sensor data using ML models."
        assert DataProcessedEvent.__name__ in capability.input_types
        assert "AnomalyDetectedEvent" in capability.output_types

    async def test_agent_start_and_subscription(self, agent, event_bus):
        """Test that the agent starts correctly and subscribes to events."""
        # Mock the event bus subscribe method
        event_bus.subscribe = AsyncMock()
        
        await agent.start()
        
        assert agent.status == "running"
        # Verify that subscribe was called with correct parameters
        event_bus.subscribe.assert_called_once_with(
            DataProcessedEvent.__name__,
            agent.process
        )

    async def test_process_data_processed_event(self, agent, sample_data_processed_event):
        """Test that the agent can process DataProcessedEvent correctly."""
        # Mock the logger to capture log messages
        with patch.object(agent.logger, 'info') as mock_info, \
             patch.object(agent.logger, 'debug') as mock_debug:
            
            await agent.process(sample_data_processed_event)
            
            # Verify that the process method was called and logged appropriately
            mock_info.assert_called()
            mock_debug.assert_called()
            
            # Check that the info log contains expected sensor information
            info_calls = [call[0][0] for call in mock_info.call_args_list]
            assert any("Processing sensor reading for sensor_temp_001" in call for call in info_calls)

    async def test_process_handles_invalid_data(self, agent):
        """Test that the agent handles invalid data gracefully."""
        # Create an event with invalid processed_data
        invalid_event = DataProcessedEvent(
            processed_data={"invalid": "data"},  # Missing required SensorReading fields
            original_event_id=uuid.uuid4(),
            source_sensor_id="invalid_sensor"
        )
        
        # Mock the logger to capture error messages
        with patch.object(agent.logger, 'error') as mock_error:
            await agent.process(invalid_event)
            
            # Verify that an error was logged
            mock_error.assert_called_once()
            error_call = mock_error.call_args[0][0]
            assert "Error processing DataProcessedEvent" in error_call

    async def test_full_agent_lifecycle(self, agent, event_bus, sample_data_processed_event):
        """Test the complete agent lifecycle from start to processing events."""
        # Mock the event bus
        event_bus.subscribe = AsyncMock()
        
        # Start the agent
        await agent.start()
        assert agent.status == "running"
        
        # Process an event
        with patch.object(agent.logger, 'info') as mock_info:
            await agent.process(sample_data_processed_event)
            mock_info.assert_called()
        
        # Stop the agent
        await agent.stop()
        assert agent.status == "stopped"

    async def test_historical_data_store_initialization(self, agent):
        """Test that the historical data store is properly initialized with mock data."""
        assert "sensor_temp_001" in agent.historical_data_store
        assert "sensor_vibr_001" in agent.historical_data_store
        assert "sensor_press_001" in agent.historical_data_store
        
        # Check structure of historical data entries
        temp_data = agent.historical_data_store["sensor_temp_001"]
        assert "mean" in temp_data
        assert "std" in temp_data
        assert isinstance(temp_data["mean"], (int, float))
        assert isinstance(temp_data["std"], (int, float))
