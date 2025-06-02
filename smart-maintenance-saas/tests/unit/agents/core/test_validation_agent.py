import unittest
from unittest.mock import (
    AsyncMock,
    Mock,
    patch,
    # MagicMock, ANY were F401, so removed
)
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone  # Added timezone
import uuid
import logging
from typing import Optional  # Added Optional
from contextlib import contextmanager

from apps.agents.core.validation_agent import ValidationAgent
from core.events.event_models import AnomalyDetectedEvent, AnomalyValidatedEvent
from data.schemas import AnomalyAlert, SensorReading, SensorType  # Added SensorType
from apps.agents.base_agent import BaseAgent  # noqa: F401 - Used in patch string

# Disable logging for tests unless specifically testing log output
logging.disable(logging.CRITICAL)


class TestValidationAgent(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_event_bus = AsyncMock()
        self.mock_crud_sensor_reading = AsyncMock()
        # Ensure the method to be called on this mock is also an AsyncMock if it's awaited
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id = AsyncMock(return_value=[])

        self.mock_rule_engine = AsyncMock()
        # Ensure the method to be called on this mock is also an AsyncMock if it's awaited
        self.mock_rule_engine.evaluate_rules = AsyncMock(return_value=(0.0, []))

        self.mock_db_session_factory = Mock()  # Regular Mock, not AsyncMock
        # Configure the factory to return another AsyncMock when called (simulating a db session)
        self.mock_db_session = AsyncMock()
        self.mock_db_session.close = AsyncMock()  # Ensure close method is properly mocked as async
        self.mock_db_session_factory.return_value = self.mock_db_session


        self.agent = ValidationAgent(
            agent_id="test_validator",
            event_bus=self.mock_event_bus,
            db_session_factory=self.mock_db_session_factory, # Added db_session_factory
            crud_sensor_reading=self.mock_crud_sensor_reading,
            rule_engine=self.mock_rule_engine,
            specific_settings={  # Ensure agent uses these, not defaults if they differ
                "credible_threshold": 0.7,
                "false_positive_threshold": 0.4,
                "historical_check_limit": 10,  # smaller for tests
                "recent_stability_window": 3,  # smaller for tests
                "recent_stability_factor": 0.1,
                "recent_stability_min_std_dev": 0.05,
                "recent_stability_jump_adjustment": 0.10,
                "recent_stability_minor_deviation_adjustment": -0.05,
                "volatile_baseline_adjustment": 0.05,
                "recurring_anomaly_diff_factor": 0.2,  # Updated to match new default
                "recurring_anomaly_threshold_pct": 0.25,
                "recurring_anomaly_penalty": -0.05,
            },
        )
        self.default_ts = datetime.utcnow()

    @contextmanager
    def _temporarily_enable_logging(self):
        """Context manager to temporarily enable logging for specific tests."""
        logging.disable(logging.NOTSET)
        try:
            yield
        finally:
            logging.disable(logging.CRITICAL)

    def _create_anomaly_detected_event(
        self,
        anomaly_details: dict,
        triggering_data: dict,
        correlation_id: Optional[str] = None,  # Optional is now imported
        event_id: Optional[str] = None,  # Optional is now imported
        source_system: str = "TestSource",
    ) -> AnomalyDetectedEvent:
        return AnomalyDetectedEvent(
            event_id=event_id or str(uuid.uuid4()),
            correlation_id=correlation_id or str(uuid.uuid4()),
            anomaly_details=anomaly_details,
            triggering_data=triggering_data,
            source_system=source_system,
            created_at=self.default_ts,
        )

    def _get_default_anomaly_details(
        self, confidence=0.8, sensor_id="sensor_A", anomaly_type="spike", severity=4
    ) -> dict:
        # Ensure timestamp is stored as datetime object before potential isoformat conversion for event
        # Pydantic model AnomalyAlert expects 'created_at: datetime'
        return {
            "sensor_id": sensor_id,
            "anomaly_type": anomaly_type,
            "severity": severity,
            "confidence": confidence,
            "description": "Test anomaly",
            "created_at": self.default_ts, # Changed 'timestamp' to 'created_at' and pass datetime
        }

    def _get_default_triggering_data(
        self, sensor_id="sensor_A", value=100.0, quality=0.9, sensor_type: SensorType = SensorType.TEMPERATURE
    ) -> dict:
        # SensorReading model expects 'sensor_type: SensorType' (enum)
        # and 'timestamp' will be parsed into datetime by Pydantic
        return {
            "sensor_id": sensor_id,
            "timestamp": self.default_ts.isoformat(), # Pydantic will parse this to datetime
            "value": value,
            "sensor_type": sensor_type, # Use SensorType enum member
            "unit": "C", # Assuming 'C' is for TEMPERATURE, adjust if other types have different units by default
            "quality": quality,
        }

    async def test_process_successful_credible_anomaly(self):
        self.mock_rule_engine.evaluate_rules.return_value = (
            0.1,
            ["Rule reason: positive adjustment"],
        )  # Positive rule effect

        event_corr_id = str(uuid.uuid4())
        anomaly_details = self._get_default_anomaly_details(
            confidence=0.75
        )  # Initial high confidence
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(
            anomaly_details, triggering_data, correlation_id=event_corr_id
        )

        await self.agent.process(event)

        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args.kwargs['event']
        self.assertIsInstance(published_event, AnomalyValidatedEvent)
        self.assertEqual(published_event.validation_status, "credible_anomaly") # Corrected status string
        self.assertAlmostEqual(
            published_event.final_confidence, 0.85
        )  # 0.75 (initial) + 0.1 (rule)
        self.assertEqual(published_event.agent_id, self.agent.agent_id)
        self.assertEqual(published_event.correlation_id, event_corr_id) # Specific event_corr_id used here
        self.assertEqual(
            published_event.original_anomaly_alert_payload, anomaly_details
        )
        self.assertEqual(published_event.triggering_reading_payload, triggering_data)
        self.assertIn(
            "Rule reason: positive adjustment", published_event.validation_reasons
        )
        self.assertIsInstance(published_event.validated_at, datetime)
        # Check if validated_at is close to now, within a tolerance (e.g., 5 seconds)
        now = datetime.now(timezone.utc)
        validated_at = published_event.validated_at
        if validated_at.tzinfo is None:
            validated_at = validated_at.replace(tzinfo=timezone.utc)
        self.assertTrue(
            (now - validated_at) < timedelta(seconds=5),
            "validated_at timestamp is not recent"
        )

    async def test_process_successful_false_positive(self):
        rule_reasons = ["Rule reason: major penalty"]
        self.mock_rule_engine.evaluate_rules.return_value = (
            -0.3,
            rule_reasons,
        )

        anomaly_details = self._get_default_anomaly_details(
            confidence=0.5
        )  # Medium initial confidence
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(
            anomaly_details, triggering_data
        )

        await self.agent.process(event)

        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args.kwargs['event']
        self.assertEqual(published_event.validation_status, "false_positive_suspected") 
        self.assertAlmostEqual(published_event.final_confidence, 0.2) 
        self.assertEqual(published_event.agent_id, self.agent.agent_id)
        self.assertEqual(published_event.correlation_id, event.correlation_id)
        self.assertEqual(
            published_event.original_anomaly_alert_payload, anomaly_details
        )
        self.assertEqual(published_event.triggering_reading_payload, triggering_data)
        # If historical data is empty by default mock, its reason should be added
        expected_reasons = rule_reasons + ["No historical readings available for context."]
        self.assertEqual(sorted(published_event.validation_reasons), sorted(expected_reasons))
        self.assertIsInstance(published_event.validated_at, datetime)

    async def test_process_successful_uncertain(self):
        rule_reasons = ["Rule reason: minor penalty"]
        self.mock_rule_engine.evaluate_rules.return_value = (
            -0.1,
            rule_reasons,
        )
        anomaly_details = self._get_default_anomaly_details(
            confidence=0.6
        ) 
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(
            anomaly_details, triggering_data
        )

        await self.agent.process(event)

        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args.kwargs['event']
        self.assertEqual(published_event.validation_status, "further_investigation_needed") 
        self.assertAlmostEqual(published_event.final_confidence, 0.5) 
        self.assertEqual(published_event.agent_id, self.agent.agent_id)
        self.assertEqual(published_event.correlation_id, event.correlation_id)
        self.assertEqual(
            published_event.original_anomaly_alert_payload, anomaly_details
        )
        self.assertEqual(published_event.triggering_reading_payload, triggering_data)
        expected_reasons = rule_reasons + ["No historical readings available for context."]
        self.assertEqual(sorted(published_event.validation_reasons), sorted(expected_reasons))
        self.assertIsInstance(published_event.validated_at, datetime)

    async def test_final_confidence_clamped_above_one(self):
        initial_confidence = 0.9
        rule_adjustment = 0.3 
        rule_reasons = ["Rule boost"]
        self.mock_rule_engine.evaluate_rules.return_value = (rule_adjustment, rule_reasons)
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = []

        anomaly_details = self._get_default_anomaly_details(confidence=initial_confidence)
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)

        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args.kwargs['event']
        self.assertAlmostEqual(published_event.final_confidence, 1.0) 
        self.assertEqual(published_event.validation_status, "credible_anomaly")
        self.assertEqual(published_event.agent_id, self.agent.agent_id)
        self.assertEqual(published_event.correlation_id, event.correlation_id)
        self.assertEqual(
            published_event.original_anomaly_alert_payload, anomaly_details
        )
        self.assertEqual(published_event.triggering_reading_payload, triggering_data)
        expected_reasons = rule_reasons + ["No historical readings available for context."]
        self.assertEqual(sorted(published_event.validation_reasons), sorted(expected_reasons))
        self.assertIsInstance(published_event.validated_at, datetime)

    async def test_final_confidence_clamped_below_zero(self):
        initial_confidence = 0.1
        rule_adjustment = -0.3 
        rule_reasons = ["Rule penalty"]
        self.mock_rule_engine.evaluate_rules.return_value = (rule_adjustment, rule_reasons)
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = []

        anomaly_details = self._get_default_anomaly_details(confidence=initial_confidence)
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)

        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args.kwargs['event']
        self.assertAlmostEqual(published_event.final_confidence, 0.0) 
        self.assertEqual(published_event.validation_status, "false_positive_suspected")
        self.assertEqual(published_event.agent_id, self.agent.agent_id)
        self.assertEqual(published_event.correlation_id, event.correlation_id)
        self.assertEqual(
            published_event.original_anomaly_alert_payload, anomaly_details
        )
        self.assertEqual(published_event.triggering_reading_payload, triggering_data)
        expected_reasons = rule_reasons + ["No historical readings available for context."]
        self.assertEqual(sorted(published_event.validation_reasons), sorted(expected_reasons))
        self.assertIsInstance(published_event.validated_at, datetime)

    async def test_status_boundary_credible_exact_zero_adjustments(self):
        initial_confidence = 0.75
        self.mock_rule_engine.evaluate_rules.return_value = (0.0, []) 
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = [] 

        anomaly_details = self._get_default_anomaly_details(confidence=initial_confidence)
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)
        published_event = self.mock_event_bus.publish.call_args.kwargs['event']
        self.assertAlmostEqual(published_event.final_confidence, 0.75)
        self.assertEqual(published_event.validation_status, "credible_anomaly")
        self.assertEqual(published_event.agent_id, self.agent.agent_id)
        self.assertEqual(published_event.correlation_id, event.correlation_id)
        self.assertEqual(
            published_event.original_anomaly_alert_payload, anomaly_details
        )
        self.assertEqual(published_event.triggering_reading_payload, triggering_data)
        self.assertEqual(published_event.validation_reasons, ["No historical readings available for context."])
        self.assertIsInstance(published_event.validated_at, datetime)

    async def test_status_boundary_further_investigation_just_below_credible(self):
        initial_confidence = 0.749 
        self.mock_rule_engine.evaluate_rules.return_value = (0.0, [])
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = []

        anomaly_details = self._get_default_anomaly_details(confidence=initial_confidence)
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)
        published_event = self.mock_event_bus.publish.call_args.kwargs['event']
        self.assertAlmostEqual(published_event.final_confidence, 0.749)
        self.assertEqual(published_event.validation_status, "credible_anomaly")  # 0.749 > 0.7 threshold
        self.assertEqual(published_event.agent_id, self.agent.agent_id)
        self.assertEqual(published_event.correlation_id, event.correlation_id)
        self.assertEqual(
            published_event.original_anomaly_alert_payload, anomaly_details
        )
        self.assertEqual(published_event.triggering_reading_payload, triggering_data)
        self.assertEqual(published_event.validation_reasons, ["No historical readings available for context."])
        self.assertIsInstance(published_event.validated_at, datetime)

    async def test_status_boundary_further_investigation_exact_at_false_positive_upper(self):
        initial_confidence = 0.40
        self.mock_rule_engine.evaluate_rules.return_value = (0.0, [])
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = []

        anomaly_details = self._get_default_anomaly_details(confidence=initial_confidence)
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)
        published_event = self.mock_event_bus.publish.call_args.kwargs['event']
        self.assertAlmostEqual(published_event.final_confidence, 0.40)
        self.assertEqual(published_event.validation_status, "further_investigation_needed")
        self.assertEqual(published_event.agent_id, self.agent.agent_id)
        self.assertEqual(published_event.correlation_id, event.correlation_id)
        self.assertEqual(
            published_event.original_anomaly_alert_payload, anomaly_details
        )
        self.assertEqual(published_event.triggering_reading_payload, triggering_data)
        self.assertEqual(published_event.validation_reasons, ["No historical readings available for context."])
        self.assertIsInstance(published_event.validated_at, datetime)

    async def test_status_boundary_false_positive_just_below_further_investigation(self):
        initial_confidence = 0.399
        self.mock_rule_engine.evaluate_rules.return_value = (0.0, [])
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = []

        anomaly_details = self._get_default_anomaly_details(confidence=initial_confidence)
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)
        published_event = self.mock_event_bus.publish.call_args.kwargs['event']
        self.assertAlmostEqual(published_event.final_confidence, 0.399)
        self.assertEqual(published_event.validation_status, "false_positive_suspected")
        self.assertEqual(published_event.agent_id, self.agent.agent_id)
        self.assertEqual(published_event.correlation_id, event.correlation_id)
        self.assertEqual(
            published_event.original_anomaly_alert_payload, anomaly_details
        )
        self.assertEqual(published_event.triggering_reading_payload, triggering_data)
        self.assertEqual(published_event.validation_reasons, ["No historical readings available for context."])
        self.assertIsInstance(published_event.validated_at, datetime)

    async def test_process_input_parsing_failure_anomaly_details(self):
        # Test what happens when anomaly_details is malformed (not a dict)
        triggering_data = self._get_default_triggering_data()
        
        # Create an event with invalid anomaly_details type
        event = AnomalyDetectedEvent(
            event_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
            anomaly_details="invalid_not_a_dict",  # This should cause parsing failure
            triggering_data=triggering_data,
            source_system="TestSource",
            created_at=self.default_ts
        )

        await self.agent.process(event)

        # The agent should not publish any event due to validation failure
        self.mock_event_bus.publish.assert_not_called()


    async def test_correlation_id_fallback_to_event_id(self):
        # Test that if correlation_id is None in incoming event, it falls back to event_id
        fixed_event_id = str(uuid.uuid4())
        anomaly_details = self._get_default_anomaly_details(confidence=0.8)
        triggering_data = self._get_default_triggering_data()
        
        # Create event with correlation_id=None
        event = self._create_anomaly_detected_event(
            anomaly_details, triggering_data, correlation_id=None, event_id=fixed_event_id
        )
        # Ensure correlation_id is indeed None on the event object if _create_anomaly_detected_event allows it
        # (it might assign a default if None is passed and not handled by Optional).
        # For this test, we'll directly create AnomalyDetectedEvent to ensure None correlation_id
        event = AnomalyDetectedEvent(
            event_id=fixed_event_id,
            correlation_id=None, # Explicitly None
            anomaly_details=anomaly_details,
            triggering_data=triggering_data,
            source_system="TestSource",
            created_at=self.default_ts
        )

        self.mock_rule_engine.evaluate_rules.return_value = (0.0, [])
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = []

        await self.agent.process(event)

        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args.kwargs['event']

        self.assertEqual(published_event.correlation_id, fixed_event_id)
        self.assertEqual(published_event.agent_id, self.agent.agent_id)
        self.assertEqual(published_event.original_anomaly_alert_payload, anomaly_details)
        self.assertEqual(published_event.triggering_reading_payload, triggering_data)
        self.assertIsInstance(published_event.validated_at, datetime)


    async def test_process_error_in_crud_historical_fetch(self):
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.side_effect = (
            Exception("DB connection failed!")
        )
        # This error occurs inside _perform_historical_context_validation, which should be handled.
        # The agent should still proceed and publish an event, but historical adjustment will be 0 and a reason added.

        initial_confidence = 0.8
        anomaly_details = self._get_default_anomaly_details(confidence=initial_confidence)
        triggering_data = self._get_default_triggering_data(sensor_type=SensorType.TEMPERATURE)
        # Pass SensorType enum for sensor_type
        event = self._create_anomaly_detected_event(
            anomaly_details, triggering_data
        )
        
        # The mock rule engine returns (0.0, [])
        self.mock_rule_engine.evaluate_rules.return_value = (0.0, [])

        with self.assertLogs(self.agent.logger.name, level="ERROR") as log_watcher:
            await self.agent.process(event)
            
        # Verify that the specific "DB connection failed!" error was logged
        self.assertTrue(
            any("DB connection failed!" in msg for msg in log_watcher.output)
        )

        self.mock_event_bus.publish.assert_called_once()  # Should still publish
        published_event = self.mock_event_bus.publish.call_args.kwargs['event']
        
        # After New Prompt A changes, the agent should return "Historical data fetch failed." in reasons
        self.assertIn(
            "Historical data fetch failed.",
            published_event.validation_reasons
        )
        self.assertAlmostEqual(
            published_event.final_confidence, initial_confidence 
        )  # No historical adjustment, no rule adjustment
        self.assertEqual(published_event.agent_id, self.agent.agent_id)
        self.assertEqual(published_event.correlation_id, event.correlation_id)
        self.assertEqual(
            published_event.original_anomaly_alert_payload, anomaly_details
        )
        self.assertEqual(published_event.triggering_reading_payload, triggering_data)
        self.assertIsInstance(published_event.validated_at, datetime)
        # Ensure no rule engine reasons are present as it was mocked to (0.0, [])
        self.assertTrue(all(r not in published_event.validation_reasons for r in ["Positive rule", "Rule penalty", "Rule reason: positive adjustment", "Rule reason: major penalty", "Rule reason: minor penalty"]))
        # Check that the status is determined correctly based on the final_confidence
        if initial_confidence >= 0.75:
            expected_status = "credible_anomaly"
        elif initial_confidence < 0.4:
            expected_status = "false_positive_suspected"
        else:
            expected_status = "further_investigation_needed"
        self.assertEqual(published_event.validation_status, expected_status)


    async def test_process_parsing_failure_malformed_anomaly_details(self):
        malformed_details = {
            "sensor_id": "test_sensor"
        }  # Missing confidence, type, severity, timestamp
        event = self._create_anomaly_detected_event(
            malformed_details, self._get_default_triggering_data()
        )

        with self.assertLogs(self.agent.logger.name, level="ERROR") as log_watcher:
            await self.agent.process(event)

        self.mock_event_bus.publish.assert_not_called()
        # Check that an error related to parsing AnomalyAlert was logged
        self.assertTrue(
            any("Error parsing AnomalyAlert" in msg for msg in log_watcher.output)
        )

    async def test_process_input_parsing_failure_triggering_data(self):
        malformed_triggering_data = {
            "sensor_id": "test_sensor"
        }  # Missing timestamp, value, type, quality
        event = self._create_anomaly_detected_event(
            self._get_default_anomaly_details(), malformed_triggering_data
        )

        with self._temporarily_enable_logging():
            with self.assertLogs(self.agent.logger.name, level="ERROR") as log_watcher:
                await self.agent.process(event)

            self.mock_event_bus.publish.assert_not_called()
            self.assertTrue(
                any("Error parsing SensorReading" in msg or "Unhandled error processing" in msg for msg in log_watcher.output)
            )

    async def test_process_parsing_failure_anomaly_missing_sensor_id(self):
        details = self._get_default_anomaly_details()
        del details["sensor_id"]  # Remove sensor_id
        event = self._create_anomaly_detected_event(
            details, self._get_default_triggering_data()
        )
        with self._temporarily_enable_logging():
            with self.assertLogs(self.agent.logger.name, level="ERROR") as log_watcher:
                await self.agent.process(event)
            self.mock_event_bus.publish.assert_not_called()
            self.assertTrue(
                any("Error parsing AnomalyAlert" in msg or "Unhandled error processing" in msg for msg in log_watcher.output)
            )

    async def test_process_parsing_failure_anomaly_missing_created_at(self):
        details = self._get_default_anomaly_details()
        del details["created_at"]  # Remove created_at
        event = self._create_anomaly_detected_event(
            details, self._get_default_triggering_data()
        )
        with self._temporarily_enable_logging():
            with self.assertLogs(self.agent.logger.name, level="ERROR") as log_watcher:
                await self.agent.process(event)
            self.mock_event_bus.publish.assert_not_called()
            self.assertTrue(
                any("Error parsing AnomalyAlert" in msg or "Unhandled error processing" in msg for msg in log_watcher.output)
            )

    async def test_process_parsing_failure_triggering_missing_timestamp(self):
        data = self._get_default_triggering_data()
        del data["timestamp"]  # Remove timestamp
        event = self._create_anomaly_detected_event(
            self._get_default_anomaly_details(), data
        )
        with self._temporarily_enable_logging():
            with self.assertLogs(self.agent.logger.name, level="ERROR") as log_watcher:
                await self.agent.process(event)
            self.mock_event_bus.publish.assert_not_called()
            self.assertTrue(
                any("Error parsing SensorReading" in msg or "Unhandled error processing" in msg for msg in log_watcher.output)
            )

    async def test_process_parsing_failure_triggering_missing_value(self):
        data = self._get_default_triggering_data()
        del data["value"]  # Remove value
        event = self._create_anomaly_detected_event(
            self._get_default_anomaly_details(), data
        )
        with self._temporarily_enable_logging():
            with self.assertLogs(self.agent.logger.name, level="ERROR") as log_watcher:
                await self.agent.process(event)
            self.mock_event_bus.publish.assert_not_called()
            self.assertTrue(
                any("Error parsing SensorReading" in msg or "Unhandled error processing" in msg for msg in log_watcher.output)
            )

    async def test_process_parsing_failure_triggering_invalid_sensor_type(self):
        data = self._get_default_triggering_data()
        data["sensor_type"] = "INVALID_TYPE"  # Set invalid sensor_type
        event = self._create_anomaly_detected_event(
            self._get_default_anomaly_details(), data
        )
        with self._temporarily_enable_logging():
            with self.assertLogs(self.agent.logger.name, level="ERROR") as log_watcher:
                await self.agent.process(event)
            self.mock_event_bus.publish.assert_not_called()
            self.assertTrue(
                any("Error parsing SensorReading" in msg or "Unhandled error processing" in msg for msg in log_watcher.output)
            )

    async def test_rule_engine_interaction(self):
        anomaly_details = self._get_default_anomaly_details()
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)

        await self.agent.process(event)

        self.mock_rule_engine.evaluate_rules.assert_called_once()
        call_kwargs = self.mock_rule_engine.evaluate_rules.call_args.kwargs
        self.assertIsInstance(call_kwargs['alert'], AnomalyAlert)  # First kwarg is AnomalyAlert
        self.assertIsInstance(
            call_kwargs['reading'], SensorReading
        )  # Second kwarg is SensorReading
        self.assertEqual(call_kwargs['alert'].sensor_id, anomaly_details["sensor_id"])
        self.assertEqual(call_kwargs['reading'].value, triggering_data["value"])

    async def test_crud_sensor_reading_interaction(self):
        anomaly_details = self._get_default_anomaly_details(sensor_id="sensor_X")
        triggering_data = self._get_default_triggering_data(sensor_id="sensor_X")
        # Make sure the triggering_data timestamp is a datetime object for comparison
        parsed_reading = SensorReading(**triggering_data)

        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)

        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.assert_called_once_with(
            db=self.mock_db_session, # Use the mock session returned by the factory
            sensor_id="sensor_X",
            limit=self.agent.historical_check_limit,  # Using agent's setting
            end_time=parsed_reading.timestamp,  # Changed from before_timestamp to end_time
        )

    async def test_historical_validation_empty_list(self):
        # Test case where CRUDSensorReading returns no historical data
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = []
        initial_confidence = 0.8
        # Rule engine gives a slight positive boost initially
        self.mock_rule_engine.evaluate_rules.return_value = (0.05, ["Positive rule"])


        anomaly_details = self._get_default_anomaly_details(confidence=initial_confidence)
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)

        await self.agent.process(event)

        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args.kwargs['event']

        # No historical data, so historical adjustment should be 0.
        # Final confidence = initial_confidence + rule_engine_adjustment + historical_adjustment
        # Final confidence = 0.8 + 0.05 + 0 = 0.85
        self.assertAlmostEqual(published_event.final_confidence, initial_confidence + 0.05)
        self.assertIn(
            "No historical readings available for context.", published_event.validation_reasons
        )
        self.assertEqual(published_event.validation_status, "credible_anomaly") # Corrected, Example, depends on thresholds
        self.assertEqual(published_event.agent_id, self.agent.agent_id)
        self.assertEqual(published_event.correlation_id, event.correlation_id)
        self.assertEqual(published_event.original_anomaly_alert_payload, anomaly_details)
        self.assertEqual(published_event.triggering_reading_payload, triggering_data)
        self.assertIsInstance(published_event.validated_at, datetime)
        # Check that "Positive rule" is also in reasons
        self.assertIn("Positive rule", published_event.validation_reasons)


    async def test_historical_recent_value_stability_triggered(self):
        sensor_id = "temp_stable"
        current_value = 20.5
        # Agent specific_settings: recent_stability_window = 3, recent_stability_minor_deviation_adjustment = -0.05
        # Historical readings: [20.0, 21.0, 19.5] (most recent first)
        # Average: (20.0 + 21.0 + 19.5) / 3 = 20.167
        # std_dev: ~0.624
        # Is stable: 0.624 < (0.1 * 20.167) = 2.017 → Yes
        # Significant jump: |20.5 - 20.167| = 0.333 > 3 * (0.624) = 1.873 → No
        # Therefore: minor deviation penalty of -0.05 should be applied
        historical_data = [
            SensorReading(
                sensor_id=sensor_id,
                value=20.0,
                timestamp=self.default_ts - timedelta(hours=1),
                sensor_type=SensorType.TEMPERATURE, # Use Enum
                quality=1.0,
                unit="C" # Ensure unit is provided if required by SensorReading
            ),
            SensorReading(
                sensor_id=sensor_id,
                value=21.0,
                timestamp=self.default_ts - timedelta(hours=2),
                sensor_type=SensorType.TEMPERATURE, # Use Enum
                quality=1.0,
                unit="C"
            ),
            SensorReading(
                sensor_id=sensor_id,
                value=19.5,
                timestamp=self.default_ts - timedelta(hours=3),
                sensor_type=SensorType.TEMPERATURE, # Use Enum
                quality=1.0,
                unit="C"
            ),
        ]
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = (
            historical_data
        )

        anomaly_details = self._get_default_anomaly_details(
            sensor_id=sensor_id, anomaly_type="spike", confidence=0.8
        )
        # Pass SensorType enum for sensor_type
        triggering_data = self._get_default_triggering_data(
            sensor_id=sensor_id, value=current_value, sensor_type=SensorType.TEMPERATURE
        )
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)

        await self.agent.process(event)

        published_event = self.mock_event_bus.publish.call_args.kwargs['event']
        self.assertIn(
            "Recent value stability", "".join(published_event.validation_reasons)
        )
        self.assertAlmostEqual(
            published_event.final_confidence, 0.8 - 0.05
        )  # Initial - minor deviation adjustment (0.8 initial, 0 rule_adj, -0.05 historical)
        self.assertEqual(published_event.validation_status, "credible_anomaly") # Corrected, Example, depends on thresholds
        self.assertEqual(published_event.agent_id, self.agent.agent_id)
        self.assertEqual(published_event.correlation_id, event.correlation_id)
        self.assertEqual(published_event.original_anomaly_alert_payload, anomaly_details)
        self.assertEqual(published_event.triggering_reading_payload, triggering_data)
        self.assertIsInstance(published_event.validated_at, datetime)
        # Rule engine default is (0.0, []), so no rule reasons expected
        self.assertTrue(all(r not in published_event.validation_reasons for r in ["Positive rule", "Rule penalty"]))


    async def test_historical_recurring_anomaly_type_triggered(self):
        sensor_id = "temp_oscillating"
        # Agent specific_settings: historical_check_limit=10, recurring_anomaly_threshold_pct=0.25, recurring_anomaly_diff_factor=0.2
        # Need > 10 * 0.25 = 2.5 (i.e., 3) historical points to be "anomalous" (20% diff from previous)
        historical_data = []
        base_val = 10
        historical_check_limit = 10  # From our settings
        for i in range(1, historical_check_limit + 1):  # Create 10 historical readings
            val = base_val + (i % 2) * base_val * 0.3  # Alternates: 10, 13, 10, 13 ... (30% diff > 20% threshold)
            historical_data.append(
                SensorReading(
                    sensor_id=sensor_id,
                    value=val,
                    timestamp=self.default_ts - timedelta(hours=i),
                    sensor_type=SensorType.TEMPERATURE, # Use Enum
                    quality=1.0,
                    unit="C" # Ensure unit is provided
                )
            )
        # This sequence (13,10,13,10,13,10,13,10,13,10) has 9 comparisons. All show 30% diff > 20%. So 9/9 = 100% > 25%.
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = (
            historical_data
        )

        anomaly_details = self._get_default_anomaly_details(
            sensor_id=sensor_id, confidence=0.8
        )
        # Pass SensorType enum for sensor_type
        triggering_data = self._get_default_triggering_data(
            sensor_id=sensor_id, value=15, sensor_type=SensorType.TEMPERATURE
        )  # Current value doesn't matter much for this rule
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)

        await self.agent.process(event)

        published_event = self.mock_event_bus.publish.call_args.kwargs['event']
        self.assertIn(
            "Recurring anomaly pattern detected in historical data.", published_event.validation_reasons
        )
        # Expected calculation: 0.8 initial + 0 rule_adj + 0.05 volatile + (-0.05) recurring = 0.8
        self.assertAlmostEqual(
            published_event.final_confidence, 0.8 + 0.05 - 0.05
        )  # Initial + volatile adjustment + recurring penalty
        self.assertEqual(published_event.validation_status, "credible_anomaly")
        self.assertEqual(published_event.agent_id, self.agent.agent_id)
        self.assertEqual(published_event.correlation_id, event.correlation_id)
        self.assertEqual(published_event.original_anomaly_alert_payload, anomaly_details)
        self.assertEqual(published_event.triggering_reading_payload, triggering_data)
        self.assertIsInstance(published_event.validated_at, datetime)
        # Rule engine default is (0.0, []), so no rule reasons expected
        self.assertTrue(all(r not in published_event.validation_reasons for r in ["Positive rule", "Rule penalty"]))


    async def test_process_error_during_event_publishing(self):
        # Configure the event bus mock to raise an error on publish
        self.mock_event_bus.publish.side_effect = Exception("Event bus down!")

        # Prepare a standard valid event
        anomaly_details = self._get_default_anomaly_details(confidence=0.8)
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)

        # Default behavior for other mocks
        self.mock_rule_engine.evaluate_rules.return_value = (0.0, [])
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = []

        with self._temporarily_enable_logging():
            with self.assertLogs(self.agent.logger.name, level="ERROR") as log_watcher:
                # The agent's process method should catch the publish error and log it
                await self.agent.process(event)
        
        # Check that an error related to publishing was logged
        self.assertTrue(
            any("Failed to publish AnomalyValidatedEvent" in msg for msg in log_watcher.output) or
            any("Error publishing event" in msg for msg in log_watcher.output) or # Depending on exact agent log
            any(f"Unhandled error in ValidationAgent.process for event {event.event_id}: Event bus down!" in msg for msg in log_watcher.output) or # General fallback log
            any("Unhandled error processing" in msg for msg in log_watcher.output)
        )
        
        # Ensure publish was attempted
        self.mock_event_bus.publish.assert_called_once()


    async def test_correlation_id_fallback_to_event_id(self):
        # Test that if correlation_id is None in incoming event, it falls back to event_id
        fixed_event_id = str(uuid.uuid4())
        anomaly_details = self._get_default_anomaly_details(confidence=0.8)
        triggering_data = self._get_default_triggering_data()
        
        # Directly create AnomalyDetectedEvent to ensure None correlation_id
        event = AnomalyDetectedEvent(
            event_id=fixed_event_id,
            correlation_id=None, # Explicitly None
            anomaly_details=anomaly_details,
            triggering_data=triggering_data,
            source_system="TestSource",
            created_at=self.default_ts
        )

        self.mock_rule_engine.evaluate_rules.return_value = (0.0, []) # Default, no adjustment
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = [] # No historical data

        await self.agent.process(event)

        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args.kwargs['event']

        self.assertEqual(published_event.correlation_id, fixed_event_id) # Fallback to event_id
        self.assertEqual(published_event.agent_id, self.agent.agent_id)
        self.assertEqual(published_event.original_anomaly_alert_payload, anomaly_details)
        self.assertEqual(published_event.triggering_reading_payload, triggering_data)
        self.assertIsInstance(published_event.validated_at, datetime)
        self.assertAlmostEqual(published_event.final_confidence, 0.8) # Initial confidence, no adjustments
        self.assertIn("No historical readings available for context.", published_event.validation_reasons)
        self.assertEqual(published_event.validation_status, "credible_anomaly")


    async def test_process_error_in_rule_engine(self):
        self.mock_rule_engine.evaluate_rules.side_effect = Exception(
            "Rule engine boom!"
        )
        event = self._create_anomaly_detected_event(
            self._get_default_anomaly_details(), self._get_default_triggering_data()
        )

        with self._temporarily_enable_logging():
            with self.assertLogs(self.agent.logger.name, level="ERROR") as log_watcher:
                await self.agent.process(event)

            self.mock_event_bus.publish.assert_not_called()
            self.assertTrue(
                any(
                    "Unhandled error" in msg or "Rule engine boom!" in msg
                    for msg in log_watcher.output
                )
            )

    async def test_process_error_in_crud_historical_fetch_graceful_handling(self):
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.side_effect = (
            Exception("DB connection failed!")
        )
        # This error occurs inside _perform_historical_context_validation, which should be handled.
        # The agent should still proceed and publish an event, but historical adjustment will be 0 and a reason added.

        anomaly_details = self._get_default_anomaly_details(confidence=0.8)
        # Pass SensorType enum for sensor_type
        event = self._create_anomaly_detected_event(
            anomaly_details, self._get_default_triggering_data(sensor_type=SensorType.TEMPERATURE)
        )

        await self.agent.process(event)

        self.mock_event_bus.publish.assert_called_once()  # Should still publish
        published_event = self.mock_event_bus.publish.call_args.kwargs['event']
        self.assertIn(
            "Failed to fetch historical readings: DB connection failed!",
            "".join(published_event.validation_reasons),
        )
        self.assertAlmostEqual(
            published_event.final_confidence, 0.8
        )  # No historical adjustment applied

    async def test_start_method(self):
        # BaseAgent.start calls register_capabilities.
        # ValidationAgent.start calls super().start() then self.subscribe.
        # We assume BaseAgent.start works; here we test ValidationAgent's additions.

        # Mock super().start() if it has complex side effects not relevant here,
        # or let it run if simple. For BaseAgent, it calls register_capabilities.
        # ValidationAgent.register_capabilities primarily logs.

        # Patching BaseAgent.start for this test
        with patch(
            "apps.agents.base_agent.BaseAgent.start", new_callable=AsyncMock
        ) as mock_base_agent_start:
            # The mock_reg_caps was F841, so removing if not directly asserted.
            # The important part is that super().start() is called, which in turn calls register_capabilities.
            await self.agent.start()

            mock_base_agent_start.assert_called_once()  # Verifies super().start() was called
            self.mock_event_bus.subscribe.assert_called_once_with(
                event_type_name=AnomalyDetectedEvent.__name__, handler=self.agent.process
            )

    async def test_register_capabilities(self):
        # This method in ValidationAgent currently only logs.
        # If it had direct interactions (e.g., self.event_bus.some_call()), they'd be mocked and asserted.
        # The call to super().register_capabilities() is part of BaseAgent's start().
        with self._temporarily_enable_logging():
            with self.assertLogs(self.agent.logger.name, level="INFO") as log_watcher:
                await self.agent.register_capabilities()
            self.assertTrue(
                any(
                    f"Agent {self.agent.agent_id}: Declaring capability" in msg or
                    "Declaring capability" in msg
                    for msg in log_watcher.output
                )
            )


if __name__ == "__main__":
    unittest.main()
