import logging
import uuid
from typing import Any, Dict, Optional, Union

from pydantic import ValidationError

from data.exceptions import DataValidationException
from data.schemas import SensorReadingCreate

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validates sensor reading data against the SensorReadingCreate schema
    and performs additional business rule validations.
    """

    def __init__(self):
        """
        Initializes the DataValidator.
        """
        logger.info(
            "DataValidator initialized, using SensorReadingCreate schema for validation."
        )

    def validate(
        self, raw_data: Union[Dict[str, Any], SensorReadingCreate], correlation_id: Optional[uuid.UUID] = None
    ) -> SensorReadingCreate:
        """
        Validates raw sensor data against the SensorReadingCreate schema.

        Args:
            raw_data: Raw sensor data to validate
            correlation_id: Optional correlation ID for tracking (not part of validation)

        Returns:
            SensorReadingCreate: Validated sensor reading data

        Raises:
            ValidationError: If the data fails Pydantic validation
            DataValidationException: If the data fails business rule validation
        """
        if isinstance(raw_data, SensorReadingCreate):
            validated_data: Optional[SensorReadingCreate] = raw_data
            data_for_model = raw_data.model_dump()
        else:
            validated_data = None
            data_for_model = raw_data.copy()

        # correlation_id is tracked separately, not part of the schema validation
        logger.debug(f"Validating data with correlation_id: {correlation_id}")

        try:
            if not isinstance(raw_data, SensorReadingCreate):
                validated_data = SensorReadingCreate(**data_for_model)
            assert validated_data is not None

            if validated_data.value is not None and validated_data.value < 0:
                raise DataValidationException(
                    f"Sensor value cannot be negative: {validated_data.value}"
                )
            return validated_data
        except ValidationError as e:
            raise e
        except DataValidationException as e:
            raise e
        except Exception as e:
            raise DataValidationException(
                f"An unexpected error occurred during validation: {str(e)}"
            )
