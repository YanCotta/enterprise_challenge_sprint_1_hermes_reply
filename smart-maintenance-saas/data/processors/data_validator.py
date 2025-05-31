import logging
from typing import Dict, Any # Keep this for raw_data type hint

from pydantic import ValidationError
from data.schemas import SensorReadingCreate # Corrected import path


logger = logging.getLogger(__name__)

class DataValidator:
    """
    Validates raw sensor data using the SensorReadingCreate Pydantic model.
    """

    def __init__(self):
        """
        Initializes the DataValidator.
        Validation is now based on the SensorReadingCreate Pydantic model.
        """
        logger.info("DataValidator initialized, using Pydantic model SensorReadingCreate for validation.")

    def validate(self, raw_data: Dict[str, Any]) -> SensorReadingCreate:
        """
        Validates the raw_data against the SensorReadingCreate Pydantic model.

        Args:
            raw_data (Dict[str, Any]): The raw data to validate.

        Returns:
            SensorReadingCreate: The validated data as a SensorReadingCreate instance.

        Raises:
            pydantic.ValidationError: If validation fails based on the SensorReadingCreate model.
        """
        try:
            validated_data = SensorReadingCreate(**raw_data)
            logger.debug(f"Data validation successful for data: {raw_data}")
            return validated_data
        except ValidationError:
            # Log the error and re-raise to allow upstream handling
            logger.warning(f"Pydantic validation failed for data: {raw_data}", exc_info=True)
            raise
