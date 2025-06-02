import logging
import asyncio
from datetime import datetime, timedelta
from typing import (
    Optional,
    Dict,
    Any,
    List,
    Tuple,
    Callable,
)  # Added Callable, Any here
import statistics  # For mean calculation

from pydantic import parse_obj_as, ValidationError

# Core components from the project
from core.events.event_models import (
    AnomalyValidatedEvent,
    AnomalyDetectedEvent,
    BaseEventModel,
)
from core.models.data_models import AnomalyAlert, SensorReading
from apps.agents.base_agent import BaseAgent
from apps.rules.validation_rules import RuleEngine

# Assuming CRUDSensorReading is in core.database.crud.crud_sensor_reading
try:
    from core.database.crud.crud_sensor_reading import CRUDSensorReading
except ImportError:
    logging.error(
        "ValidationAgent: CRUDSensorReading not found. Historical context will fail."
    )

    # Define a dummy CRUDSensorReading if not found, so the agent can be instantiated
    class CRUDSensorReading:
        async def get_sensor_readings_by_sensor_id(
            self, **kwargs
        ) -> List[Any]:  # Added Any for List type hint
            return []


class ValidationAgent(BaseAgent):
    def __init__(
        self,
        agent_id: str,
        event_bus: Any,  # Should be an instance of an EventBus supporting async subscribe/publish
        crud_sensor_reading: CRUDSensorReading,
        rule_engine: RuleEngine,
        specific_settings: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(agent_id, event_bus, specific_settings)
        self.crud_sensor_reading = crud_sensor_reading
        self.rule_engine = rule_engine

        # Overwrite default logger from BaseAgent to include agent_id more explicitly if desired,
        # or ensure BaseAgent's logger is sufficient. BaseAgent already does getLogger(f"agent.{self.agent_id}")
        # self.logger = logging.getLogger(f"ValidationAgent.{self.agent_id}") # Example if more specific logger needed

        # Thresholds for validation_status determination
        self.credible_threshold: float = self.specific_settings.get(
            "credible_threshold", 0.7
        )
        self.false_positive_threshold: float = self.specific_settings.get(
            "false_positive_threshold", 0.4
        )

        # Settings for historical context validation
        self.historical_check_limit: int = self.specific_settings.get(
            "historical_check_limit", 20
        )
        self.recent_stability_window: int = self.specific_settings.get(
            "recent_stability_window", 5
        )
        self.recent_stability_factor: float = self.specific_settings.get(
            "recent_stability_factor", 0.05
        )  # e.g. 5% of mean
        self.recurring_anomaly_threshold_pct: float = self.specific_settings.get(
            "recurring_anomaly_threshold_pct", 0.25
        )  # 25%
        self.recurring_anomaly_diff_factor: float = self.specific_settings.get(
            "recurring_anomaly_diff_factor", 0.5
        )  # 50% diff from previous

        self.logger.info(
            f"ValidationAgent '{self.agent_id}' initialized with credible_threshold={self.credible_threshold}, "
            f"false_positive_threshold={self.false_positive_threshold}"
        )

    async def register_capabilities(self) -> None:
        """Registers interest in AnomalyDetectedEvent."""
        # This method is called by BaseAgent.start()
        # The actual subscription logic is handled in start() via self.subscribe
        self.logger.info(
            f"Agent {self.agent_id} registering capabilities: processing '{AnomalyDetectedEvent.__name__}'."
        )
        # If the event bus requires explicit registration of events an agent can process:
        # await self.event_bus.register_event_handler(AnomalyDetectedEvent.__name__, self.process)

    async def start(self) -> None:
        """Starts the agent and subscribes to AnomalyDetectedEvent."""
        await super().start()  # Calls register_capabilities, sets self._is_running
        if self.event_bus:
            # The event name string is often derived from the class name itself.
            await self.subscribe(AnomalyDetectedEvent.__name__, self.process)
            self.logger.info(
                f"Agent {self.agent_id} subscribed to '{AnomalyDetectedEvent.__name__}'."
            )
        else:
            self.logger.error(
                f"Agent {self.agent_id} cannot start: Event bus is not configured."
            )

    async def _parse_event_data(
        self, event: AnomalyDetectedEvent
    ) -> Tuple[Optional[AnomalyAlert], Optional[SensorReading]]:
        """Parses anomaly_details and triggering_data from the event."""
        parsed_alert: Optional[AnomalyAlert] = None
        parsed_reading: Optional[SensorReading] = None

        try:
            parsed_alert = parse_obj_as(AnomalyAlert, event.anomaly_details)
        except ValidationError as e:
            self.logger.error(
                f"[{event.correlation_id}] Error parsing AnomalyAlert from event.anomaly_details: {e}. Data: {event.anomaly_details}"
            )
            return None, None
        except Exception as e:
            self.logger.error(
                f"[{event.correlation_id}] Unexpected error parsing AnomalyAlert: {e}. Data: {event.anomaly_details}"
            )
            return None, None

        try:
            parsed_reading = parse_obj_as(SensorReading, event.triggering_data)
        except ValidationError as e:
            self.logger.error(
                f"[{event.correlation_id}] Error parsing SensorReading from event.triggering_data: {e}. Data: {event.triggering_data}"
            )
            return (
                None,
                None,
            )  # Or just return parsed_alert, None if alert parsing was successful
        except Exception as e:
            self.logger.error(
                f"[{event.correlation_id}] Unexpected error parsing SensorReading: {e}. Data: {event.triggering_data}"
            )
            return parsed_alert, None

        return parsed_alert, parsed_reading

    async def _perform_historical_context_validation(
        self, parsed_alert: AnomalyAlert, parsed_reading: SensorReading
    ) -> Tuple[float, List[str]]:
        """Performs historical context validation logic."""
        historical_confidence_adjustment = 0.0
        historical_reasons = []

        if not self.crud_sensor_reading:
            historical_reasons.append(
                "Historical context skipped: CRUDSensorReading not available."
            )
            return historical_confidence_adjustment, historical_reasons

        try:
            historical_readings = (
                await self.crud_sensor_reading.get_sensor_readings_by_sensor_id(
                    sensor_id=parsed_alert.sensor_id,
                    limit=self.historical_check_limit,
                    before_timestamp=parsed_reading.timestamp,
                )
            )
        except Exception as e:
            self.logger.error(
                f"[{parsed_alert.sensor_id}] Error fetching historical readings: {e}"
            )
            historical_reasons.append(f"Failed to fetch historical readings: {e}")
            return historical_confidence_adjustment, historical_reasons

        if not historical_readings:
            historical_reasons.append("No historical readings found for context.")
            return historical_confidence_adjustment, historical_reasons

        # 1. Recent Value Stability
        if (
            parsed_alert.anomaly_type in ["spike", "statistical_threshold_breach"]
            and len(historical_readings) >= self.recent_stability_window
        ):

            recent_values = [
                r.value
                for r in historical_readings[: self.recent_stability_window]
                if isinstance(r.value, (int, float))
            ]
            if (
                len(recent_values) >= self.recent_stability_window - 1
            ):  # Allow for one missing/non-numeric
                try:
                    mean_recent_value = statistics.mean(recent_values)
                    if isinstance(parsed_reading.value, (int, float)) and abs(
                        parsed_reading.value - mean_recent_value
                    ) < (
                        self.recent_stability_factor * abs(mean_recent_value)
                        if mean_recent_value != 0
                        else self.recent_stability_factor
                    ):
                        adjustment = -0.1
                        historical_confidence_adjustment += adjustment
                        historical_reasons.append(
                            f"Recent value stability: Reading {parsed_reading.value} is close to recent mean {mean_recent_value:.2f}. Adjusted by {adjustment}."
                        )
                except statistics.StatisticsError:
                    self.logger.warning(
                        f"[{parsed_alert.sensor_id}] Could not calculate mean for recent stability check for values: {recent_values}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"[{parsed_alert.sensor_id}] Error in recent value stability check: {e}"
                    )

        # 2. Recurring Anomaly Type (Simplified)
        # Check if a significant number of historical readings are themselves "anomalous"
        # compared to *their* preceding values.
        if len(historical_readings) > 1:  # Need at least two readings to compare
            anomalous_historical_count = 0
            # Iterate from the second oldest up to the most recent historical reading
            for i in range(len(historical_readings) - 1, 0, -1):
                current_hist_reading = historical_readings[
                    i - 1
                ]  # More recent in this pair
                previous_hist_reading = historical_readings[i]  # Older in this pair

                if (
                    isinstance(current_hist_reading.value, (int, float))
                    and isinstance(previous_hist_reading.value, (int, float))
                    and previous_hist_reading.value != 0
                ):  # Avoid division by zero

                    if (
                        abs(current_hist_reading.value - previous_hist_reading.value)
                        / abs(previous_hist_reading.value)
                        > self.recurring_anomaly_diff_factor
                    ):
                        anomalous_historical_count += 1

            if (
                anomalous_historical_count / len(historical_readings)
                > self.recurring_anomaly_threshold_pct
            ):
                adjustment = -0.05
                historical_confidence_adjustment += adjustment
                historical_reasons.append(
                    f"Recurring anomaly pattern: {anomalous_historical_count}/{len(historical_readings)} historical points showed significant deviation. Adjusted by {adjustment}."
                )

        return historical_confidence_adjustment, historical_reasons

    async def process(self, event: AnomalyDetectedEvent) -> None:
        """Processes an AnomalyDetectedEvent to validate the anomaly."""
        correlation_id = (
            event.correlation_id or event.event_id
        )  # Use event_id if correlation_id is missing
        self.logger.info(
            f"[{correlation_id}] Received {event.event_type}: {event.event_id}. Source: {event.source_system}"
        )

        try:
            parsed_alert, parsed_reading = await self._parse_event_data(event)
            if not parsed_alert or not parsed_reading:
                # Errors already logged in _parse_event_data
                self.logger.error(
                    f"[{correlation_id}] Aborting processing due to parsing errors."
                )
                return

            # 1. Rule-based validation
            rule_adjustment, rule_reasons = await self.rule_engine.evaluate_rules(
                parsed_alert, parsed_reading
            )
            self.logger.info(
                f"[{correlation_id}] Rule engine adjustment: {rule_adjustment}, Reasons: {rule_reasons}"
            )

            # 2. Historical Context Validation
            historical_adjustment, historical_reasons = (
                await self._perform_historical_context_validation(
                    parsed_alert, parsed_reading
                )
            )
            self.logger.info(
                f"[{correlation_id}] Historical context adjustment: {historical_adjustment}, Reasons: {historical_reasons}"
            )

            # 3. Bayesian Validation Placeholder
            self.logger.info(
                f"[{correlation_id}] Bayesian validation step is a placeholder."
            )
            bayesian_adjustment = 0.0
            bayesian_reasons = ["Bayesian validation placeholder - no adjustment."]

            # 4. Final Confidence & Status
            final_confidence = (
                parsed_alert.confidence
                + rule_adjustment
                + historical_adjustment
                + bayesian_adjustment
            )
            final_confidence = max(
                0.0, min(1.0, final_confidence)
            )  # Clamp between 0.0 and 1.0

            validation_status: str
            if final_confidence >= self.credible_threshold:
                validation_status = "CONFIRMED_CREDIBLE"
            elif final_confidence < self.false_positive_threshold:
                validation_status = "POTENTIAL_FALSE_POSITIVE"
            else:
                validation_status = "UNCERTAIN"

            all_validation_reasons = (
                rule_reasons + historical_reasons + bayesian_reasons
            )

            self.logger.info(
                f"[{correlation_id}] Original Confidence: {parsed_alert.confidence:.2f}, "
                f"Rule Adj: {rule_adjustment:.2f}, Hist Adj: {historical_adjustment:.2f}, Bayes Adj: {bayesian_adjustment:.2f}. "
                f"Final Confidence: {final_confidence:.2f}. Status: {validation_status}"
            )

            # 5. Event Publishing
            validated_event = AnomalyValidatedEvent(
                # BaseEventModel fields (event_id, created_at are auto-generated)
                event_type="AnomalyValidated",  # This is also set by default in AnomalyValidatedEvent
                original_anomaly_alert_payload=event.anomaly_details,  # Original dict
                triggering_reading_payload=event.triggering_data,  # Original dict
                validation_status=validation_status,
                final_confidence=final_confidence,
                validation_reasons=all_validation_reasons,
                # validated_at is auto-generated by AnomalyValidatedEvent
                agent_id=self.agent_id,
                correlation_id=correlation_id,
            )

            await self.publish_event(validated_event)
            self.logger.info(
                f"[{correlation_id}] Published {validated_event.event_type} for original alert on sensor {parsed_alert.sensor_id}."
            )

        except Exception as e:
            self.logger.error(
                f"[{correlation_id}] Unhandled error in ValidationAgent.process: {e}",
                exc_info=True,
            )
            # Potentially publish an error event or implement retry logic if applicable


# Example of how to run (for testing purposes, actual setup would be different)
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Mock Event Bus (use the one from base_agent or a more sophisticated one)
    class MockEventBus:
        def __init__(self):
            self.subscriptions: Dict[str, List[Callable]] = (
                {}
            )  # Callable is now imported
            self.published_events: List[Any] = []  # Any is now imported

        async def subscribe(
            self, event_type: str, handler: Callable
        ):  # Callable is now imported
            if event_type not in self.subscriptions:
                self.subscriptions[event_type] = []
            self.subscriptions[event_type].append(handler)
            logger.info(f"MockEventBus: Handler subscribed to {event_type}")

        async def publish(self, event: BaseEventModel):
            self.published_events.append(event)
            logger.info(
                f"MockEventBus: Published event {event.event_type} (ID: {event.event_id}, CorrID: {getattr(event, 'correlation_id', 'N/A')})"
            )
            event_type_name = event.__class__.__name__
            if event_type_name in self.subscriptions:
                for handler in self.subscriptions[event_type_name]:
                    asyncio.create_task(handler(event))  # Run handler

        def get_published_events_by_type(
            self, event_type_name: str
        ) -> List[Any]:  # Any is now imported
            return [
                e
                for e in self.published_events
                if e.__class__.__name__ == event_type_name
            ]

    async def test_validation_agent():
        logger.info("--- Setting up Validation Agent Test ---")
        mock_bus = MockEventBus()
        mock_crud_sensor_reading = CRUDSensorReading()  # Uses dummy data
        mock_rule_engine = RuleEngine()

        # Initialize agent
        validation_agent = ValidationAgent(
            agent_id="validator_001",
            event_bus=mock_bus,
            crud_sensor_reading=mock_crud_sensor_reading,
            rule_engine=mock_rule_engine,
            specific_settings={
                "credible_threshold": 0.65,
                "false_positive_threshold": 0.35,
            },
        )
        await validation_agent.start()  # Subscribes to AnomalyDetectedEvent

        # --- Test Case 1: Credible Anomaly ---
        logger.info("\n--- Test Case 1: Credible Anomaly ---")
        alert_details_1 = {
            "sensor_id": "temp_sensor_001",
            "anomaly_type": "spike",
            "severity": 5,
            "confidence": 0.8,
            "description": "High spike",
            "timestamp": datetime.utcnow().isoformat(),
        }
        # Ensure triggering data matches a recent reading from dummy data for better historical context
        # Let's pick a timestamp around 2 hours ago from CRUDSensorReading's dummy data
        trigger_ts_1 = datetime.utcnow() - timedelta(hours=2)
        triggering_data_1 = {
            "sensor_id": "temp_sensor_001",
            "timestamp": trigger_ts_1.isoformat(),
            "value": 60,
            "sensor_type": "TEMPERATURE",
            "unit": "°C",
            "quality": 0.95,
        }
        # Add this specific reading to CRUD so historical context can find it if needed as 'current'
        # await mock_crud_sensor_reading.add_sensor_reading(SensorReading(**triggering_data_1))

        detected_event_1 = AnomalyDetectedEvent(
            anomaly_details=alert_details_1,
            triggering_data=triggering_data_1,
            source_system="TestSystem1",
            correlation_id="test_corr_001",
        )
        await mock_bus.publish(detected_event_1)
        await asyncio.sleep(0.2)  # Allow event processing

        # --- Test Case 2: Potential False Positive (low quality, low initial confidence) ---
        logger.info("\n--- Test Case 2: Potential False Positive ---")
        alert_details_2 = {
            "sensor_id": "pressure_sensor_002",
            "anomaly_type": "statistical_threshold_breach",
            "severity": 2,
            "confidence": 0.25,
            "description": "Slight pressure drop",
            "timestamp": datetime.utcnow().isoformat(),
        }
        trigger_ts_2 = datetime.utcnow() - timedelta(minutes=10)
        triggering_data_2 = {
            "sensor_id": "pressure_sensor_002",
            "timestamp": trigger_ts_2.isoformat(),
            "value": 980,
            "sensor_type": "PRESSURE",
            "unit": "PSI",
            "quality": 0.5,  # Poor quality
        }
        detected_event_2 = AnomalyDetectedEvent(
            anomaly_details=alert_details_2,
            triggering_data=triggering_data_2,
            source_system="TestSystem2",
            correlation_id="test_corr_002",
        )
        await mock_bus.publish(detected_event_2)
        await asyncio.sleep(0.2)

        # --- Test Case 3: Historical context makes it uncertain ---
        # (e.g. value is stable with recent past, recurring anomaly pattern)
        logger.info("\n--- Test Case 3: Historical Context Influence ---")
        # Use temp_sensor_001, it has more varied dummy data
        # Find a reading from dummy data that is "anomalous" (e.g. value 22.5 for temp_sensor_001)
        # This is 15 + (0/10)*(30-15) = 15; 15 + (1/10)*15 = 16.5 ... 15 + (5/10)*15 = 22.5 (i=5)
        # Anomaly: 22.5 * 1.5 = 33.75 (i=20, 40, 60, 80)
        # Let's make current reading value close to mean of last 5 non-anomalous readings
        # Example: last 5 readings for temp_sensor_001 (before now - timedelta(hours=3)) might be around 15-25
        # Let's assume mean is 20. Current reading is 20.5.
        trigger_ts_3 = datetime.utcnow() - timedelta(
            hours=3, minutes=30
        )  # A time for the triggering reading
        alert_details_3 = {
            "sensor_id": "temp_sensor_001",
            "anomaly_type": "spike",
            "severity": 4,
            "confidence": 0.75,  # Initially high confidence
            "description": "Temperature spike that might be normal fluctuation",
            "timestamp": trigger_ts_3.isoformat(),
        }
        triggering_data_3 = (
            {  # This reading should be close to the mean of readings before it
                "sensor_id": "temp_sensor_001",
                "timestamp": trigger_ts_3.isoformat(),
                "value": 20.5,
                "sensor_type": "TEMPERATURE",
                "unit": "°C",
                "quality": 0.9,
            }
        )
        # Need to ensure CRUDSensorReading has appropriate data for this test case
        # The dummy data in CRUDSensorReading is generated based on `now` when it's instantiated.
        # For "Recent Value Stability", the current `parsed_reading.value` (20.5) should be close to
        # the mean of the 5 readings immediately preceding `trigger_ts_3`.
        # The dummy data populates hourly. So readings before trigger_ts_3 would be at:
        # T-4h, T-5h, T-6h, T-7h, T-8h.
        # Values: (now-4h) -> i=4 -> 15 + (4%10)/10 * 15 = 15 + 0.4*15 = 21
        # (now-5h) -> i=5 -> 15 + (5%10)/10 * 15 = 15 + 0.5*15 = 22.5
        # (now-6h) -> i=6 -> 15 + (6%10)/10 * 15 = 15 + 0.6*15 = 24
        # (now-7h) -> i=7 -> 15 + (7%10)/10 * 15 = 15 + 0.7*15 = 25.5
        # (now-8h) -> i=8 -> 15 + (8%10)/10 * 15 = 15 + 0.8*15 = 27
        # Mean = (21+22.5+24+25.5+27)/5 = 120/5 = 24.
        # Our value 20.5 is somewhat close to 24. (24*0.05 = 1.2). |20.5-24| = 3.5. So this might not trigger stability.
        # Let's set value to 23.5. Then |23.5-24| = 0.5, which is < 1.2. This should trigger.
        triggering_data_3["value"] = 23.5

        detected_event_3 = AnomalyDetectedEvent(
            anomaly_details=alert_details_3,
            triggering_data=triggering_data_3,
            source_system="TestSystem3",
            correlation_id="test_corr_003",
        )
        await mock_bus.publish(detected_event_3)
        await asyncio.sleep(0.2)

        # Check published events
        validated_events = mock_bus.get_published_events_by_type(
            "AnomalyValidatedEvent"
        )
        logger.info(f"\n--- Summary of Validated Events ({len(validated_events)}) ---")
        for ve in validated_events:
            logger.info(
                f"  CorrID: {ve.correlation_id}, Sensor: {ve.original_anomaly_alert_payload.get('sensor_id')}, "
                f"OriginalConf: {ve.original_anomaly_alert_payload.get('confidence'):.2f}, "
                f"FinalConf: {ve.final_confidence:.2f}, Status: {ve.validation_status}"
            )
            # logger.debug(f"   Reasons: {ve.validation_reasons}")

        await validation_agent.stop()
        logger.info("--- Validation Agent Test Finished ---")

    if __name__ == "__main__":
        asyncio.run(test_validation_agent())
