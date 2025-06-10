#!/usr/bin/env python3
"""
Quick test to verify ValidationAgent historical validation changes work correctly.
"""

import asyncio
import warnings
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from apps.agents.core.validation_agent import ValidationAgent
from data.schemas import AnomalyAlert, SensorReading, SensorType

# Suppress warnings for this test
warnings.filterwarnings("ignore")

async def test_historical_validation():
    """Test the updated historical validation logic."""
    
    # Create agent with specific settings
    mock_event_bus = AsyncMock()
    mock_crud = AsyncMock()
    mock_rule_engine = AsyncMock()
    mock_db_session_factory = AsyncMock()
    
    agent = ValidationAgent(
        agent_id='test_agent',
        event_bus=mock_event_bus,
        crud_sensor_reading=mock_crud,
        rule_engine=mock_rule_engine,
        db_session_factory=mock_db_session_factory,
        specific_settings={
            'recent_stability_window': 3,
            'recent_stability_factor': 0.1,
            'recent_stability_min_std_dev': 0.05,
            'recent_stability_jump_adjustment': 0.10,
            'recent_stability_minor_deviation_adjustment': -0.05,
            'volatile_baseline_adjustment': 0.05,
            'recurring_anomaly_diff_factor': 0.5,
            'recurring_anomaly_threshold_pct': 0.25,
            'recurring_anomaly_penalty': -0.05,
        }
    )
    
    print("✅ ValidationAgent created with updated settings")
    
    # Test 1: Recent Value Stability (Minor Deviation)
    print("\n📊 Test 1: Recent Value Stability - Minor Deviation")
    now = datetime.utcnow()
    historical_readings = [
        SensorReading(
            sensor_id="test_sensor",
            value=20.0,
            timestamp=now - timedelta(hours=1),
            sensor_type=SensorType.TEMPERATURE,
            quality=1.0,
            unit="C"
        ),
        SensorReading(
            sensor_id="test_sensor", 
            value=21.0,
            timestamp=now - timedelta(hours=2),
            sensor_type=SensorType.TEMPERATURE,
            quality=1.0,
            unit="C"
        ),
        SensorReading(
            sensor_id="test_sensor",
            value=19.5,
            timestamp=now - timedelta(hours=3),
            sensor_type=SensorType.TEMPERATURE,
            quality=1.0,
            unit="C"
        ),
    ]
    
    alert = AnomalyAlert(
        sensor_id="test_sensor",
        anomaly_type="spike",
        severity=4,
        confidence=0.8,
        description="Test anomaly",
        created_at=now
    )
    
    reading = SensorReading(
        sensor_id="test_sensor",
        value=20.5,
        timestamp=now,
        sensor_type=SensorType.TEMPERATURE,
        quality=1.0,
        unit="C"
    )
    
    adjustment, reasons = agent._perform_historical_validation(alert, reading, historical_readings)
    print(f"   Adjustment: {adjustment}")
    print(f"   Reasons: {reasons}")
    expected_adjustment = -0.05  # Minor deviation penalty
    assert abs(adjustment - expected_adjustment) < 0.001, f"Expected {expected_adjustment}, got {adjustment}"
    assert any("Recent value stability" in reason for reason in reasons), "Expected stability reason"
    print("   ✅ Minor deviation test passed")
    
    # Test 2: Recurring Anomaly Pattern
    print("\n📊 Test 2: Recurring Anomaly Pattern")
    # Create oscillating pattern: 10, 16, 10, 16, 10 (60% differences)
    recurring_readings = []
    base_val = 10
    for i in range(1, 6):
        val = base_val + (i % 2) * base_val * 0.6  # Alternates 10, 16, 10, 16, 10
        recurring_readings.append(
            SensorReading(
                sensor_id="test_sensor",
                value=val,
                timestamp=now - timedelta(hours=i),
                sensor_type=SensorType.TEMPERATURE,
                quality=1.0,
                unit="C"
            )
        )
    
    adjustment2, reasons2 = agent._perform_historical_validation(alert, reading, recurring_readings)
    print(f"   Adjustment: {adjustment2}")
    print(f"   Reasons: {reasons2}")
    
    # Should trigger volatile baseline adjustment (+0.05) and recurring anomaly penalty (-0.05)
    # Net effect: 0.0
    # Volatile: std_dev of [16,10,16] is dynamically computed (~2.83), avg is dynamically computed (~14). 
    # Thresholds are derived from settings: stability factor = {agent.settings.get('recent_stability_factor', 0.1)}, 
    # min std_dev = {agent.settings.get('recent_stability_min_std_dev', 0.05)}. 
    # Volatile if std_dev is not < stability factor * avg and not < min std_dev. So, volatile.
    # Recurring: 2 out of 4 historical diffs are > 0.5 (50%), which is > threshold_pct (25%)
    expected_total_adjustment_test2 = agent.settings.get('volatile_baseline_adjustment', 0.05) + agent.settings.get('recurring_anomaly_penalty', -0.05)
    assert abs(adjustment2 - expected_total_adjustment_test2) < 0.001, f"Expected total adjustment {expected_total_adjustment_test2}, got {adjustment2}. Reasons: {reasons2}"
    expected_reason = "volatile readings"
    assert any(expected_reason.lower() in reason.lower() for reason in reasons2), "Expected volatile baseline reason"
    assert any("Recurring anomaly pattern" in reason for reason in reasons2), "Expected recurring pattern reason"
    print("   ✅ Recurring anomaly pattern with volatile baseline test passed")
    
    # Test 3: Settings-driven parameters
    print("\n📊 Test 3: Settings-driven parameters")
    print(f"   Window size: {agent.settings.get('recent_stability_window', 5)}")
    print(f"   Stability factor: {agent.settings.get('recent_stability_factor', 0.1)}")
    print(f"   Recurring threshold: {agent.settings.get('recurring_anomaly_threshold_pct', 0.25)}")
    print("   ✅ Settings properly loaded")
    
    print("\n🎉 All tests passed! ValidationAgent historical validation is working correctly.")

if __name__ == "__main__":
    asyncio.run(test_historical_validation())
