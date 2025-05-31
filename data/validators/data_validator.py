import uuid
from typing import Optional, Dict, Any
from pydantic import ValidationError
from data.schemas import SensorReadingCreate
from data.exceptions import DataValidationException

class DataValidator:
    def validate(self, raw_data: Dict[str, Any], correlation_id: Optional[uuid.UUID] = None) -> SensorReadingCreate:
        data_for_model = raw_data.copy()
        # Ensure correlation_id from the event is used if not in raw_data
        if 'correlation_id' not in data_for_model and correlation_id is not None:
            data_for_model['correlation_id'] = correlation_id
        elif 'correlation_id' in data_for_model and data_for_model['correlation_id'] is None and correlation_id is not None:
            # If raw_data explicitly has None but event has one, prefer event's
            data_for_model['correlation_id'] = correlation_id

        try:
            # This is where Pydantic validation happens
            validated_data = SensorReadingCreate(**data_for_model)

            # Custom validation rule
            if validated_data.value is not None and validated_data.value < 0:
                # This will be caught by the agent's DataValidationException handler
                raise DataValidationException(f"Sensor value cannot be negative: {validated_data.value}")
            return validated_data
        except ValidationError as e:
            # Re-raise Pydantic's ValidationError to be caught by the agent
            raise e
        except DataValidationException as e:
            # Re-raise custom DataValidationException
            raise e
        except Exception as e:
            # Catch any other unexpected error during validation and wrap it
            # This helps in not exposing raw exceptions if not desired
            raise DataValidationException(f"An unexpected error occurred during validation: {str(e)}")
