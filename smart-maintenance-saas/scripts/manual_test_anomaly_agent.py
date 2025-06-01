import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, List, Dict, Optional

from apps.agents.core.anomaly_detection_agent import AnomalyDetectionAgent
from core.events.event_bus import EventBus
from core.events.event_models import AnomalyDetectedEvent, DataProcessedEvent, BaseEventModel
from data.schemas import SensorReading, SensorType # Assuming SensorType is in data.schemas

# --- Globals to capture events and simplify testing ---
CAPTURED_ANOMALY_EVENTS: List[AnomalyDetectedEvent] = []
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# --- Logging Setup ---
def setup_logging():
    """Configures logging for the test script."""
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    # Set specific loggers to DEBUG if more detail is needed
    logging.getLogger("apps.agents.core.anomaly_detection_agent").setLevel(logging.DEBUG)
    logging.getLogger("apps.ml.statistical_models").setLevel(logging.DEBUG)
    logging.getLogger("core.events.event_bus").setLevel(logging.INFO) # Keep INFO for event bus unless debugging it
    # If you want to see BaseAgent logs too:
    # logging.getLogger("apps.agents.base_agent").setLevel(logging.DEBUG)

# --- Event Capturing Handler ---
async def anomaly_event_handler(event: AnomalyDetectedEvent):
    """Handles AnomalyDetectedEvent and stores it."""
    logging.info(f"--- CAPTURED AnomalyDetectedEvent: ID={event.event_id}, Sensor={event.anomaly_details.get('sensor_id')}, Type={event.anomaly_details.get('anomaly_type')}, Sev={event.severity}, Conf={event.anomaly_details.get('confidence'):.4f}, CorrID={event.correlation_id} ---")
    CAPTURED_ANOMALY_EVENTS.append(event)

# --- Test Runner Helper ---
async def run_test_scenario(
    agent: AnomalyDetectionAgent,
    event_bus: EventBus,
    # Params for normal SensorReading construction
    sensor_id: Optional[str] = None,
    value: Optional[float] = None,
    sensor_type: SensorType = SensorType.TEMPERATURE,
    unit: str = "celsius",
    quality: float = 1.0,
    metadata: Optional[Dict[str, Any]] = None,
    # Params for event itself or overriding processed_data
    correlation_id: Optional[str] = None, # For DataProcessedEvent.correlation_id
    processed_data_override: Optional[Dict[str, Any]] = None, # Directly sets DataProcessedEvent.processed_data
    is_malformed_payload_test: bool = False # Flag to indicate if we are testing malformed processed_data
):
    """Helper to create, publish, and process a DataProcessedEvent."""
    event_timestamp = datetime.now(timezone.utc)
    # test_correlation_id is for the DataProcessedEvent, for passthrough testing
    event_correlation_id = correlation_id or str(uuid.uuid4())

    actual_processed_data: Any
    # Determine display_sensor_id for logging before it might be deleted or be absent
    if is_malformed_payload_test and isinstance(processed_data_override, dict):
        display_sensor_id_for_log = processed_data_override.get('sensor_id', 'N/A_Malformed_DictKeyMissing')
    elif is_malformed_payload_test: # Not a dict
        display_sensor_id_for_log = 'N/A_Malformed_NotDict'
    else: # Normal case
        display_sensor_id_for_log = sensor_id

    display_value_for_log = value # Will be None if not a normal test, or overridden by N/A

    if is_malformed_payload_test:
        actual_processed_data = processed_data_override # This is the direct payload for DataProcessedEvent.processed_data
        display_value_for_log = "N/A_Malformed"
    else:
        # Standard path: construct a valid SensorReading
        reading_payload_for_model = {
            "sensor_id": sensor_id,
            "value": value,
            "timestamp": event_timestamp,
            "sensor_type": sensor_type,
            "unit": unit,
            "quality": quality,
            "metadata": metadata or {}
            # SensorReading.correlation_id will use its default_factory
        }
        reading = SensorReading(**reading_payload_for_model)
        actual_processed_data = reading.model_dump()
        # display_sensor_id_for_log is already set from sensor_id
        # display_value_for_log is already set from value

    processed_event = DataProcessedEvent(
        processed_data=actual_processed_data,
        original_event_id=uuid.uuid4(),
        source_sensor_id=str(display_sensor_id_for_log) if display_sensor_id_for_log is not None else "unknown_malformed_source",
        correlation_id=event_correlation_id
    )

    logging.info(f"--- PUBLISHING DataProcessedEvent for Sensor ID: {display_sensor_id_for_log}, Value: {display_value_for_log}, CorrID: {event_correlation_id} ---")
    await event_bus.publish(processed_event)
    await asyncio.sleep(0.2)


async def main():
    setup_logging()
    event_bus = EventBus()

    # Subscribe the capturer
    await event_bus.subscribe(AnomalyDetectedEvent.__name__, anomaly_event_handler)

    # Initialize Agent
    # For specific tests, we might re-initialize or modify the agent's properties
    # Default initialization for now
    specific_agent_settings = {
        'isolation_forest_params': {'random_state': 42}, # Consistent IF behavior
        'statistical_detector_config': {'threshold_std_dev': 3.0} # Default
    }
    agent = AnomalyDetectionAgent(
        agent_id="manual_test_anomaly_agent",
        event_bus=event_bus,
        specific_settings=specific_agent_settings
    )
    await agent.start() # Subscribes to DataProcessedEvent

    logging.info("\n\n--- SCENARIO 1: Normal Data (Known Sensor) ---")
    CAPTURED_ANOMALY_EVENTS.clear()
    # Sensor ID: sensor_temp_001 (mean: 22.5, std: 2.1) -> 3*std = 6.3. Normal range approx [16.2, 28.8]
    # Value: 23.0 (should be normal)
    await run_test_scenario(agent, event_bus, sensor_id="sensor_temp_001", value=23.0)
    if not CAPTURED_ANOMALY_EVENTS:
        logging.info("SCENARIO 1: PASSED - No anomaly event published, as expected.")
    else:
        logging.error(f"SCENARIO 1: FAILED - Anomaly event published for normal data: {CAPTURED_ANOMALY_EVENTS}")

    logging.info("\n\n--- SCENARIO 2: Clear Statistical Anomaly (Known Sensor - High Value) ---")
    CAPTURED_ANOMALY_EVENTS.clear()
    corr_id_scenario2 = "corr_id_scenario_2"
    # Value: 40.0 (significantly above 28.8)
    await run_test_scenario(agent, event_bus, sensor_id="sensor_temp_001", value=40.0, correlation_id=corr_id_scenario2)
    if CAPTURED_ANOMALY_EVENTS and CAPTURED_ANOMALY_EVENTS[0].correlation_id == corr_id_scenario2:
        logging.info(f"SCENARIO 2: PASSED - Anomaly event published with correct correlation ID.")
    elif CAPTURED_ANOMALY_EVENTS:
        logging.error(f"SCENARIO 2: FAILED - Anomaly event published but WRONG correlation ID: {CAPTURED_ANOMALY_EVENTS[0].correlation_id}, expected {corr_id_scenario2}")
    else:
        logging.error(f"SCENARIO 2: FAILED - No anomaly event published for clear high anomaly.")

    logging.info("\n\n--- SCENARIO 3: Clear Statistical Anomaly (Known Sensor - Low Value) ---")
    CAPTURED_ANOMALY_EVENTS.clear()
    corr_id_scenario3 = "corr_id_scenario_3"
    # Sensor ID: sensor_press_001 (mean: 101.3, std: 0.8) -> 3*std = 2.4. Normal range approx [98.9, 103.7]
    # Value: 95.0 (significantly below 98.9)
    await run_test_scenario(agent, event_bus, sensor_id="sensor_press_001", value=95.0, sensor_type=SensorType.PRESSURE, unit="kPa", correlation_id=corr_id_scenario3)
    if CAPTURED_ANOMALY_EVENTS and CAPTURED_ANOMALY_EVENTS[0].correlation_id == corr_id_scenario3:
        logging.info(f"SCENARIO 3: PASSED - Anomaly event published with correct correlation ID.")
    elif CAPTURED_ANOMALY_EVENTS:
        logging.error(f"SCENARIO 3: FAILED - Anomaly event published but WRONG correlation ID: {CAPTURED_ANOMALY_EVENTS[0].correlation_id}, expected {corr_id_scenario3}")
    else:
        logging.error(f"SCENARIO 3: FAILED - No anomaly event published for clear low anomaly.")

    logging.info("\n\n--- SCENARIO 4: Isolation Forest Fitting & First Data Point ---")
    CAPTURED_ANOMALY_EVENTS.clear()
    new_sensor_if = "sensor_new_if_001"
    # Ensure IF is not fitted for this sensor yet by re-init or using a truly new agent
    # For simplicity, we assume the agent's IF model is fresh or handles new sensors appropriately.
    # The agent's current IF logic fits on the first point it sees if not already fitted globally.
    logging.info("SCENARIO 4: Value 1 (10.0) - Expect IF fitting log")
    agent.isolation_forest_fitted = False # Resetting for test - normally IF fits once globally.
    await run_test_scenario(agent, event_bus, sensor_id=new_sensor_if, value=10.0)

    logging.info("SCENARIO 4: Value 2 (11.0) - Expect IF NOT re-fitting")
    await run_test_scenario(agent, event_bus, sensor_id=new_sensor_if, value=11.0)
    # Visual inspection of logs needed for "Fitting Isolation Forest model" and its absence on 2nd call.

    logging.info("\n\n--- SCENARIO 5: Unknown Sensor Behavior (Statistical Model Fallback) ---")
    CAPTURED_ANOMALY_EVENTS.clear()
    unknown_sensor_stat = "sensor_unknown_stat_002"
    # Value 1: 100.0 (should be normal by fallback logic)
    logging.info("SCENARIO 5: Value 1 (100.0) - Expect normal, fallback to default_historical_std")
    await run_test_scenario(agent, event_bus, sensor_id=unknown_sensor_stat, value=100.0)
    if not CAPTURED_ANOMALY_EVENTS:
        logging.info("SCENARIO 5.1: PASSED - No anomaly for first unknown sensor value.")
    else:
        logging.error(f"SCENARIO 5.1: FAILED - Anomaly event for first unknown value: {CAPTURED_ANOMALY_EVENTS}")

    CAPTURED_ANOMALY_EVENTS.clear()
    # Value 2: 100.2 (should be anomaly if default_historical_std=0.1 and mean became 100.0)
    # The agent's current logic for unknown sensors uses reading.value as mean for that first point.
    # The default_historical_std is 0.1. 3 * 0.1 = 0.3. Range becomes [99.7, 100.3] around 100.0
    # So 100.2 should be normal. 100.31 would be an anomaly.
    logging.info("SCENARIO 5: Value 2 (100.2) - Expect normal with default_historical_std=0.1")
    await run_test_scenario(agent, event_bus, sensor_id=unknown_sensor_stat, value=100.2)
    if not CAPTURED_ANOMALY_EVENTS:
        logging.info("SCENARIO 5.2: PASSED - No anomaly for second unknown sensor value (100.2).")
    else:
        logging.error(f"SCENARIO 5.2: FAILED - Anomaly event for 100.2: {CAPTURED_ANOMALY_EVENTS}")

    CAPTURED_ANOMALY_EVENTS.clear()
    logging.info("SCENARIO 5: Value 3 (100.31) - Expect anomaly with default_historical_std=0.1")
    await run_test_scenario(agent, event_bus, sensor_id=unknown_sensor_stat, value=100.31)
    if CAPTURED_ANOMALY_EVENTS:
        logging.info(f"SCENARIO 5.3: PASSED - Anomaly detected for 100.31: {CAPTURED_ANOMALY_EVENTS[0].anomaly_details['confidence']:.4f}")
    else:
        logging.error(f"SCENARIO 5.3: FAILED - No anomaly for 100.31.")


    logging.info("\n\n--- SCENARIO 6: Malformed DataProcessedEvent ---")
    # 6a: Missing 'value'
    logging.info("SCENARIO 6a: Malformed - missing 'value'")
    malformed_data_6a = {'sensor_id': 'test_malformed_1', 'timestamp': datetime.now(timezone.utc).isoformat(), 'sensor_type': SensorType.TEMPERATURE.value, 'unit': 'C'}
    await run_test_scenario(agent, event_bus, processed_data_override=malformed_data_6a, is_malformed_payload_test=True, sensor_id='logs_for_test_malformed_1')
    # Expect Pydantic validation error in logs.

    # 6b: processed_data is not a dict
    logging.info("SCENARIO 6b: Malformed - processed_data is not a dict")
    await run_test_scenario(agent, event_bus, processed_data_override="not_a_dict", is_malformed_payload_test=True, sensor_id='logs_for_test_malformed_b')
    # Expect "processed_data must be a dictionary" error in logs.

    # 6c: sensor_id is empty
    logging.info("SCENARIO 6c: Malformed - empty sensor_id")
    malformed_data_6c = {'sensor_id': '', 'value': 10.0, 'timestamp': datetime.now(timezone.utc).isoformat(), 'sensor_type': SensorType.TEMPERATURE.value, 'unit': 'C'}
    await run_test_scenario(agent, event_bus, processed_data_override=malformed_data_6c, is_malformed_payload_test=True, sensor_id='logs_for_test_malformed_c_empty')
    # Expect "_validate_sensor_reading" error in logs.

    # 6d: value is non-numeric
    logging.info("SCENARIO 6d.1: Malformed - non-numeric value")
    malformed_data_6d1 = {'sensor_id': 'test_malformed_d1', 'value': 'not-a-number', 'timestamp': datetime.now(timezone.utc).isoformat(), 'sensor_type': SensorType.TEMPERATURE.value, 'unit': 'C'}
    await run_test_scenario(agent, event_bus, processed_data_override=malformed_data_6d1, is_malformed_payload_test=True, sensor_id='logs_for_test_malformed_d1')
    # Expect Pydantic validation error.

    # 6d: value is non-finite (nan)
    logging.info("SCENARIO 6d.2: Malformed - non-finite value (nan)")
    malformed_data_6d2 = {'sensor_id': 'test_malformed_d2', 'value': float('nan'), 'timestamp': datetime.now(timezone.utc).isoformat(), 'sensor_type': SensorType.TEMPERATURE.value, 'unit': 'C'}
    await run_test_scenario(agent, event_bus, processed_data_override=malformed_data_6d2, is_malformed_payload_test=True, sensor_id='logs_for_test_malformed_d2')
    # Expect "_validate_sensor_reading" error for non-finite value.

    logging.info("\n\n--- SCENARIO 7: Statistical Model - Zero Standard Deviation ---")
    # Temporarily modify historical data for this test. This is intrusive.
    # A better way would be to allow injecting historical data config into the agent or using a specific agent config.
    original_hist_data = agent.historical_data_store.copy()
    agent.historical_data_store["sensor_zero_std_001"] = {"mean": 50.0, "std": 0.0}

    CAPTURED_ANOMALY_EVENTS.clear()
    logging.info("SCENARIO 7: Value 1 (50.0) - matches mean, std=0")
    await run_test_scenario(agent, event_bus, sensor_id="sensor_zero_std_001", value=50.0)
    if not CAPTURED_ANOMALY_EVENTS:
        logging.info("SCENARIO 7.1: PASSED - No anomaly for value matching mean with zero std.")
    else:
        logging.error(f"SCENARIO 7.1: FAILED - Anomaly event for zero std, matching mean: {CAPTURED_ANOMALY_EVENTS}")

    CAPTURED_ANOMALY_EVENTS.clear()
    logging.info("SCENARIO 7: Value 2 (50.1) - differs from mean, std=0")
    await run_test_scenario(agent, event_bus, sensor_id="sensor_zero_std_001", value=50.1)
    if CAPTURED_ANOMALY_EVENTS and CAPTURED_ANOMALY_EVENTS[0].anomaly_details.get('anomaly_type') == "statistical_statistical_threshold_breach_zero_std":
        logging.info("SCENARIO 7.2: PASSED - Anomaly detected with correct type for zero std, differing value.")
        assert math.isclose(CAPTURED_ANOMALY_EVENTS[0].anomaly_details.get('confidence'), 0.8), f"Confidence should be 0.8, was {CAPTURED_ANOMALY_EVENTS[0].anomaly_details.get('confidence')}"
    else:
        logging.error(f"SCENARIO 7.2: FAILED or wrong type for zero std, differing value. Events: {CAPTURED_ANOMALY_EVENTS}")

    agent.historical_data_store = original_hist_data # Restore

    logging.info("\n\n--- SCENARIO 8: Event Publishing (Observe Logs) ---")
    # This scenario relies on visual inspection of logs from previous successful anomaly publications (e.g., Scenario 2, 3, 5.3, 7.2)
    # Look for: "Publishing AnomalyDetectedEvent (attempt 1): ..."
    # And: "Successfully published AnomalyDetectedEvent: ..."
    # This confirms the basic success path of publishing. Retry logic is harder to test here.
    logging.info("SCENARIO 8: Check logs from previous scenarios for successful publish messages.")


    await agent.stop()
    logging.info("Manual testing script finished.")

if __name__ == "__main__":
    asyncio.run(main())
