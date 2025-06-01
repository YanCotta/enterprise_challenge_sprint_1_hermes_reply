"""Statistical models for anomaly detection."""
import logging
import math
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class StatisticalAnomalyDetector:
    """Detects anomalies based on statistical thresholds using 3-sigma rule."""

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the StatisticalAnomalyDetector.

        Args:
            config: Optional configuration dictionary. Supported keys:
                - sigma_threshold: Number of standard deviations for anomaly detection (default: 3)
                - min_confidence: Minimum confidence score for anomalies (default: 0.5)
                - tolerance: Relative tolerance for float comparisons (default: 1e-09)
        """
        self.config = config if config is not None else {}
        self.sigma_threshold = self.config.get("sigma_threshold", 3)
        self.min_confidence = self.config.get("min_confidence", 0.5)
        self.tolerance = self.config.get("tolerance", 1e-09)

        # Validate configuration
        if self.sigma_threshold <= 0:
            raise ValueError("sigma_threshold must be positive")
        if not (0 <= self.min_confidence <= 1):
            raise ValueError("min_confidence must be between 0 and 1")

    def detect(
        self, reading_value: float, historical_mean: float, historical_std: float
    ) -> Tuple[bool, float, str]:
        """
        Detect if a reading_value is an anomaly based on historical data using 3-sigma rule.

        Args:
            reading_value: Current sensor reading value
            historical_mean: Historical mean of sensor readings
            historical_std: Historical standard deviation of sensor readings (must be >= 0)

        Returns:
            A tuple containing:
                - is_anomaly (bool): True if an anomaly is detected, False otherwise
                - confidence_score (float): Confidence in the anomaly detection
                                            0.0 if not an anomaly
                                            Between min_confidence and 1.0 if an anomaly
                - anomaly_type_description (str): Description of the anomaly type

        Raises:
            ValueError: If historical_std is negative or any input is NaN/infinite
        """
        # Input validation
        if not all(math.isfinite(val) for val in [reading_value, historical_mean, historical_std]):
            raise ValueError("All input values must be finite (not NaN or infinite)")

        if historical_std < 0:
            raise ValueError("historical_std must be non-negative")

        is_anomaly = False
        confidence_score = 0.0
        anomaly_type_description = "normal"

        # Handle zero standard deviation case
        if math.isclose(historical_std, 0.0, rel_tol=self.tolerance):
            if not math.isclose(reading_value, historical_mean, rel_tol=self.tolerance):
                is_anomaly = True
                confidence_score = 1.0  # Maximum confidence for any deviation when std=0
                anomaly_type_description = "statistical_threshold_breach_zero_std"
                logger.info(
                    f"Anomaly detected (zero std): value={reading_value:.4f}, "
                    f"mean={historical_mean:.4f}, deviation={abs(reading_value - historical_mean):.4f}"
                )
            else:
                anomaly_type_description = "normal_zero_std"
                logger.debug(
                    f"Normal reading (zero std): value={reading_value:.4f}, mean={historical_mean:.4f}"
                )
        else:
            # Standard 3-sigma rule
            deviation = abs(reading_value - historical_mean)
            threshold = self.sigma_threshold * historical_std

            if deviation > threshold:
                is_anomaly = True

                # Improved confidence calculation with better mathematical properties
                # Maps deviation beyond threshold to confidence score
                # Formula: confidence = min_confidence + (1 - min_confidence) * (1 - threshold/deviation)
                # This ensures:
                # - Confidence starts at min_confidence when deviation = threshold
                # - Confidence approaches 1.0 as deviation increases
                # - Mathematical stability (no division by zero since deviation > threshold > 0)
                confidence_factor = 1.0 - (threshold / deviation)
                confidence_score = self.min_confidence + (1.0 - self.min_confidence) * confidence_factor
                confidence_score = min(1.0, confidence_score)  # Ensure upper bound

                anomaly_type_description = "statistical_threshold_breach"

                logger.info(
                    f"Anomaly detected: value={reading_value:.4f}, mean={historical_mean:.4f}, "
                    f"std={historical_std:.4f}, deviation={deviation:.4f}, "
                    f"threshold={threshold:.4f}, confidence={confidence_score:.4f}"
                )
            else:
                logger.debug(
                    f"Normal reading: value={reading_value:.4f}, mean={historical_mean:.4f}, "
                    f"std={historical_std:.4f}, deviation={deviation:.4f}, "
                    f"threshold={threshold:.4f}"
                )

        return is_anomaly, confidence_score, anomaly_type_description
