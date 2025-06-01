"""Statistical models for anomaly detection."""
import logging
import math  # Using math.isclose for float comparisons might be useful for tests

logger = logging.getLogger(__name__)


class StatisticalAnomalyDetector:
    """Detects anomalies based on statistical thresholds."""

    def __init__(self, config: dict = None):
        """
        Initialize the StatisticalAnomalyDetector.

        Future configuration (e.g., threshold parameters) can be passed via config.
        """
        self.config = config if config is not None else {}
        # Example: self.sigma_threshold = self.config.get("sigma_threshold", 3)
        self.sigma_threshold = 3  # Defaulting to 3-sigma

    def detect(
        self, reading_value: float, historical_mean: float, historical_std: float
    ) -> tuple[bool, float, str]:
        """
        Detect if a reading_value is an anomaly based on historical data.

        Args:
            reading_value: Current sensor reading.
            historical_mean: Historical mean of sensor readings.
            historical_std: Historical standard deviation of sensor readings.

        Returns:
            A tuple containing:
                - is_anomaly (bool): True if an anomaly is detected, False otherwise.
                - confidence_score (float): Confidence in the anomaly detection.
                                            0.0 if not an anomaly.
                                            Capped between 0.5 and 1.0 if an anomaly.
                - anomaly_type_description (str): Description of the anomaly type.
        """
        is_anomaly = False
        confidence_score = 0.0
        anomaly_type_description = "normal"

        if historical_std == 0:
            # If std is zero, any deviation from mean is an anomaly if not equal.
            # If equal, it's normal.
            if not math.isclose(reading_value, historical_mean):
                is_anomaly = True
                confidence_score = 1.0  # Max confidence as any deviation is significant
                anomaly_type_description = "statistical_threshold_breach_zero_std"
                logger.info(
                    f"Anomaly (zero std): val={reading_value}, mean={historical_mean}"
                )
            else:
                # Value is same as mean, and std is zero, so it's normal.
                anomaly_type_description = "normal_zero_std"
                logger.info(
                    f"Normal (zero std): val={reading_value}, mean={historical_mean}"
                )
        else:
            deviation = abs(reading_value - historical_mean)
            threshold = self.sigma_threshold * historical_std

            if deviation > threshold:
                is_anomaly = True
                # Calculate confidence: 1.0 - (threshold / deviation)
                # Score increases as deviation surpasses threshold.
                # Capped between 0.5 and 1.0.
                raw_confidence = 1.0 - (threshold / deviation) if deviation > 0 else 1.0
                confidence_score = min(1.0, max(0.5, raw_confidence))
                anomaly_type_description = "statistical_threshold_breach"
                logger.info(
                    f"Anomaly: val={reading_value}, mean={historical_mean}, "
                    f"std={historical_std}, dev={deviation:.2f}, threshold={threshold:.2f}"
                )
            else:
                logger.info(
                    f"Normal: val={reading_value}, mean={historical_mean}, "
                    f"std={historical_std}, dev={deviation:.2f}, threshold={threshold:.2f}"
                )

        return is_anomaly, confidence_score, anomaly_type_description
