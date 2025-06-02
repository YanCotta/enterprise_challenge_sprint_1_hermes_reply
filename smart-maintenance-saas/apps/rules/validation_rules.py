import logging
from typing import Tuple, List, Any
from data.schemas import AnomalyAlert, SensorReading # Ensure these are the correct Pydantic models

class RuleEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Potentially load rules from a configuration file or database in a real scenario
        self.logger.info("RuleEngine initialized.")

    async def evaluate_rules(
        self, alert: AnomalyAlert, reading: SensorReading
    ) -> Tuple[float, List[str]]:
        '''
        Evaluates a set of predefined rules against an anomaly alert and its triggering sensor reading.

        Args:
            alert: The AnomalyAlert Pydantic model instance.
            reading: The SensorReading Pydantic model instance that triggered the alert.

        Returns:
            A tuple containing:
                - rule_based_confidence_adjustment (float): A value to adjust the original alert's confidence.
                                                           Positive values increase confidence, negative decrease.
                - rule_reasons (List[str]): A list of reasons explaining the adjustment.
        '''
        rule_based_confidence_adjustment = 0.0
        rule_reasons = []

        self.logger.debug(f"Evaluating rules for alert on sensor {alert.sensor_id} and reading from {reading.timestamp}")

        # Rule 1: Low Original Confidence
        # If the initial alert confidence is very low, it might be less reliable.
        # AnomalyAlert schema has: confidence: float = Field(ge=0, le=1)
        if alert.confidence < 0.3:
            rule_based_confidence_adjustment -= 0.1
            reason = f"Initial alert confidence ({alert.confidence:.2f}) is below threshold (0.3)."
            rule_reasons.append(reason)
            self.logger.debug(f"Rule 1 (Low Original Confidence) triggered: {reason}")

        # Rule 2: Poor Data Quality
        # If the sensor reading quality is poor, the alert might be based on faulty data.
        # SensorReading schema has: quality: float = Field(default=1.0, ge=0, le=1)
        if reading.quality < 0.5:
            rule_based_confidence_adjustment -= 0.2
            reason = f"Triggering sensor reading quality ({reading.quality:.2f}) is low (below 0.5)."
            rule_reasons.append(reason)
            self.logger.debug(f"Rule 2 (Poor Data Quality) triggered: {reason}")

        # Rule 3: Value vs. Type-Specific Broad Threshold Check (Example for Temperature)
        # This is a simplified example. Real rules would be more sophisticated and configurable.
        # SensorReading schema has: sensor_type: SensorType, value: float
        # AnomalyAlert schema has: anomaly_type: str (e.g., "spike", "drift")
        if reading.sensor_type == "temperature": # Assumes SensorType is an Enum or string
            # Example: If it's a 'spike' alert but the value is not extremely high for a temperature sensor,
            # it might be a minor fluctuation rather than a critical anomaly.
            # This rule is quite subjective and for demonstration.
            if alert.anomaly_type == "spike" and reading.value < 40: # Assuming Celsius
                rule_based_confidence_adjustment -= 0.05
                reason = (
                    f"Temperature spike alert ({alert.anomaly_type}) for a value ({reading.value}°C) "
                    f"that is not considered extremely high (< 40°C)."
                )
                rule_reasons.append(reason)
                self.logger.debug(f"Rule 3 (Temp Spike Value Check) triggered: {reason}")
            elif alert.anomaly_type == "low_value" and reading.value > 0: # Example for low value alert
                 rule_based_confidence_adjustment -=0.05
                 reason = (
                    f"Temperature low_value alert ({alert.anomaly_type}) for a value ({reading.value}°C) "
                    f"that is not critically low (> 0°C)."
                 )
                 rule_reasons.append(reason)
                 self.logger.debug(f"Rule 3 (Temp Low Value Check) triggered: {reason}")


        # Ensure adjustment does not push confidence out of bounds later
        # The adjustment is relative; final clamping will be done by the agent.

        if not rule_reasons:
            rule_reasons.append("No rule-based adjustments applied.")
            self.logger.debug("No validation rules triggered significant adjustments.")
        
        self.logger.info(f"Rule evaluation complete. Adjustment: {rule_based_confidence_adjustment}, Reasons: {rule_reasons}")
        return rule_based_confidence_adjustment, rule_reasons
