import unittest
from datetime import datetime

# Assuming models are in core.models.data_models
from core.models.data_models import AnomalyAlert, SensorReading
from apps.rules.validation_rules import RuleEngine


class TestRuleEngine(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.engine = RuleEngine()
        # Default timestamp for models if not specified in test
        self.default_timestamp = datetime.utcnow()

    async def test_rule_low_original_confidence_triggered(self):
        alert = AnomalyAlert(
            sensor_id="s1",
            confidence=0.2,
            anomaly_type="type1",
            severity=3,
            timestamp=self.default_timestamp,
        )
        reading = SensorReading(
            sensor_id="s1",
            quality=0.9,
            value=10,
            sensor_type="TEMPERATURE",
            timestamp=self.default_timestamp,
        )

        adj, reasons = await self.engine.evaluate_rules(alert, reading)

        self.assertAlmostEqual(adj, -0.2)
        self.assertIn(
            "Low original alert confidence (0.20). Adjusted by -0.20.", reasons[0]
        )

    async def test_rule_low_original_confidence_not_triggered(self):
        alert = AnomalyAlert(
            sensor_id="s1",
            confidence=0.5,
            anomaly_type="type1",
            severity=3,
            timestamp=self.default_timestamp,
        )
        reading = SensorReading(
            sensor_id="s1",
            quality=0.9,
            value=10,
            sensor_type="TEMPERATURE",
            timestamp=self.default_timestamp,
        )

        adj, reasons = await self.engine.evaluate_rules(alert, reading)

        self.assertAlmostEqual(adj, 0.0)  # No adjustment from this rule
        self.assertNotIn("Low original alert confidence", "".join(reasons))

    async def test_rule_poor_data_quality_triggered(self):
        alert = AnomalyAlert(
            sensor_id="s1",
            confidence=0.8,
            anomaly_type="type1",
            severity=3,
            timestamp=self.default_timestamp,
        )
        reading = SensorReading(
            sensor_id="s1",
            quality=0.6,
            value=10,
            sensor_type="TEMPERATURE",
            timestamp=self.default_timestamp,
        )  # quality < 0.7

        adj, reasons = await self.engine.evaluate_rules(alert, reading)

        self.assertAlmostEqual(adj, -0.15)
        self.assertIn("Poor sensor data quality (0.60). Adjusted by -0.15.", reasons[0])

    async def test_rule_poor_data_quality_not_triggered(self):
        alert = AnomalyAlert(
            sensor_id="s1",
            confidence=0.8,
            anomaly_type="type1",
            severity=3,
            timestamp=self.default_timestamp,
        )
        reading = SensorReading(
            sensor_id="s1",
            quality=0.8,
            value=10,
            sensor_type="TEMPERATURE",
            timestamp=self.default_timestamp,
        )

        adj, reasons = await self.engine.evaluate_rules(alert, reading)

        self.assertAlmostEqual(adj, 0.0)
        self.assertNotIn("Poor sensor data quality", "".join(reasons))

    # --- Value vs. Type-Specific Threshold Tests ---
    async def test_rule_value_vs_threshold_triggered_temp_marginally_high(self):
        alert = AnomalyAlert(
            sensor_id="s1",
            confidence=0.8,
            anomaly_type="statistical_threshold_breach",
            severity=4,
            timestamp=self.default_timestamp,
        )
        # TEMPERATURE range: (-20, 100). Margin 10% of 120 = 12. Marginal high: >100 and <=112
        reading = SensorReading(
            sensor_id="s1",
            quality=0.9,
            value=105,
            sensor_type="TEMPERATURE",
            unit="C",
            timestamp=self.default_timestamp,
        )

        adj, reasons = await self.engine.evaluate_rules(alert, reading)

        self.assertAlmostEqual(adj, -0.1)
        self.assertIn(
            "Statistical anomaly (Severity 4), but value (105 C) is near typical operational range for TEMPERATURE (-20-100 C). Adjusted by -0.10.",
            reasons[0],
        )

    async def test_rule_value_vs_threshold_triggered_temp_marginally_low(self):
        alert = AnomalyAlert(
            sensor_id="s1",
            confidence=0.8,
            anomaly_type="statistical_threshold_breach",
            severity=5,
            timestamp=self.default_timestamp,
        )
        # TEMPERATURE range: (-20, 100). Margin 10% of 120 = 12. Marginal low: <-20 and >= -32
        reading = SensorReading(
            sensor_id="s1",
            quality=0.9,
            value=-25,
            sensor_type="TEMPERATURE",
            unit="C",
            timestamp=self.default_timestamp,
        )

        adj, reasons = await self.engine.evaluate_rules(alert, reading)

        self.assertAlmostEqual(adj, -0.1)
        self.assertIn(
            "Statistical anomaly (Severity 5), but value (-25 C) is near typical operational range for TEMPERATURE (-20-100 C). Adjusted by -0.10.",
            reasons[0],
        )

    async def test_rule_value_vs_threshold_triggered_pressure_marginally_high(self):
        alert = AnomalyAlert(
            sensor_id="s2",
            confidence=0.8,
            anomaly_type="statistical_threshold_breach",
            severity=4,
            timestamp=self.default_timestamp,
        )
        # PRESSURE range: (800, 1200). Margin 10% of 400 = 40. Marginal high: >1200 and <=1240
        reading = SensorReading(
            sensor_id="s2",
            quality=0.9,
            value=1230,
            sensor_type="PRESSURE",
            unit="PSI",
            timestamp=self.default_timestamp,
        )

        adj, reasons = await self.engine.evaluate_rules(alert, reading)

        self.assertAlmostEqual(adj, -0.1)
        self.assertIn(
            "Statistical anomaly (Severity 4), but value (1230 PSI) is near typical operational range for PRESSURE (800-1200 PSI). Adjusted by -0.10.",
            reasons[0],
        )

    async def test_rule_value_vs_threshold_not_triggered_wrong_anomaly_type(self):
        alert = AnomalyAlert(
            sensor_id="s1",
            confidence=0.8,
            anomaly_type="spike_detected",
            severity=4,
            timestamp=self.default_timestamp,
        )  # Wrong type
        reading = SensorReading(
            sensor_id="s1",
            quality=0.9,
            value=105,
            sensor_type="TEMPERATURE",
            unit="C",
            timestamp=self.default_timestamp,
        )

        adj, reasons = await self.engine.evaluate_rules(alert, reading)
        self.assertAlmostEqual(adj, 0.0)
        self.assertEqual(len(reasons), 0)

    async def test_rule_value_vs_threshold_not_triggered_low_severity(self):
        alert = AnomalyAlert(
            sensor_id="s1",
            confidence=0.8,
            anomaly_type="statistical_threshold_breach",
            severity=3,
            timestamp=self.default_timestamp,
        )  # Severity < 4
        reading = SensorReading(
            sensor_id="s1",
            quality=0.9,
            value=105,
            sensor_type="TEMPERATURE",
            unit="C",
            timestamp=self.default_timestamp,
        )

        adj, reasons = await self.engine.evaluate_rules(alert, reading)
        self.assertAlmostEqual(adj, 0.0)
        self.assertEqual(len(reasons), 0)

    async def test_rule_value_vs_threshold_not_triggered_value_far_outside_range(self):
        alert = AnomalyAlert(
            sensor_id="s1",
            confidence=0.8,
            anomaly_type="statistical_threshold_breach",
            severity=4,
            timestamp=self.default_timestamp,
        )
        reading = SensorReading(
            sensor_id="s1",
            quality=0.9,
            value=150,
            sensor_type="TEMPERATURE",
            unit="C",
            timestamp=self.default_timestamp,
        )  # Far outside

        adj, reasons = await self.engine.evaluate_rules(alert, reading)
        self.assertAlmostEqual(adj, 0.0)  # This specific rule logic doesn't trigger
        self.assertEqual(len(reasons), 0)

    async def test_rule_value_vs_threshold_not_triggered_value_within_range(self):
        alert = AnomalyAlert(
            sensor_id="s1",
            confidence=0.8,
            anomaly_type="statistical_threshold_breach",
            severity=4,
            timestamp=self.default_timestamp,
        )
        reading = SensorReading(
            sensor_id="s1",
            quality=0.9,
            value=50,
            sensor_type="TEMPERATURE",
            unit="C",
            timestamp=self.default_timestamp,
        )  # Within range

        adj, reasons = await self.engine.evaluate_rules(alert, reading)
        self.assertAlmostEqual(adj, 0.0)
        self.assertEqual(len(reasons), 0)

    async def test_rule_value_vs_threshold_not_triggered_unknown_sensor_type(self):
        alert = AnomalyAlert(
            sensor_id="s1",
            confidence=0.8,
            anomaly_type="statistical_threshold_breach",
            severity=4,
            timestamp=self.default_timestamp,
        )
        reading = SensorReading(
            sensor_id="s1",
            quality=0.9,
            value=105,
            sensor_type="HUMIDITY",
            unit="%",
            timestamp=self.default_timestamp,
        )  # HUMIDITY not in ranges

        adj, reasons = await self.engine.evaluate_rules(alert, reading)
        self.assertAlmostEqual(adj, 0.0)
        self.assertEqual(len(reasons), 0)

    async def test_rule_value_vs_threshold_not_triggered_non_numeric_value(self):
        alert = AnomalyAlert(
            sensor_id="s1",
            confidence=0.8,
            anomaly_type="statistical_threshold_breach",
            severity=4,
            timestamp=self.default_timestamp,
        )
        reading = SensorReading(
            sensor_id="s1",
            quality=0.9,
            value="error",
            sensor_type="TEMPERATURE",
            unit="C",
            timestamp=self.default_timestamp,
        )  # Non-numeric

        adj, reasons = await self.engine.evaluate_rules(alert, reading)
        self.assertAlmostEqual(adj, 0.0)
        self.assertEqual(
            len(reasons), 0
        )  # Rule engine currently skips non-numeric, no reason added by this rule part

    # --- Combination Tests ---
    async def test_multiple_rules_triggered(self):
        # Low confidence, poor quality, and marginally high value
        alert = AnomalyAlert(
            sensor_id="s1",
            confidence=0.25,
            anomaly_type="statistical_threshold_breach",
            severity=4,
            timestamp=self.default_timestamp,
        )
        reading = SensorReading(
            sensor_id="s1",
            quality=0.65,
            value=107,
            sensor_type="TEMPERATURE",
            unit="C",
            timestamp=self.default_timestamp,
        )

        # Comments explaining the components of expected_adj
        # -0.2 for low confidence (alert.confidence=0.25 is < 0.3)
        # -0.15 for poor quality (reading.quality=0.65 is < 0.7)
        # -0.1 for value vs threshold (TEMPERATURE 107 is marginally high: >100 and <=112)
        expected_adj = -0.2 - 0.15 - 0.1
        adj, reasons = await self.engine.evaluate_rules(alert, reading)

        self.assertAlmostEqual(adj, expected_adj)
        self.assertEqual(len(reasons), 3)
        self.assertIn(
            "Low original alert confidence (0.25). Adjusted by -0.20.", reasons
        )
        self.assertIn("Poor sensor data quality (0.65). Adjusted by -0.15.", reasons)
        self.assertIn(
            "Statistical anomaly (Severity 4), but value (107 C) is near typical operational range for TEMPERATURE (-20-100 C). Adjusted by -0.10.",
            reasons,
        )

    async def test_no_rules_triggered(self):
        alert = AnomalyAlert(
            sensor_id="s1",
            confidence=0.7,
            anomaly_type="spike",
            severity=3,
            timestamp=self.default_timestamp,
        )
        reading = SensorReading(
            sensor_id="s1",
            quality=0.9,
            value=50,
            sensor_type="TEMPERATURE",
            unit="C",
            timestamp=self.default_timestamp,
        )

        adj, reasons = await self.engine.evaluate_rules(alert, reading)

        self.assertAlmostEqual(adj, 0.0)
        self.assertEqual(len(reasons), 0)


if __name__ == "__main__":
    unittest.main()
