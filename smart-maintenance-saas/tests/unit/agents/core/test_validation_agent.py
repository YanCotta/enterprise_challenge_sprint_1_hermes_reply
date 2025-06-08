import unittest
from unittest.mock import (
    AsyncMock,
    Mock,
    patch,
)
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import uuid
import logging
from typing import Optional
from pydantic import ValidationError

from apps.agents.core.validation_agent import ValidationAgent
from core.events.event_models import AnomalyDetectedEvent, AnomalyValidatedEvent
from data.schemas import AnomalyAlert, SensorReading, SensorType
from core.base_agent_abc import BaseAgent

logging.disable(logging.CRITICAL)

class TestValidationAgent(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_event_bus = AsyncMock()
        self.mock_crud_sensor_reading = AsyncMock()
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id = AsyncMock(return_value=[])
        self.mock_rule_engine = AsyncMock()
        self.mock_rule_engine.evaluate_rules = AsyncMock(return_value=(0.0, []))
        self.mock_db_session_factory = Mock()
        self.mock_db_session = AsyncMock()
        self.mock_db_session.close = AsyncMock()
        self.mock_db_session_factory.return_value = self.mock_db_session
        self.agent = ValidationAgent(
            agent_id="test_validator",
            event_bus=self.mock_event_bus,
            db_session_factory=self.mock_db_session_factory,
            crud_sensor_reading=self.mock_crud_sensor_reading,
            rule_engine=self.mock_rule_engine,
            specific_settings={
                "credible_threshold": 0.7,
                "false_positive_threshold": 0.4,
                "historical_check_limit": 10,
                "recent_stability_window": 3,
                "recent_stability_factor": 0.1,
                "recent_stability_min_std_dev": 0.05,
                "recent_stability_jump_adjustment": 0.10,
                "recent_stability_minor_deviation_adjustment": -0.05,
                "volatile_baseline_adjustment": 0.05,
                "recurring_anomaly_diff_factor": 0.2,
                "recurring_anomaly_threshold_pct": 0.25,
                "recurring_anomaly_penalty": -0.05,
            },
        )
        self.default_ts = datetime.utcnow()
        self.expected_logger_name = f"apps.agents.core.validation_agent.{self.agent.agent_id}"

    @contextmanager
    def _temporarily_enable_logging(self):
        logging.disable(logging.NOTSET)
        try:
            yield
        finally:
            logging.disable(logging.CRITICAL)

    def _create_anomaly_detected_event(
        self,
        anomaly_details: dict,
        triggering_data: dict,
        correlation_id: Optional[str] = None,
        event_id: Optional[str] = None,
        source_system: str = "TestSource",
    ) -> AnomalyDetectedEvent:
        # Ensure 'created_at' in anomaly_details is a datetime object if not already
        if 'created_at' in anomaly_details and isinstance(anomaly_details['created_at'], str):
            anomaly_details['created_at'] = datetime.fromisoformat(anomaly_details['created_at'])
        elif 'created_at' not in anomaly_details: # Ensure it has a default for tests not focusing on its absence
             anomaly_details['created_at'] = self.default_ts

        # Ensure 'timestamp' in triggering_data is a datetime object if not already (and if present)
        if 'timestamp' in triggering_data and isinstance(triggering_data['timestamp'], str):
            triggering_data['timestamp'] = datetime.fromisoformat(triggering_data['timestamp'])
        
        return AnomalyDetectedEvent(
            event_id=event_id or str(uuid.uuid4()),
            correlation_id=correlation_id or str(uuid.uuid4()),
            anomaly_details=anomaly_details,
            triggering_data=triggering_data,
            source_system=source_system,
            created_at=self.default_ts, # Event's own created_at, not the anomaly's
        )

    def _get_default_anomaly_details(
        self, confidence=0.8, sensor_id="sensor_A", anomaly_type="spike", severity=4
    ) -> dict:
        return {
            "sensor_id": sensor_id,
            "anomaly_type": anomaly_type,
            "severity": severity,
            "confidence": confidence,
            "description": "Test anomaly",
            "created_at": self.default_ts, # This is a datetime object
        }

    def _get_default_triggering_data(
        self, sensor_id="sensor_A", value=100.0, quality=0.9, sensor_type: SensorType = SensorType.TEMPERATURE
    ) -> dict:
        return {
            "sensor_id": sensor_id,
            "timestamp": self.default_ts.isoformat(), # This is a string, Pydantic will parse
            "value": value,
            "sensor_type": sensor_type,
            "unit": "C",
            "quality": quality,
        }

    async def test_process_successful_credible_anomaly(self):
        self.mock_rule_engine.evaluate_rules.return_value = (0.1, ["Rule reason: positive adjustment"])
        event_corr_id = str(uuid.uuid4())
        anomaly_details = self._get_default_anomaly_details(confidence=0.75)
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data, correlation_id=event_corr_id)
        await self.agent.process(event)
        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args.args[0]
        self.assertIsInstance(published_event, AnomalyValidatedEvent)
        self.assertEqual(published_event.validation_status, "credible_anomaly")
        self.assertAlmostEqual(published_event.final_confidence, 0.85)
        self.assertEqual(published_event.agent_id, self.agent.agent_id)
        self.assertEqual(published_event.correlation_id, event_corr_id) 
        self.assertEqual(published_event.original_anomaly_alert_payload, anomaly_details)
        self.assertEqual(published_event.triggering_reading_payload, triggering_data)
        self.assertIn("Rule reason: positive adjustment", published_event.validation_reasons)
        self.assertIsInstance(published_event.validated_at, datetime)
        now = datetime.now(timezone.utc)
        validated_at = published_event.validated_at
        if validated_at.tzinfo is None: # Ensure timezone aware for comparison
            validated_at = validated_at.replace(tzinfo=timezone.utc)
        self.assertTrue((now - validated_at) < timedelta(seconds=5))

    async def test_process_successful_false_positive(self):
        rule_reasons = ["Rule reason: major penalty"]
        self.mock_rule_engine.evaluate_rules.return_value = (-0.3, rule_reasons)
        anomaly_details = self._get_default_anomaly_details(confidence=0.5)
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)
        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args.args[0]
        self.assertEqual(published_event.validation_status, "false_positive_suspected") 
        self.assertAlmostEqual(published_event.final_confidence, 0.2) 
        expected_reasons = rule_reasons + ["No historical readings available for context."]
        self.assertEqual(sorted(published_event.validation_reasons), sorted(expected_reasons))

    async def test_process_successful_uncertain(self):
        rule_reasons = ["Rule reason: minor penalty"]
        self.mock_rule_engine.evaluate_rules.return_value = (-0.1, rule_reasons)
        anomaly_details = self._get_default_anomaly_details(confidence=0.6)
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)
        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args.args[0]
        self.assertEqual(published_event.validation_status, "further_investigation_needed") 
        self.assertAlmostEqual(published_event.final_confidence, 0.5) 
        expected_reasons = rule_reasons + ["No historical readings available for context."]
        self.assertEqual(sorted(published_event.validation_reasons), sorted(expected_reasons))

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
        published_event = self.mock_event_bus.publish.call_args.args[0]
        self.assertAlmostEqual(published_event.final_confidence, 1.0) 
        self.assertEqual(published_event.validation_status, "credible_anomaly")

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
        published_event = self.mock_event_bus.publish.call_args.args[0]
        self.assertAlmostEqual(published_event.final_confidence, 0.0) 
        self.assertEqual(published_event.validation_status, "false_positive_suspected")

    async def test_status_boundary_credible_exact_zero_adjustments(self):
        initial_confidence = self.agent.settings["credible_threshold"] 
        self.mock_rule_engine.evaluate_rules.return_value = (0.0, []) 
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = [] 
        anomaly_details = self._get_default_anomaly_details(confidence=initial_confidence)
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)
        published_event = self.mock_event_bus.publish.call_args.args[0]
        self.assertAlmostEqual(published_event.final_confidence, initial_confidence)
        self.assertEqual(published_event.validation_status, "credible_anomaly")

    async def test_status_boundary_further_investigation_just_below_credible(self):
        initial_confidence = self.agent.settings["credible_threshold"] - 0.001
        self.mock_rule_engine.evaluate_rules.return_value = (0.0, [])
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = []
        anomaly_details = self._get_default_anomaly_details(confidence=initial_confidence)
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)
        published_event = self.mock_event_bus.publish.call_args.args[0]
        self.assertAlmostEqual(published_event.final_confidence, initial_confidence)
        self.assertEqual(published_event.validation_status, "further_investigation_needed")

    async def test_status_boundary_further_investigation_exact_at_false_positive_upper(self):
        initial_confidence = self.agent.settings["false_positive_threshold"]
        self.mock_rule_engine.evaluate_rules.return_value = (0.0, [])
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = []
        anomaly_details = self._get_default_anomaly_details(confidence=initial_confidence)
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)
        published_event = self.mock_event_bus.publish.call_args.args[0]
        self.assertAlmostEqual(published_event.final_confidence, initial_confidence)
        self.assertEqual(published_event.validation_status, "further_investigation_needed")

    async def test_status_boundary_false_positive_just_below_further_investigation(self):
        initial_confidence = self.agent.settings["false_positive_threshold"] - 0.001
        self.mock_rule_engine.evaluate_rules.return_value = (0.0, [])
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = []
        anomaly_details = self._get_default_anomaly_details(confidence=initial_confidence)
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)
        published_event = self.mock_event_bus.publish.call_args.args[0]
        self.assertAlmostEqual(published_event.final_confidence, initial_confidence)
        self.assertEqual(published_event.validation_status, "false_positive_suspected")

    async def test_process_input_parsing_failure_anomaly_details(self):
        triggering_data = self._get_default_triggering_data()
        event = AnomalyDetectedEvent(
            event_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
            anomaly_details="invalid_not_a_dict",
            triggering_data=triggering_data,
            source_system="TestSource",
            created_at=self.default_ts
        )
        with self._temporarily_enable_logging():
            with self.assertLogs(self.expected_logger_name, level="ERROR") as log_watcher:
                await self.agent.process(event)
        self.assertTrue(
            any("anomaly_details or triggering_data is not a dict" in record.getMessage() for record in log_watcher.records)
        )
        self.mock_event_bus.publish.assert_not_called()

    async def test_correlation_id_fallback_to_event_id(self):
        fixed_event_id = str(uuid.uuid4())
        anomaly_details = self._get_default_anomaly_details(confidence=0.8)
        triggering_data = self._get_default_triggering_data()
        event = AnomalyDetectedEvent(
            event_id=fixed_event_id,
            correlation_id=None, 
            anomaly_details=anomaly_details,
            triggering_data=triggering_data,
            source_system="TestSource",
            created_at=self.default_ts
        )
        await self.agent.process(event)
        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args.args[0]
        self.assertEqual(published_event.correlation_id, fixed_event_id)

    async def test_process_error_in_crud_historical_fetch(self):
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.side_effect = Exception("DB connection failed!")
        anomaly_details = self._get_default_anomaly_details(confidence=0.8)
        triggering_data = self._get_default_triggering_data(sensor_type=SensorType.TEMPERATURE)
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        with self._temporarily_enable_logging():
            with self.assertLogs(self.expected_logger_name, level="ERROR") as log_watcher:
                await self.agent.process(event)
        self.assertTrue(any("DB connection failed!" in msg for msg in log_watcher.output))
        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args.args[0]
        self.assertIn("Historical data fetch failed.", published_event.validation_reasons)

    async def test_process_parsing_failure_malformed_anomaly_details(self):
        malformed_details = {"sensor_id": "test_sensor"} 
        event = self._create_anomaly_detected_event(malformed_details, self._get_default_triggering_data())
        with self._temporarily_enable_logging():
            with self.assertLogs(self.expected_logger_name, level="ERROR") as log_watcher:
                await self.agent.process(event)
        self.mock_event_bus.publish.assert_not_called()
        self.assertTrue(
            any(isinstance(record.exc_info[1], ValidationError) for record in log_watcher.records if record.exc_info)
        )

    async def test_process_input_parsing_failure_triggering_data(self):
        anomaly_details = self._get_default_anomaly_details()
        event = AnomalyDetectedEvent(
            event_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
            anomaly_details=anomaly_details,
            triggering_data="not_a_dict", 
            source_system="TestSource",
            created_at=self.default_ts
        )
        with self._temporarily_enable_logging():
            with self.assertLogs(self.expected_logger_name, level="ERROR") as log_watcher:
                await self.agent.process(event)
        self.assertTrue(
            any("anomaly_details or triggering_data is not a dict" in record.getMessage() for record in log_watcher.records)
        )
        self.mock_event_bus.publish.assert_not_called()

    async def test_process_parsing_failure_anomaly_missing_sensor_id(self):
        details = self._get_default_anomaly_details()
        del details["sensor_id"] 
        event = self._create_anomaly_detected_event(details, self._get_default_triggering_data())
        with self._temporarily_enable_logging():
            with self.assertLogs(self.expected_logger_name, level="ERROR") as log_watcher:
                await self.agent.process(event)
        self.mock_event_bus.publish.assert_not_called()
        self.assertTrue(
            any(isinstance(record.exc_info[1], ValidationError) for record in log_watcher.records if record.exc_info)
        )

    async def test_process_parsing_failure_anomaly_missing_created_at(self):
        details = self._get_default_anomaly_details()
        del details["created_at"] 
        event = self._create_anomaly_detected_event(details, self._get_default_triggering_data())
        with self._temporarily_enable_logging():
             await self.agent.process(event) 
        self.mock_event_bus.publish.assert_called_once()

    async def test_process_parsing_failure_triggering_missing_timestamp(self):
        data = self._get_default_triggering_data()
        del data["timestamp"] 
        event = self._create_anomaly_detected_event(self._get_default_anomaly_details(), data)
        with self._temporarily_enable_logging():
            await self.agent.process(event)
        self.mock_event_bus.publish.assert_called_once()
        # Check that the event published has "No historical readings" because timestamp was None
        # and mock CRUD returned [] for end_time=None
        published_event = self.mock_event_bus.publish.call_args.args[0]
        self.assertIn("No historical readings available for context.", published_event.validation_reasons)


    async def test_process_parsing_failure_triggering_missing_value(self):
        data = self._get_default_triggering_data()
        del data["value"] 
        event = self._create_anomaly_detected_event(self._get_default_anomaly_details(), data)
        with self._temporarily_enable_logging():
            with self.assertLogs(self.expected_logger_name, level="ERROR") as log_watcher:
                await self.agent.process(event)
        self.mock_event_bus.publish.assert_not_called()
        self.assertTrue(
            any(isinstance(record.exc_info[1], ValidationError) for record in log_watcher.records if record.exc_info)
        )

    async def test_process_parsing_failure_triggering_invalid_sensor_type(self):
        data = self._get_default_triggering_data()
        data["sensor_type"] = "INVALID_TYPE" 
        event = self._create_anomaly_detected_event(self._get_default_anomaly_details(), data)
        with self._temporarily_enable_logging():
            with self.assertLogs(self.expected_logger_name, level="ERROR") as log_watcher:
                await self.agent.process(event)
        self.mock_event_bus.publish.assert_not_called()
        self.assertTrue(
            any(isinstance(record.exc_info[1], ValidationError) for record in log_watcher.records if record.exc_info)
        )

    async def test_rule_engine_interaction(self):
        anomaly_details = self._get_default_anomaly_details()
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)
        self.mock_rule_engine.evaluate_rules.assert_called_once()
        call_kwargs = self.mock_rule_engine.evaluate_rules.call_args.kwargs
        self.assertIsInstance(call_kwargs['alert'], AnomalyAlert)
        self.assertIsInstance(call_kwargs['reading'], SensorReading)
        self.assertEqual(call_kwargs['alert'].sensor_id, anomaly_details["sensor_id"])
        self.assertEqual(call_kwargs['reading'].value, triggering_data["value"])

    async def test_crud_sensor_reading_interaction(self):
        anomaly_details = self._get_default_anomaly_details(sensor_id="sensor_X")
        triggering_data = self._get_default_triggering_data(sensor_id="sensor_X")
        # Ensure timestamp is datetime for direct comparison if CRUD method expects it
        # Here, SensorReading Pydantic model handles conversion from ISO string
        parsed_reading = SensorReading(**triggering_data) 
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.assert_called_once_with(
            db=self.mock_db_session,
            sensor_id="sensor_X",
            limit=self.agent.historical_check_limit,
            end_time=parsed_reading.timestamp, 
        )

    async def test_historical_validation_empty_list(self):
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = []
        initial_confidence = 0.8
        self.mock_rule_engine.evaluate_rules.return_value = (0.05, ["Positive rule"])
        anomaly_details = self._get_default_anomaly_details(confidence=initial_confidence)
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)
        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args.args[0]
        self.assertAlmostEqual(published_event.final_confidence, 0.85)
        self.assertIn("No historical readings available for context.", published_event.validation_reasons)
        self.assertIn("Positive rule", published_event.validation_reasons)

    async def test_historical_recent_value_stability_triggered(self):
        sensor_id = "temp_stable"
        current_value = 20.5
        historical_data = [
            SensorReading(sensor_id=sensor_id, value=20.0, timestamp=self.default_ts - timedelta(hours=1), sensor_type=SensorType.TEMPERATURE, quality=1.0, unit="C"),
            SensorReading(sensor_id=sensor_id, value=21.0, timestamp=self.default_ts - timedelta(hours=2), sensor_type=SensorType.TEMPERATURE, quality=1.0, unit="C"),
            SensorReading(sensor_id=sensor_id, value=19.5, timestamp=self.default_ts - timedelta(hours=3), sensor_type=SensorType.TEMPERATURE, quality=1.0, unit="C"),
        ]
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = historical_data
        anomaly_details = self._get_default_anomaly_details(sensor_id=sensor_id, anomaly_type="spike", confidence=0.8)
        triggering_data = self._get_default_triggering_data(sensor_id=sensor_id, value=current_value, sensor_type=SensorType.TEMPERATURE)
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)
        published_event = self.mock_event_bus.publish.call_args.args[0]
        avg_recent_value_formatted = f"{20.166666666666668:.2f}"
        std_dev_recent_formatted = f"{0.6236095644623235:.2f}"
        expected_reason = (
            f"Recent value stability: Anomaly (value: {current_value}) is a minor deviation "
            f"from a recently stable baseline (avg: {avg_recent_value_formatted}, std_dev: {std_dev_recent_formatted})."
        )
        self.assertIn(expected_reason, published_event.validation_reasons)
        self.assertAlmostEqual(published_event.final_confidence, 0.75)

    async def test_historical_recurring_anomaly_type_triggered(self):
        sensor_id = "temp_oscillating"
        historical_data = []
        base_val = 10
        historical_check_limit = 10 
        for i in range(1, historical_check_limit + 1):
            val = base_val + (i % 2) * base_val * 0.3 
            historical_data.append(SensorReading(sensor_id=sensor_id, value=val, timestamp=self.default_ts - timedelta(hours=i), sensor_type=SensorType.TEMPERATURE, quality=1.0, unit="C"))
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = historical_data
        anomaly_details = self._get_default_anomaly_details(sensor_id=sensor_id, confidence=0.8)
        triggering_data = self._get_default_triggering_data(sensor_id=sensor_id, value=15, sensor_type=SensorType.TEMPERATURE)
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)
        published_event = self.mock_event_bus.publish.call_args.args[0]
        current_value_for_reason = 15.0 
        avg_recent_value_for_reason = 12.00
        std_dev_recent_for_reason = 1.41421356
        expected_reason_volatile = (
            f"Anomaly (value: {current_value_for_reason:.1f}) occurred during a period of volatile readings " 
            f"(avg: {avg_recent_value_for_reason:.2f}, std_dev: {std_dev_recent_for_reason:.2f}). "
            "Less adjustment made."
        )
        expected_reason_recurring = "Recurring anomaly pattern detected in historical data."
        self.assertIn(expected_reason_volatile, published_event.validation_reasons)
        self.assertIn(expected_reason_recurring, published_event.validation_reasons)
        self.assertAlmostEqual(published_event.final_confidence, 0.8)

    async def test_process_error_during_event_publishing(self):
        self.mock_event_bus.publish.side_effect = Exception("Event bus down!")
        anomaly_details = self._get_default_anomaly_details(confidence=0.8)
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        with self._temporarily_enable_logging():
            with self.assertLogs(self.expected_logger_name, level="ERROR") as log_watcher:
                await self.agent.process(event)
        self.assertTrue(
            any("Unhandled error processing" in record.getMessage() and "Event bus down!" in record.getMessage() 
                for record in log_watcher.records)
        )
        self.mock_event_bus.publish.assert_called_once()

    async def test_process_error_in_rule_engine(self):
        self.mock_rule_engine.evaluate_rules.side_effect = Exception("Rule engine boom!")
        event = self._create_anomaly_detected_event(self._get_default_anomaly_details(), self._get_default_triggering_data())
        with self._temporarily_enable_logging():
            with self.assertLogs(self.expected_logger_name, level="ERROR") as log_watcher:
                await self.agent.process(event)
        self.mock_event_bus.publish.assert_not_called()
        self.assertTrue(
            any("Unhandled error processing" in record.getMessage() and "Rule engine boom!" in record.getMessage() 
                for record in log_watcher.records)
        )
        
    async def test_process_error_in_crud_historical_fetch_graceful_handling(self):
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.side_effect = Exception("DB connection failed!")
        anomaly_details = self._get_default_anomaly_details(confidence=0.8)
        event = self._create_anomaly_detected_event(anomaly_details, self._get_default_triggering_data(sensor_type=SensorType.TEMPERATURE))
        await self.agent.process(event)
        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args.args[0]
        self.assertIn("Historical data fetch failed.", published_event.validation_reasons)
        self.assertAlmostEqual(published_event.final_confidence, 0.8)

    async def test_start_method(self):
        with patch("apps.agents.base_agent.BaseAgent.start", new_callable=AsyncMock) as mock_base_agent_start:
            await self.agent.start()
            mock_base_agent_start.assert_called_once()
            self.mock_event_bus.subscribe.assert_called_once_with(
                event_type_name=AnomalyDetectedEvent.__name__, handler=self.agent.process
            )

    async def test_register_capabilities(self):
        with self._temporarily_enable_logging():
            with self.assertLogs(self.expected_logger_name, level="INFO") as log_watcher: 
                await self.agent.register_capabilities()
        self.assertTrue(any(f"Agent {self.agent.agent_id}: Declaring capability" in msg for msg in log_watcher.output))

if __name__ == "__main__":
    unittest.main()
