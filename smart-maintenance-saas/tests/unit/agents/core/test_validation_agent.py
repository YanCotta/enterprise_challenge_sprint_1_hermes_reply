import unittest
from unittest.mock import (
    AsyncMock,
    patch,
    # MagicMock, ANY were F401, so removed
)
from datetime import datetime, timedelta
import uuid
import logging
from typing import Optional  # Added Optional

from apps.agents.core.validation_agent import ValidationAgent
from core.events.event_models import AnomalyDetectedEvent, AnomalyValidatedEvent
from data.schemas import AnomalyAlert, SensorReading
from apps.agents.base_agent import BaseAgent  # noqa: F401 - Used in patch string

# Disable logging for tests unless specifically testing log output
logging.disable(logging.CRITICAL)


class TestValidationAgent(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_event_bus = AsyncMock()
        self.mock_crud_sensor_reading = AsyncMock()
        self.mock_rule_engine = AsyncMock()

        # Default return values for mocks
        self.mock_rule_engine.evaluate_rules.return_value = (0.0, [])
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = []

        self.agent = ValidationAgent(
            agent_id="test_validator",
            event_bus=self.mock_event_bus,
            crud_sensor_reading=self.mock_crud_sensor_reading,
            rule_engine=self.mock_rule_engine,
            specific_settings={  # Ensure agent uses these, not defaults if they differ
                "credible_threshold": 0.7,
                "false_positive_threshold": 0.4,
                "historical_check_limit": 10,  # smaller for tests
                "recent_stability_window": 3,  # smaller for tests
            },
        )
        self.default_ts = datetime.utcnow()

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
        return {
            "sensor_id": sensor_id,
            "anomaly_type": anomaly_type,
            "severity": severity,
            "confidence": confidence,
            "description": "Test anomaly",
            "timestamp": self.default_ts.isoformat(),
        }

    def _get_default_triggering_data(
        self, sensor_id="sensor_A", value=100.0, quality=0.9, sensor_type="TEMPERATURE"
    ) -> dict:
        return {
            "sensor_id": sensor_id,
            "timestamp": self.default_ts.isoformat(),
            "value": value,
            "sensor_type": sensor_type,
            "unit": "C",
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
        published_event = self.mock_event_bus.publish.call_args[0][0]
        self.assertIsInstance(published_event, AnomalyValidatedEvent)
        self.assertEqual(published_event.validation_status, "CONFIRMED_CREDIBLE")
        self.assertAlmostEqual(
            published_event.final_confidence, 0.85
        )  # 0.75 (initial) + 0.1 (rule)
        self.assertEqual(published_event.agent_id, "test_validator")
        self.assertEqual(published_event.correlation_id, event_corr_id)
        self.assertEqual(
            published_event.original_anomaly_alert_payload, anomaly_details
        )
        self.assertEqual(published_event.triggering_reading_payload, triggering_data)
        self.assertIn(
            "Rule reason: positive adjustment", published_event.validation_reasons
        )

    async def test_process_successful_false_positive(self):
        self.mock_rule_engine.evaluate_rules.return_value = (
            -0.3,
            ["Rule reason: major penalty"],
        )

        anomaly_details = self._get_default_anomaly_details(
            confidence=0.5
        )  # Medium initial confidence
        event = self._create_anomaly_detected_event(
            anomaly_details, self._get_default_triggering_data()
        )

        await self.agent.process(event)

        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args[0][0]
        self.assertEqual(published_event.validation_status, "POTENTIAL_FALSE_POSITIVE")
        self.assertAlmostEqual(published_event.final_confidence, 0.2)  # 0.5 - 0.3

    async def test_process_successful_uncertain(self):
        self.mock_rule_engine.evaluate_rules.return_value = (
            -0.1,
            ["Rule reason: minor penalty"],
        )
        anomaly_details = self._get_default_anomaly_details(
            confidence=0.6
        )  # Initial: 0.6 -> Final: 0.5
        event = self._create_anomaly_detected_event(
            anomaly_details, self._get_default_triggering_data()
        )

        await self.agent.process(event)

        self.mock_event_bus.publish.assert_called_once()
        published_event = self.mock_event_bus.publish.call_args[0][0]
        self.assertEqual(published_event.validation_status, "UNCERTAIN")
        self.assertAlmostEqual(published_event.final_confidence, 0.5)  # 0.6 - 0.1

    async def test_process_input_parsing_failure_anomaly_details(self):
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

        with self.assertLogs(self.agent.logger.name, level="ERROR") as log_watcher:
            await self.agent.process(event)

        self.mock_event_bus.publish.assert_not_called()
        self.assertTrue(
            any("Error parsing SensorReading" in msg for msg in log_watcher.output)
        )

    async def test_rule_engine_interaction(self):
        anomaly_details = self._get_default_anomaly_details()
        triggering_data = self._get_default_triggering_data()
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)

        await self.agent.process(event)

        self.mock_rule_engine.evaluate_rules.assert_called_once()
        call_args = self.mock_rule_engine.evaluate_rules.call_args[0]
        self.assertIsInstance(call_args[0], AnomalyAlert)  # First arg is AnomalyAlert
        self.assertIsInstance(
            call_args[1], SensorReading
        )  # Second arg is SensorReading
        self.assertEqual(call_args[0].sensor_id, anomaly_details["sensor_id"])
        self.assertEqual(call_args[1].value, triggering_data["value"])

    async def test_crud_sensor_reading_interaction(self):
        anomaly_details = self._get_default_anomaly_details(sensor_id="sensor_X")
        triggering_data = self._get_default_triggering_data(sensor_id="sensor_X")
        # Make sure the triggering_data timestamp is a datetime object for comparison
        parsed_reading = SensorReading(**triggering_data)

        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)
        await self.agent.process(event)

        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.assert_called_once_with(
            sensor_id="sensor_X",
            limit=self.agent.historical_check_limit,  # Using agent's setting
            before_timestamp=parsed_reading.timestamp,
        )

    async def test_historical_recent_value_stability_triggered(self):
        sensor_id = "temp_stable"
        current_value = 20.5
        # Agent specific_settings: recent_stability_window = 3
        # Historical readings: mean should be close to current_value
        # (20 + 21 + 19.5) / 3 = 60.5 / 3 = 20.1666...
        # current_value 20.5. Difference = 0.333. Stability factor 0.05 * 20.16 = 1.008. Triggered.
        historical_data = [
            SensorReading(
                sensor_id=sensor_id,
                value=20.0,
                timestamp=self.default_ts - timedelta(hours=1),
                sensor_type="TEMPERATURE",
                quality=1.0,
            ),
            SensorReading(
                sensor_id=sensor_id,
                value=21.0,
                timestamp=self.default_ts - timedelta(hours=2),
                sensor_type="TEMPERATURE",
                quality=1.0,
            ),
            SensorReading(
                sensor_id=sensor_id,
                value=19.5,
                timestamp=self.default_ts - timedelta(hours=3),
                sensor_type="TEMPERATURE",
                quality=1.0,
            ),
        ]
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = (
            historical_data
        )

        anomaly_details = self._get_default_anomaly_details(
            sensor_id=sensor_id, anomaly_type="spike", confidence=0.8
        )
        triggering_data = self._get_default_triggering_data(
            sensor_id=sensor_id, value=current_value
        )
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)

        await self.agent.process(event)

        published_event = self.mock_event_bus.publish.call_args[0][0]
        self.assertIn(
            "Recent value stability", "".join(published_event.validation_reasons)
        )
        self.assertAlmostEqual(
            published_event.final_confidence, 0.8 - 0.1
        )  # Initial - stability adjustment

    async def test_historical_recurring_anomaly_type_triggered(self):
        sensor_id = "temp_oscillating"
        # Agent specific_settings: historical_check_limit=10, recurring_anomaly_threshold_pct=0.25, recurring_anomaly_diff_factor=0.5
        # Need > 10 * 0.25 = 2.5 (i.e., 3) historical points to be "anomalous" (50% diff from previous)
        historical_data = []
        base_val = 10
        for i in range(
            1, self.agent.historical_check_limit + 1
        ):  # Create 10 historical readings
            val = (
                base_val + (i % 2) * base_val * 0.6
            )  # Alternates: 10, 16, 10, 16 ... (60% diff)
            historical_data.append(
                SensorReading(
                    sensor_id=sensor_id,
                    value=val,
                    timestamp=self.default_ts - timedelta(hours=i),
                    sensor_type="TEMPERATURE",
                    quality=1.0,
                )
            )
        # This sequence (10,16,10,16...) has 9 comparisons. All show 60% diff. So 9/10 > 0.25.
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.return_value = (
            historical_data
        )

        anomaly_details = self._get_default_anomaly_details(
            sensor_id=sensor_id, confidence=0.8
        )
        triggering_data = self._get_default_triggering_data(
            sensor_id=sensor_id, value=15
        )  # Current value doesn't matter much for this rule
        event = self._create_anomaly_detected_event(anomaly_details, triggering_data)

        await self.agent.process(event)

        published_event = self.mock_event_bus.publish.call_args[0][0]
        self.assertIn(
            "Recurring anomaly pattern", "".join(published_event.validation_reasons)
        )
        self.assertAlmostEqual(
            published_event.final_confidence, 0.8 - 0.05
        )  # Initial - recurring adjustment

    async def test_process_error_in_rule_engine(self):
        self.mock_rule_engine.evaluate_rules.side_effect = Exception(
            "Rule engine boom!"
        )
        event = self._create_anomaly_detected_event(
            self._get_default_anomaly_details(), self._get_default_triggering_data()
        )

        with self.assertLogs(self.agent.logger.name, level="ERROR") as log_watcher:
            await self.agent.process(event)

        self.mock_event_bus.publish.assert_not_called()
        self.assertTrue(
            any(
                "Unhandled error in ValidationAgent.process" in msg
                for msg in log_watcher.output
            )
        )
        self.assertTrue(any("Rule engine boom!" in msg for msg in log_watcher.output))

    async def test_process_error_in_crud_historical_fetch(self):
        self.mock_crud_sensor_reading.get_sensor_readings_by_sensor_id.side_effect = (
            Exception("DB connection failed!")
        )
        # This error occurs inside _perform_historical_context_validation, which should be handled.
        # The agent should still proceed and publish an event, but historical adjustment will be 0 and a reason added.

        anomaly_details = self._get_default_anomaly_details(confidence=0.8)
        event = self._create_anomaly_detected_event(
            anomaly_details, self._get_default_triggering_data()
        )

        await self.agent.process(event)

        self.mock_event_bus.publish.assert_called_once()  # Should still publish
        published_event = self.mock_event_bus.publish.call_args[0][0]
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
                AnomalyDetectedEvent.__name__, self.agent.process
            )

    async def test_register_capabilities(self):
        # This method in ValidationAgent currently only logs.
        # If it had direct interactions (e.g., self.event_bus.some_call()), they'd be mocked and asserted.
        # The call to super().register_capabilities() is part of BaseAgent's start().
        with self.assertLogs(self.agent.logger.name, level="INFO") as log_watcher:
            await self.agent.register_capabilities()
        self.assertTrue(
            any(
                f"Agent {self.agent.agent_id} registering capabilities" in msg
                for msg in log_watcher.output
            )
        )


if __name__ == "__main__":
    unittest.main()
