import unittest
from unittest.mock import AsyncMock, Mock, patch
import asyncio
from datetime import datetime, timedelta
import uuid
import logging
from typing import Optional, List  # Added Optional, List

from apps.agents.core.validation_agent import ValidationAgent
from core.events.event_models import AnomalyDetectedEvent, AnomalyValidatedEvent
from core.events.event_bus import EventBus

# AnomalyAlert F401 was previously noted. While _get_default_anomaly_details returns a dict,
# it's structured like an AnomalyAlert. If tests ever directly instantiate AnomalyAlert,
# this import would be needed. For now, assuming dicts are sufficient and Flake8 is correct.
# from data.schemas import AnomalyAlert # Removed F401
from data.schemas import (
    SensorReading,
)  # SensorReading is used for historical data
from apps.rules.validation_rules import RuleEngine

# Mock EventBus for integration testing
class MockEventBus(EventBus):
    def __init__(self):
        super().__init__()
        self.published_events = []
    
    async def publish(self, event):
        """Override to capture published events for testing."""
        self.published_events.append(event)
        # Call the parent's publish method to ensure handlers are invoked
        return await super().publish(event)

# Disable logging for tests to keep output clean
# logging.disable(logging.CRITICAL)  # Temporarily enable for debugging


class TestValidationAgentIntegration(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.event_bus = MockEventBus()  # Use the custom MockEventBus
        self.mock_crud_sensor_reading = Mock()  # Use regular Mock instead of AsyncMock
        self.rule_engine = RuleEngine()  # Real RuleEngine

        # Default return values for mocks
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id = AsyncMock(return_value=[])

        # Create a mock session factory that returns a mock session
        def mock_session_factory():
            return AsyncMock()  # Return a mock session

        self.agent = ValidationAgent(
            agent_id="integration_validator",
            event_bus=self.event_bus,
            crud_sensor_reading=self.mock_crud_sensor_reading,
            rule_engine=self.rule_engine,
            db_session_factory=mock_session_factory,  # Provide the mock session factory
            specific_settings={
                "credible_threshold": 0.7,
                "false_positive_threshold": 0.4,
                "historical_check_limit": 5,
            },
        )
        self.default_ts = datetime.utcnow()
        self.received_events: List[AnomalyValidatedEvent] = (
            []
        )  # To store events received by test handlers, added type hint

    async def asyncSetUp(self):
        # Start the agent, which includes subscribing to AnomalyDetectedEvent
        await self.agent.start()

    async def asyncTearDown(self):
        if self.agent and self.agent.status == "running":
            await self.agent.stop()
        # Clear subscriptions from the mock bus if necessary (MockEventBus clears on init)
        self.event_bus.subscriptions = {}
        self.received_events = []

    def _create_anomaly_detected_event(
        self,
        anomaly_details: dict,
        triggering_data: dict,
        correlation_id: Optional[str] = None,  # Optional is imported
    ) -> AnomalyDetectedEvent:
        return AnomalyDetectedEvent(
            event_id=str(uuid.uuid4()),  # uuid is imported
            correlation_id=correlation_id or str(uuid.uuid4()),  # uuid is imported
            anomaly_details=anomaly_details,
            triggering_data=triggering_data,
            source_system="IntegrationTestSource",
            created_at=self.default_ts,
        )

    def _get_default_anomaly_details(
        self, confidence=0.8, sensor_id="sensor_INT", anomaly_type="spike", severity=4
    ) -> dict:
        return {
            "sensor_id": sensor_id,
            "anomaly_type": anomaly_type,
            "severity": severity,
            "confidence": confidence,
            "description": "Integration test anomaly",
            "timestamp": self.default_ts.isoformat(),
        }

    def _get_default_triggering_data(
        self,
        sensor_id="sensor_INT",
        value=100.0,
        quality=0.9,
        sensor_type="temperature",  # Use lowercase enum value
    ) -> dict:
        return {
            "sensor_id": sensor_id,
            "timestamp": self.default_ts.isoformat(),
            "value": value,
            "sensor_type": sensor_type,
            "unit": "C",
            "quality": quality,
        }

    async def _validated_event_handler(self, event: AnomalyValidatedEvent):
        """Callback to store received AnomalyValidatedEvent."""
        self.received_events.append(event)

    async def test_scenario_credible_anomaly(self):
        # Setup handler for AnomalyValidatedEvent
        await self.event_bus.subscribe(
            AnomalyValidatedEvent.__name__, self._validated_event_handler
        )

        # Create an event expected to be credible
        # Initial high confidence, good quality data, no strong negative rules from RuleEngine
        anomaly_details = self._get_default_anomaly_details(confidence=0.85)
        triggering_data = self._get_default_triggering_data(quality=0.95)
        detected_event = self._create_anomaly_detected_event(
            anomaly_details, triggering_data, correlation_id="credible_corr_01"
        )

        # Mock historical data to be benign - we need to mock both the async call and the ORM conversion
        mock_orm_readings = [
            Mock(
                sensor_id=anomaly_details["sensor_id"],
                value=98.0,
                timestamp=self.default_ts - timedelta(hours=1),
                sensor_type="temperature",
                unit="C",
                quality=1.0,
            ),
            Mock(
                sensor_id=anomaly_details["sensor_id"],
                value=99.0,
                timestamp=self.default_ts - timedelta(hours=2),
                sensor_type="temperature",
                unit="C",
                quality=1.0,
            ),
        ]
        
        # Set up the async mock properly - AsyncMock needs return_value for direct returns
        async def mock_get_readings(*args, **kwargs):
            return mock_orm_readings
        
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.side_effect = mock_get_readings
        
        # Mock the ORM to Pydantic conversion
        def mock_orm_to_pydantic(orm_obj):
            return SensorReading(
                sensor_id=orm_obj.sensor_id,
                value=orm_obj.value,
                timestamp=orm_obj.timestamp,
                sensor_type=orm_obj.sensor_type,
                unit=orm_obj.unit,
                quality=orm_obj.quality,
            )
        
        self.mock_crud_sensor_reading.orm_to_pydantic.side_effect = mock_orm_to_pydantic

        await self.event_bus.publish(detected_event)

        # Wait for the event to be processed and handled
        await asyncio.sleep(0.1)  # Give a short time for async processing

        self.assertEqual(len(self.received_events), 1)
        validated_event = self.received_events[0]

        self.assertIsInstance(validated_event, AnomalyValidatedEvent)
        self.assertEqual(validated_event.validation_status, "credible_anomaly")
        # Expected: 0.85 (initial) + 0 (no rules by default) + 0 (no strong historical) = 0.85
        self.assertAlmostEqual(validated_event.final_confidence, 0.85, places=2)
        self.assertEqual(validated_event.agent_id, self.agent.agent_id)
        self.assertEqual(validated_event.correlation_id, "credible_corr_01")
        self.assertEqual(
            validated_event.original_anomaly_alert_payload, anomaly_details
        )
        self.assertEqual(validated_event.triggering_reading_payload, triggering_data)

    async def test_scenario_false_positive_due_to_rules(self):
        await self.event_bus.subscribe(
            AnomalyValidatedEvent.__name__, self._validated_event_handler
        )

        # Event designed to trigger negative rules in RuleEngine
        # Low initial confidence, poor data quality
        anomaly_details = self._get_default_anomaly_details(
            confidence=0.25
        )  # Rule 1: -0.1 (confidence < 0.3)
        triggering_data = self._get_default_triggering_data(quality=0.4)  # Rule 2: -0.2 (quality < 0.5)
        # Total from rules: -0.3. Initial: 0.25. Final: -0.05 -> clamped to 0.0

        detected_event = self._create_anomaly_detected_event(
            anomaly_details, triggering_data, correlation_id="fp_corr_01"
        )

        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = (
            []
        )  # No historical impact

        await self.event_bus.publish(detected_event)
        await asyncio.sleep(0.1)

        self.assertEqual(len(self.received_events), 1)
        validated_event = self.received_events[0]

        self.assertEqual(validated_event.validation_status, "false_positive_suspected")
        self.assertAlmostEqual(
            validated_event.final_confidence, 0.0, places=2
        )  # Clamped
        self.assertEqual(validated_event.agent_id, self.agent.agent_id)
        self.assertEqual(validated_event.correlation_id, "fp_corr_01")
        self.assertIn(
            "Initial alert confidence (0.25) is below threshold (0.3).",
            validated_event.validation_reasons,
        )
        self.assertIn(
            "Triggering sensor reading quality (0.40) is low (below 0.5).",
            validated_event.validation_reasons,
        )

    async def test_agent_integration_historical_context(self):
        await self.event_bus.subscribe(
            AnomalyValidatedEvent.__name__, self._validated_event_handler
        )

        sensor_id = "temp_hist_trigger"
        current_value = 25.0

        # Configure agent settings for this specific test
        self.agent.settings.update({
            "historical_check_limit": 5, # Ensure this is consistent or explicitly set
            "recent_stability_window": 3,
            "recent_stability_factor": 0.1, 
            "recent_stability_min_std_dev": 0.05,
            "recent_stability_jump_adjustment": -0.15, 
            "recent_stability_minor_deviation_adjustment": -0.05,
            "volatile_baseline_adjustment": 0.05,
            "recurring_anomaly_diff_factor": 0.5, 
            "recurring_anomaly_threshold_pct": 0.5,
            "recurring_anomaly_penalty": -0.1 
        })
        # Historical data designed to trigger "Recent Value Stability" (-0.1)
        # Agent settings: recent_stability_window = 3 (from ValidationAgent unit test, assuming similar settings here)
        # Let's assume specific_settings for this test agent are:
        # "recent_stability_window": 3, "recent_stability_factor": 0.05
        # Mean of (20, 21, 19.5) = 20.16. Current value 20.5. Diff 0.33. Factor*Mean = 1.008. Triggered.
        historical_data = [
            SensorReading(
                sensor_id=sensor_id, # Ensure sensor_id is defined in the test, e.g., "temp_hist_trigger"
                value=10.0,
                timestamp=self.default_ts - timedelta(hours=1),
                sensor_type="temperature",
                unit="C",
                quality=1.0,
            ),
            SensorReading(
                sensor_id=sensor_id,
                value=10.1,
                timestamp=self.default_ts - timedelta(hours=2),
                sensor_type="temperature",
                unit="C",
                quality=1.0,
            ),
            SensorReading(
                sensor_id=sensor_id,
                value=9.9,
                timestamp=self.default_ts - timedelta(hours=3),
                sensor_type="temperature",
                unit="C",
                quality=1.0,
            ),
            # Add a couple more older readings to satisfy historical_check_limit if it's > 3
            # These older readings should not make the recent window unstable
            SensorReading(
                sensor_id=sensor_id,
                value=10.2, # Still close to the recent average
                timestamp=self.default_ts - timedelta(hours=4),
                sensor_type="temperature",
                unit="C",
                quality=1.0,
            ),
            SensorReading(
                sensor_id=sensor_id,
                value=9.8, # Still close to the recent average
                timestamp=self.default_ts - timedelta(hours=5),
                sensor_type="temperature",
                unit="C",
                quality=1.0,
            ),
        ]
        
        # Create mock ORM objects that will be converted to Pydantic objects
        mock_orm_readings = []
        for reading in historical_data:
            mock_orm_readings.append(Mock(
                sensor_id=reading.sensor_id,
                value=reading.value,
                timestamp=reading.timestamp,
                sensor_type=reading.sensor_type,
                unit=reading.unit,
                quality=reading.quality,
            ))
        
        # Set up the async mock properly
        async def mock_get_readings(*args, **kwargs):
            return mock_orm_readings
        
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.side_effect = mock_get_readings
        
        # Mock the ORM to Pydantic conversion
        def mock_orm_to_pydantic(orm_obj):
            return SensorReading(
                sensor_id=orm_obj.sensor_id,
                value=orm_obj.value,
                timestamp=orm_obj.timestamp,
                sensor_type=orm_obj.sensor_type,
                unit=orm_obj.unit,
                quality=orm_obj.quality,
            )
        
        self.mock_crud_sensor_reading.orm_to_pydantic.side_effect = mock_orm_to_pydantic

        # Initial confidence is borderline, e.g., 0.45. Historical context pushes it down.
        anomaly_details = self._get_default_anomaly_details(
            sensor_id=sensor_id, confidence=0.6, anomaly_type="spike"
        )
        triggering_data = self._get_default_triggering_data(
            sensor_id=sensor_id, value=current_value, quality=0.95
        )
        # Expected: 0.45 (initial) - 0.1 (historical stability) = 0.35. Status: false_positive_suspected

        detected_event = self._create_anomaly_detected_event(
            anomaly_details, triggering_data, correlation_id="hist_fp_corr_01"
        )

        # Mock RuleEngine for this test to isolate historical validation
        with patch.object(self.rule_engine, 'evaluate_rules', new_callable=AsyncMock) as mock_evaluate_rules:
            mock_evaluate_rules.return_value = (0.0, [])

            # Publish the event
            await self.event_bus.publish(detected_event)
            await asyncio.sleep(0.1) # Wait for processing

            # Assertions
            self.assertEqual(len(self.received_events), 1) # Keep this assertion
            validated_event = self.received_events[0] # Keep this

            # Updated assertions:
            self.assertEqual(validated_event.validation_status, "further_investigation_needed")
            self.assertAlmostEqual(validated_event.final_confidence, 0.45, places=2)
            
            # Check for the specific historical reason string
            expected_reason = "Anomaly (value: 25.0) deviates significantly from a recently stable baseline (avg: 10.00, std_dev: 0.08)."
            self.assertIn(expected_reason, validated_event.validation_reasons)
            
            # Ensure no other unexpected reasons are present if we want to be strict,
            # or just check that the list is not empty and contains the expected one.
            # For now, let's ensure it's the primary reason if no rule-based reasons are expected.
            # Based on agent logic, if rule_reasons are empty and this hist_reason is present, 
            # validation_reasons should contain just this.
            self.assertEqual(len(validated_event.validation_reasons), 1, 
                             f"Expected only one validation reason, but got: {validated_event.validation_reasons}")

            self.assertEqual(validated_event.agent_id, self.agent.agent_id) # Keep this

    async def test_agent_does_not_process_if_not_started(self):
        # Create a new agent instance that is NOT started
        new_agent = ValidationAgent(
            agent_id="not_started_validator",
            event_bus=AsyncMock(),  # Use a dedicated mock bus for new_agent
            crud_sensor_reading=self.mock_crud_sensor_reading,
            rule_engine=self.rule_engine,
        )
        # DO NOT call await new_agent.start()

        await self.event_bus.subscribe(
            AnomalyValidatedEvent.__name__, self._validated_event_handler
        )

        anomaly_details = self._get_default_anomaly_details()
        triggering_data = self._get_default_triggering_data()
        detected_event = self._create_anomaly_detected_event(
            anomaly_details, triggering_data
        )

        await self.event_bus.publish(detected_event)
        await asyncio.sleep(0.1)  # Give time for any accidental processing

        # self.received_events should be empty because the new_agent was not started and thus
        # should not have subscribed to AnomalyDetectedEvent.
        # The already started self.agent WILL process this event.
        # This test needs careful thought about shared event bus state.

        # Let's refine: the goal is to see if `new_agent` published.
        # We can check if `new_agent.event_bus.publish` was called by `new_agent`.
        # This requires `new_agent` to have its own mock bus or spy on the shared bus.
        # For simplicity with shared bus: check if an event from "not_started_validator" appears.

        processed_by_started_agent = False
        processed_by_not_started_agent = False

        for (
            event_obj
        ) in (
            self.received_events
        ):  # Renamed event to event_obj to avoid conflict with event module
            if event_obj.agent_id == self.agent.agent_id:  # The agent started in setUp
                processed_by_started_agent = True
            if event_obj.agent_id == new_agent.agent_id:
                processed_by_not_started_agent = True

        self.assertTrue(
            processed_by_started_agent,
            "The started agent should have processed the event.",
        )
        self.assertFalse(
            processed_by_not_started_agent,
            "The non-started agent should NOT have processed the event.",
        )


if __name__ == "__main__":
    unittest.main()
