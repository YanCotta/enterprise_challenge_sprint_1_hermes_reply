import pytest
from datetime import datetime, timezone
import uuid

from apps.rules.validation_rules import RuleEngine
from data.schemas import AnomalyAlert, SensorReading, SensorType, AnomalyType, AnomalyStatus # Added AnomalyType and AnomalyStatus


@pytest.fixture
def anomaly_alert_factory():
    def _factory(
        confidence: float,
        created_at: datetime = None,
        description: str = "Test Alert",
        anomaly_type: AnomalyType = AnomalyType.UNKNOWN, # Changed to use Enum and a default
        severity: int = 3, # Added default
        sensor_id: str = None, # Added sensor_id
        evidence: dict = None, # Added evidence
        recommended_actions: list = None, # Added recommended_actions
        status: AnomalyStatus = AnomalyStatus.OPEN # Changed to use enum
    ) -> AnomalyAlert:
        return AnomalyAlert(
            id=uuid.uuid4(),
            sensor_id=sensor_id or str(uuid.uuid4()), # Use provided or generate
            created_at=created_at or datetime.now(timezone.utc),
            description=description,
            confidence=confidence,
            anomaly_type=anomaly_type,
            severity=severity,
            evidence=evidence or {},
            recommended_actions=recommended_actions or [],
            status=status,
        )
    return _factory

@pytest.fixture
def sensor_reading_factory():
    def _factory(
        quality: float = 1.0,  # Default to good quality (float)
        sensor_type: SensorType = SensorType.TEMPERATURE,
        value: float = 25.0,
        timestamp: datetime = None
    ) -> SensorReading:
        # The SensorReading model expects a string for sensor_id in its base SensorReadingCreate
        # and sensor_type as an enum, which is correct.
        # The 'quality' field in SensorReading is a float.
        return SensorReading(
            sensor_id=str(uuid.uuid4()), # Ensure sensor_id is a string
            timestamp=timestamp or datetime.now(timezone.utc),
            sensor_type=sensor_type,
            value=value,
            quality=quality, # This is float as per SensorReading schema
            unit="N/A", # SensorReading requires 'unit', provide a default
            metadata={}
        )
    return _factory

@pytest.fixture
def rule_engine() -> RuleEngine:
    return RuleEngine()

@pytest.mark.asyncio
async def test_low_original_confidence_triggered(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test that the 'Low Original Confidence' rule is triggered when confidence < 0.3."""
    alert_confidence = 0.2
    # Ensure other rules that might affect adjustment are not triggered by default values
    alert = anomaly_alert_factory(confidence=alert_confidence, anomaly_type=AnomalyType.DRIFT) # Use Enum that won't trigger Rule 3
    reading = sensor_reading_factory() # Default reading is temperature 25C, quality 1.0

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    # Rule 1: -0.1
    # Rule 2 (Poor Data Quality) not triggered (quality=1.0)
    # Rule 3 (Temp/Spike/Low Value checks) not triggered (anomaly_type=DRIFT)
    assert -0.1 == pytest.approx(adjustment, abs=1e-9)
    expected_reason = f"Initial alert confidence ({alert.confidence:.2f}) is below threshold (0.3)."
    assert expected_reason in reasons

@pytest.mark.asyncio
async def test_low_original_confidence_not_triggered(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test that the 'Low Original Confidence' rule is NOT triggered when confidence >= 0.3."""
    alert_confidence = 0.4
    # Ensure other rules that might affect adjustment are not triggered by default values
    alert = anomaly_alert_factory(confidence=alert_confidence, anomaly_type=AnomalyType.DRIFT) # Use Enum
    reading = sensor_reading_factory() # Default reading is temperature 25C, quality 1.0

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    # Rule 1: Not triggered
    # Rule 2 (Poor Data Quality) not triggered (quality=1.0)
    # Rule 3 (Temp Spike Value Check) not triggered (anomaly_type="other_anomaly")
    # So, adjustment should be 0.0
    assert 0.0 == pytest.approx(adjustment, abs=1e-9)

    # The specific reason for low confidence should not be present.
    reason_if_low_confidence_triggered = f"Initial alert confidence ({alert.confidence:.2f}) is below threshold (0.3)."
    assert reason_if_low_confidence_triggered not in reasons


@pytest.mark.asyncio
async def test_poor_data_quality_triggered(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test that the 'Poor Data Quality' rule is triggered when reading.quality < 0.5."""
    # Ensure other rules are not triggered:
    # - Alert confidence >= 0.3 (e.g., 0.5)
    # - Anomaly type that doesn\'t trigger temperature rules (e.g., "other_type")
    alert = anomaly_alert_factory(confidence=0.5, anomaly_type=AnomalyType.UNKNOWN) # Use Enum
    
    # Trigger this rule
    reading_quality = 0.4
    reading = sensor_reading_factory(quality=reading_quality)

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    # Rule 1 (Low Original Confidence) not triggered.
    # Rule 2 (Poor Data Quality) triggered: -0.2
    # Rule 3 (Temp Spike/Low Value) not triggered.
    assert -0.2 == pytest.approx(adjustment, abs=1e-9)
    expected_reason = f"Triggering sensor reading quality ({reading.quality:.2f}) is low (below 0.5)."
    assert expected_reason in reasons

@pytest.mark.asyncio
async def test_poor_data_quality_not_triggered(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test that the 'Poor Data Quality' rule is NOT triggered when reading.quality >= 0.5."""
    # Ensure other rules are not triggered:
    alert = anomaly_alert_factory(confidence=0.5, anomaly_type=AnomalyType.UNKNOWN) # Use Enum
    
    # Do not trigger this rule
    reading_quality = 0.6
    reading = sensor_reading_factory(quality=reading_quality)

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    # Rule 1 (Low Original Confidence) not triggered.
    # Rule 2 (Poor Data Quality) not triggered.
    # Rule 3 (Temp Spike/Low Value) not triggered.
    # So, adjustment should be 0.0
    assert 0.0 == pytest.approx(adjustment, abs=1e-9)
    
    reason_not_expected = f"Triggering sensor reading quality ({reading.quality:.2f}) is low (below 0.5)."
    # We need to format the reason with the actual quality (0.60) to check it's not present
    specific_reason_if_triggered = f"Triggering sensor reading quality (0.60) is low (below 0.5)."
    assert specific_reason_if_triggered not in reasons


# Tests for Rule 3: Value vs. Type-Specific Broad Threshold Check (Temperature/Spike part)

@pytest.mark.asyncio
async def test_temp_spike_value_below_threshold_triggered(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test Rule 3: Temp spike, value < 40°C, rule IS triggered."""
    alert = anomaly_alert_factory(confidence=0.5, anomaly_type=AnomalyType.SPIKE) # Use Enum
    reading_value = 35.0
    reading = sensor_reading_factory(
        quality=0.8, sensor_type=SensorType.TEMPERATURE, value=reading_value
    )

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    # Rule 1 (Low Confidence) not triggered (confidence=0.5)
    # Rule 2 (Poor Quality) not triggered (quality=0.8)
    # Rule 3 (Temp Spike < 40C) IS triggered: -0.05
    assert -0.05 == pytest.approx(adjustment, abs=1e-9)
    expected_reason = (
        f"Temperature spike alert ({alert.anomaly_type}) for a value ({reading.value}°C) "
        f"that is not considered extremely high (< 40°C)."
    )
    assert expected_reason in reasons

@pytest.mark.asyncio
async def test_temp_spike_value_above_threshold_not_triggered(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test Rule 3: Temp spike, value >= 40°C, rule NOT triggered."""
    alert = anomaly_alert_factory(confidence=0.5, anomaly_type=AnomalyType.SPIKE) # Use Enum
    reading_value = 45.0
    reading = sensor_reading_factory(
        quality=0.8, sensor_type=SensorType.TEMPERATURE, value=reading_value
    )

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    # All rules should not be triggered
    assert 0.0 == pytest.approx(adjustment, abs=1e-9)
    reason_not_expected = (
        f"Temperature spike alert ({alert.anomaly_type}) for a value ({reading.value}°C) "
        f"that is not considered extremely high (< 40°C)."
    )
    assert reason_not_expected not in reasons


# Tests for Rule 3: Value vs. Type-Specific Broad Threshold Check (Temperature/Low Value part)

@pytest.mark.asyncio
async def test_temp_low_value_above_threshold_triggered(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test Rule 3: Temp low_value, value > 0°C, rule IS triggered."""
    alert = anomaly_alert_factory(confidence=0.5, anomaly_type=AnomalyType.LOW_VALUE)
    reading_value = 5.0
    reading = sensor_reading_factory(
        quality=0.8, sensor_type=SensorType.TEMPERATURE, value=reading_value
    )

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    # Rule 1 (Low Confidence) not triggered
    # Rule 2 (Poor Quality) not triggered
    # Rule 3 (Temp Spike) not triggered
    # Rule 3 (Temp Low Value > 0C) IS triggered: -0.05
    assert -0.05 == pytest.approx(adjustment, abs=1e-9)
    expected_reason = (
        f"Temperature low_value alert ({alert.anomaly_type}) for a value ({reading.value}°C) "
        f"that is not critically low (> 0°C)."
    )
    assert expected_reason in reasons

@pytest.mark.asyncio
async def test_temp_low_value_below_threshold_not_triggered(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test Rule 3: Temp low_value, value <= 0°C, rule NOT triggered."""
    alert = anomaly_alert_factory(confidence=0.5, anomaly_type=AnomalyType.LOW_VALUE)
    reading_value = -5.0
    reading = sensor_reading_factory(
        quality=0.8, sensor_type=SensorType.TEMPERATURE, value=reading_value
    )

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    assert 0.0 == pytest.approx(adjustment, abs=1e-9)
    reason_not_expected = (
        f"Temperature low_value alert ({alert.anomaly_type}) for a value ({reading.value}°C) "
        f"that is not critically low (> 0°C)."
    )
    assert reason_not_expected not in reasons


# Tests for Rule Interactions

@pytest.mark.asyncio
async def test_interaction_no_rules_triggered(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test that no rules are triggered and adjustment is 0.0."""
    alert = anomaly_alert_factory(confidence=0.5, anomaly_type=AnomalyType.UNKNOWN)
    # Use a non-temperature sensor to avoid Rule 3, or set temp value outside Rule 3 trigger ranges
    reading = sensor_reading_factory(quality=0.8, sensor_type=SensorType.VIBRATION, value=30) 
    
    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    assert 0.0 == pytest.approx(adjustment, abs=1e-9)
    assert reasons == ["No rule-based adjustments applied."]

@pytest.mark.asyncio
async def test_interaction_only_low_confidence_triggered(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test only 'Low Original Confidence' rule is triggered."""
    alert_confidence = 0.2
    alert = anomaly_alert_factory(confidence=alert_confidence, anomaly_type=AnomalyType.UNKNOWN)
    reading = sensor_reading_factory(quality=0.8, sensor_type=SensorType.VIBRATION, value=30)

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    assert -0.1 == pytest.approx(adjustment, abs=1e-9)
    assert len(reasons) == 1
    expected_reason = f"Initial alert confidence ({alert.confidence:.2f}) is below threshold (0.3)."
    assert expected_reason in reasons

@pytest.mark.asyncio
async def test_interaction_only_poor_quality_triggered(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test only 'Poor Data Quality' rule is triggered."""
    alert = anomaly_alert_factory(confidence=0.5, anomaly_type=AnomalyType.UNKNOWN)
    reading_quality = 0.4
    reading = sensor_reading_factory(quality=reading_quality, sensor_type=SensorType.VIBRATION, value=30)

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    assert -0.2 == pytest.approx(adjustment, abs=1e-9)
    assert len(reasons) == 1
    expected_reason = f"Triggering sensor reading quality ({reading.quality:.2f}) is low (below 0.5)."
    assert expected_reason in reasons

@pytest.mark.asyncio
async def test_interaction_only_temp_spike_triggered(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test only 'Value vs. Type-Specific Threshold' (Spike) rule is triggered."""
    alert = anomaly_alert_factory(confidence=0.5, anomaly_type=AnomalyType.SPIKE)
    reading_value = 35.0
    reading = sensor_reading_factory(
        quality=0.8, sensor_type=SensorType.TEMPERATURE, value=reading_value
    )

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)
    
    assert -0.05 == pytest.approx(adjustment, abs=1e-9)
    assert len(reasons) == 1
    expected_reason = (
        f"Temperature spike alert ({alert.anomaly_type}) for a value ({reading.value}°C) "
        f"that is not considered extremely high (< 40°C)."
    )
    assert expected_reason in reasons

@pytest.mark.asyncio
async def test_interaction_low_confidence_and_poor_quality_triggered(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test 'Low Original Confidence' AND 'Poor Data Quality' rules are triggered."""
    alert_confidence = 0.2
    alert = anomaly_alert_factory(confidence=alert_confidence, anomaly_type=AnomalyType.UNKNOWN)
    reading_quality = 0.4
    reading = sensor_reading_factory(quality=reading_quality, sensor_type=SensorType.VIBRATION, value=30)

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    assert -0.3 == pytest.approx(adjustment, abs=1e-9) # -0.1 (confidence) + -0.2 (quality)
    assert len(reasons) == 2
    reason1 = f"Initial alert confidence ({alert.confidence:.2f}) is below threshold (0.3)."
    reason2 = f"Triggering sensor reading quality ({reading.quality:.2f}) is low (below 0.5)."
    assert reason1 in reasons
    assert reason2 in reasons

@pytest.mark.asyncio
async def test_interaction_all_rules_triggered_temp_spike(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test all three rule types are triggered (Low Confidence, Poor Quality, Temp Spike)."""
    alert_confidence = 0.2
    alert = anomaly_alert_factory(confidence=alert_confidence, anomaly_type=AnomalyType.SPIKE)
    
    reading_quality = 0.4
    reading_value = 35.0
    reading = sensor_reading_factory(
        quality=reading_quality, sensor_type=SensorType.TEMPERATURE, value=reading_value
    )

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    expected_adjustment = -0.1 + -0.2 + -0.05
    assert expected_adjustment == pytest.approx(adjustment, abs=1e-9)
    assert len(reasons) == 3
    
    reason_low_conf = f"Initial alert confidence ({alert.confidence:.2f}) is below threshold (0.3)."
    reason_poor_quality = f"Triggering sensor reading quality ({reading.quality:.2f}) is low (below 0.5)."
    reason_temp_spike = (
        f"Temperature spike alert ({alert.anomaly_type}) for a value ({reading.value}°C) "
        f"that is not considered extremely high (< 40°C)."
    )
    assert reason_low_conf in reasons
    assert reason_poor_quality in reasons
    assert reason_temp_spike in reasons


# Tests for Edge Conditions

# Edge Cases for Rule 1: Low Original Confidence (Threshold 0.3)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_confidence, triggered, expected_adjustment",
    [
        (0.3, False, 0.0),
        (0.299, True, -0.1),
        (0.301, False, 0.0),
    ],
)
async def test_edge_low_confidence(
    anomaly_alert_factory, sensor_reading_factory, rule_engine,
    test_confidence, triggered, expected_adjustment
):
    """Test edge conditions for the Low Original Confidence rule."""
    alert = anomaly_alert_factory(confidence=test_confidence, anomaly_type=AnomalyType.UNKNOWN)
    # Ensure other rules are not triggered
    reading = sensor_reading_factory(quality=0.8, sensor_type=SensorType.VIBRATION, value=30) 
    
    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    assert expected_adjustment == pytest.approx(adjustment, abs=1e-9)
    reason = f"Initial alert confidence ({alert.confidence:.2f}) is below threshold (0.3)."
    if triggered:
        assert reason in reasons
    else:
        assert reason not in reasons
        if expected_adjustment == 0.0:
             assert reasons == ["No rule-based adjustments applied."] or not any("Initial alert confidence" in r for r in reasons)


# Edge Cases for Rule 2: Poor Data Quality (Threshold 0.5)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_quality, triggered, expected_adjustment",
    [
        (0.5, False, 0.0),
        (0.499, True, -0.2),
        (0.501, False, 0.0),
    ],
)
async def test_edge_poor_quality(
    anomaly_alert_factory, sensor_reading_factory, rule_engine,
    test_quality, triggered, expected_adjustment
):
    """Test edge conditions for the Poor Data Quality rule."""
    # Ensure other rules are not triggered
    alert = anomaly_alert_factory(confidence=0.5, anomaly_type=AnomalyType.UNKNOWN)
    reading = sensor_reading_factory(quality=test_quality, sensor_type=SensorType.VIBRATION, value=30)

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    assert expected_adjustment == pytest.approx(adjustment, abs=1e-9)
    reason = f"Triggering sensor reading quality ({reading.quality:.2f}) is low (below 0.5)."
    if triggered:
        assert reason in reasons
    else:
        assert reason not in reasons
        if expected_adjustment == 0.0:
            assert reasons == ["No rule-based adjustments applied."] or not any("Triggering sensor reading quality" in r for r in reasons)


# Edge Cases for Rule 3: Temperature/Spike (Value < 40°C)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_value, triggered, expected_adjustment",
    [
        (40.0, False, 0.0),
        (39.999, True, -0.05),
        (40.001, False, 0.0),
    ],
)
async def test_edge_temp_spike_value(
    anomaly_alert_factory, sensor_reading_factory, rule_engine,
    test_value, triggered, expected_adjustment
):
    """Test edge conditions for the Temperature/Spike rule."""
    # Ensure other rules are not triggered
    alert = anomaly_alert_factory(confidence=0.5, anomaly_type=AnomalyType.SPIKE)
    reading = sensor_reading_factory(
        quality=0.8, sensor_type=SensorType.TEMPERATURE, value=test_value
    )

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    assert expected_adjustment == pytest.approx(adjustment, abs=1e-9)
    reason = (
        f"Temperature spike alert ({alert.anomaly_type}) for a value ({reading.value}°C) "
        f"that is not considered extremely high (< 40°C)."
    )
    if triggered:
        assert reason in reasons
    else:
        assert reason not in reasons
        if expected_adjustment == 0.0:
            assert reasons == ["No rule-based adjustments applied."] or not any("Temperature spike alert" in r for r in reasons)


# Edge Cases for Rule 3: Temperature/Low Value (Value > 0°C)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_value, triggered, expected_adjustment",
    [
        (0.0, False, 0.0),
        (-0.001, False, 0.0), # Not triggered because value <= 0
        (0.001, True, -0.05),  # Triggered because value > 0
    ],
)
async def test_edge_temp_low_value(
    anomaly_alert_factory, sensor_reading_factory, rule_engine,
    test_value, triggered, expected_adjustment
):
    """Test edge conditions for the Temperature/Low Value rule."""
    # Ensure other rules are not triggered
    alert = anomaly_alert_factory(confidence=0.5, anomaly_type=AnomalyType.LOW_VALUE)
    reading = sensor_reading_factory(
        quality=0.8, sensor_type=SensorType.TEMPERATURE, value=test_value
    )

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    assert expected_adjustment == pytest.approx(adjustment, abs=1e-9)
    reason = (
        f"Temperature low_value alert ({alert.anomaly_type}) for a value ({reading.value}°C) "
        f"that is not critically low (> 0°C)."
    )
    if triggered:
        assert reason in reasons
    else:
        assert reason not in reasons
        # If no rules triggered, the default message should be there.
        # Or, more robustly, ensure the specific reason for *this* rule is not present.
        if expected_adjustment == 0.0 :
             assert reasons == ["No rule-based adjustments applied."] or not any("Temperature low_value alert" in r for r in reasons)

@pytest.mark.asyncio
async def test_temp_low_value_not_temperature_sensor_not_triggered(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test Rule 3: Low_value alert, but not a temperature sensor, rule NOT triggered."""
    alert = anomaly_alert_factory(confidence=0.5, anomaly_type=AnomalyType.LOW_VALUE)
    reading_value = 5.0 # Value that would trigger if it were temperature
    reading = sensor_reading_factory(
        quality=0.8, sensor_type=SensorType.VIBRATION, value=reading_value
    )

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    assert 0.0 == pytest.approx(adjustment, abs=1e-9)
    # Construct the specific reason string that would appear if it was a temp sensor
    hypothetical_temp_reading_for_reason = SensorReading(
        sensor_id=reading.sensor_id, sensor_type=SensorType.TEMPERATURE, value=reading.value,
        timestamp=reading.timestamp, quality=reading.quality, unit=reading.unit
    )
    reason_not_expected = (
        f"Temperature low_value alert ({alert.anomaly_type}) for a value ({hypothetical_temp_reading_for_reason.value}°C) "
        f"that is not critically low (> 0°C)."
    )
    assert reason_not_expected not in reasons

@pytest.mark.asyncio
async def test_temp_low_value_not_low_value_anomaly_not_triggered(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test Rule 3: Temperature sensor, value > 0°C, but not a low_value anomaly, rule NOT triggered."""
    alert = anomaly_alert_factory(confidence=0.5, anomaly_type=AnomalyType.OTHER) # Not "low_value"
    reading_value = 5.0
    reading = sensor_reading_factory(
        quality=0.8, sensor_type=SensorType.TEMPERATURE, value=reading_value
    )

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    assert 0.0 == pytest.approx(adjustment, abs=1e-9)
    # Use "low_value" in the hypothetical reason because that's what the rule checks for
    reason_not_expected = (
        f"Temperature low_value alert (low_value) for a value ({reading.value}°C) "
        f"that is not critically low (> 0°C)."
    )
    assert reason_not_expected not in reasons

@pytest.mark.asyncio
async def test_temp_spike_not_temperature_sensor_not_triggered(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test Rule 3: Spike alert, but not a temperature sensor, rule NOT triggered."""
    alert = anomaly_alert_factory(confidence=0.5, anomaly_type=AnomalyType.SPIKE)
    reading_value = 35.0 # Value that would trigger if it were temperature
    reading = sensor_reading_factory(
        quality=0.8, sensor_type=SensorType.VIBRATION, value=reading_value
    )

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    # All rules should not be triggered
    assert 0.0 == pytest.approx(adjustment, abs=1e-9)
    # Construct the specific reason string that would appear if it was a temp sensor
    # to ensure it's not present.
    hypothetical_temp_reading_for_reason = SensorReading(
        sensor_id=reading.sensor_id, sensor_type=SensorType.TEMPERATURE, value=reading.value,
        timestamp=reading.timestamp, quality=reading.quality, unit=reading.unit
    )
    reason_not_expected = (
        f"Temperature spike alert ({alert.anomaly_type}) for a value ({hypothetical_temp_reading_for_reason.value}°C) "
        f"that is not considered extremely high (< 40°C)."
    )
    assert reason_not_expected not in reasons

@pytest.mark.asyncio
async def test_temp_spike_not_spike_anomaly_not_triggered(
    anomaly_alert_factory, sensor_reading_factory, rule_engine
):
    """Test Rule 3: Temperature sensor, value < 40°C, but not a spike anomaly, rule NOT triggered."""
    alert = anomaly_alert_factory(confidence=0.5, anomaly_type=AnomalyType.UNKNOWN)
    reading_value = 35.0
    reading = sensor_reading_factory(
        quality=0.8, sensor_type=SensorType.TEMPERATURE, value=reading_value
    )

    adjustment, reasons = await rule_engine.evaluate_rules(alert, reading)

    # All rules should not be triggered
    assert 0.0 == pytest.approx(adjustment, abs=1e-9)
    reason_not_expected = (
        # Use "spike" in the hypothetical reason because that's what the rule checks for
        f"Temperature spike alert (spike) for a value ({reading.value}°C) "
        f"that is not considered extremely high (< 40°C)."
    )
    assert reason_not_expected not in reasons
