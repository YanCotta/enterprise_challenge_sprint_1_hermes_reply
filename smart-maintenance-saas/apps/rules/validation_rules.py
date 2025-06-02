from typing import Tuple, List  # Removed Dict, Any as they were F401
from data.schemas import AnomalyAlert, SensorReading  # Updated import


class RuleEngine:
    def __init__(self):
        # Basic initialization, can be expanded later (e.g., load rules from config)
        # Ensure sensor types here match those used in SensorReading.sensor_type
        self.typical_ranges = {
            "TEMPERATURE": (-20, 100),
            "PRESSURE": (800, 1200),
            "VIBRATION": (0, 10),
        }

    async def evaluate_rules(
        self, alert: AnomalyAlert, reading: SensorReading
    ) -> Tuple[float, List[str]]:
        rule_based_confidence_adjustment = 0.0
        rule_reasons = []

        # Rule 1: Low Original Confidence Check
        if alert.confidence < 0.3:
            adjustment = -0.2
            rule_based_confidence_adjustment += adjustment
            rule_reasons.append(
                f"Low original alert confidence ({alert.confidence:.2f}). Adjusted by {adjustment:.2f}."
            )

        # Rule 2: Poor Data Quality Check
        if reading.quality < 0.7:
            adjustment = -0.15
            rule_based_confidence_adjustment += adjustment
            rule_reasons.append(
                f"Poor sensor data quality ({reading.quality:.2f}). Adjusted by {adjustment:.2f}."
            )

        # Rule 3: Value vs. Type-Specific Threshold (Simplified)
        if alert.anomaly_type == "statistical_threshold_breach" and alert.severity >= 4:
            sensor_type_upper = reading.sensor_type.upper()  # Ensure case-insensitivity
            if sensor_type_upper in self.typical_ranges:
                min_val, max_val = self.typical_ranges[sensor_type_upper]
                range_width = max_val - min_val
                margin = 0.10 * range_width  # 10% margin

                # Check if value is numeric before comparison
                if isinstance(reading.value, (int, float)):
                    # Check if value is marginally outside the broad range
                    is_marginally_low = (reading.value < min_val) and (
                        reading.value >= min_val - margin
                    )
                    is_marginally_high = (reading.value > max_val) and (
                        reading.value <= max_val + margin
                    )

                    if is_marginally_low or is_marginally_high:
                        adjustment = -0.1
                        rule_based_confidence_adjustment += adjustment
                        reading_unit = reading.unit if reading.unit else ""
                        reason = (
                            f"Statistical anomaly (Severity {alert.severity}), "
                            f"but value ({reading.value} {reading_unit}) is near typical operational range "
                            f"for {sensor_type_upper} ({min_val}-{max_val} {reading_unit}). Adjusted by {adjustment:.2f}."
                        )
                        rule_reasons.append(reason)
                else:
                    # Optional: log a warning or add a reason if value is not numeric for a checkable sensor type
                    # rule_reasons.append(f"Cannot evaluate value range for {sensor_type_upper} as value '{reading.value}' is not numeric.")
                    pass

        return rule_based_confidence_adjustment, rule_reasons


# Example Usage (not part of the class definition, just for illustration)
if __name__ == "__main__":
    import asyncio
    from datetime import datetime  # Ensure datetime is imported for example

    async def main():
        engine = RuleEngine()

        # Example 1: Low confidence alert
        alert1 = AnomalyAlert(
            sensor_id="s1",
            confidence=0.25,
            anomaly_type="model_drift",
            severity=3,
            timestamp=datetime.now(),
        )
        reading1 = SensorReading(
            sensor_id="s1",
            quality=0.9,
            value=50,
            sensor_type="TEMPERATURE",
            timestamp=datetime.now(),
        )
        adj1, reasons1 = await engine.evaluate_rules(alert1, reading1)
        print(f"Example 1: Adjustment={adj1}, Reasons={reasons1}")

        # Example 2: Poor data quality
        alert2 = AnomalyAlert(
            sensor_id="s2",
            confidence=0.8,
            anomaly_type="spike_detected",
            severity=5,
            timestamp=datetime.now(),
        )
        reading2 = SensorReading(
            sensor_id="s2",
            quality=0.6,
            value=105,
            sensor_type="TEMPERATURE",
            timestamp=datetime.now(),
        )
        adj2, reasons2 = await engine.evaluate_rules(alert2, reading2)
        print(f"Example 2: Adjustment={adj2}, Reasons={reasons2}")

        # Example 3: Statistical breach, value marginally outside range
        alert3 = AnomalyAlert(
            sensor_id="s3",
            confidence=0.7,
            anomaly_type="statistical_threshold_breach",
            severity=4,
            timestamp=datetime.now(),
        )
        reading3 = SensorReading(
            sensor_id="s3",
            quality=0.95,
            value=108,
            sensor_type="TEMPERATURE",
            unit="°C",
            timestamp=datetime.now(),
        )  # 100 is max, 10% margin of 120 is 12, so 100 to 112
        adj3, reasons3 = await engine.evaluate_rules(alert3, reading3)
        print(f"Example 3: Adjustment={adj3}, Reasons={reasons3}")

        # Example 3b: Statistical breach, value significantly outside range (no adjustment for this rule)
        alert3b = AnomalyAlert(
            sensor_id="s3b",
            confidence=0.7,
            anomaly_type="statistical_threshold_breach",
            severity=4,
            timestamp=datetime.now(),
        )
        reading3b = SensorReading(
            sensor_id="s3b",
            quality=0.95,
            value=130,
            sensor_type="TEMPERATURE",
            unit="°C",
            timestamp=datetime.now(),
        )
        adj3b, reasons3b = await engine.evaluate_rules(alert3b, reading3b)
        print(f"Example 3b: Adjustment={adj3b}, Reasons={reasons3b}")

        # Example 4: All rules trigger
        alert4 = AnomalyAlert(
            sensor_id="s4",
            confidence=0.2,
            anomaly_type="statistical_threshold_breach",
            severity=5,
            timestamp=datetime.now(),
        )
        reading4 = SensorReading(
            sensor_id="s4",
            quality=0.5,
            value=-25,
            sensor_type="TEMPERATURE",
            unit="°C",
            timestamp=datetime.now(),
        )  # -20 is min, 10% margin of 120 is 12, so -20 to -32
        adj4, reasons4 = await engine.evaluate_rules(alert4, reading4)
        print(f"Example 4: Adjustment={adj4}, Reasons={reasons4}")

        # Example 5: Non-numeric value for a sensor type that has a range check
        alert5 = AnomalyAlert(
            sensor_id="s5",
            confidence=0.8,
            anomaly_type="statistical_threshold_breach",
            severity=4,
            timestamp=datetime.now(),
        )
        reading5 = SensorReading(
            sensor_id="s5",
            quality=0.9,
            value="error_code",
            sensor_type="TEMPERATURE",
            timestamp=datetime.now(),
        )
        adj5, reasons5 = await engine.evaluate_rules(alert5, reading5)
        print(f"Example 5: Adjustment={adj5}, Reasons={reasons5}")

    # Import datetime for example usage if not already imported at top level for the main module
    # from datetime import datetime # This was in the original file, re-adding if needed by main()

    asyncio.run(main())
