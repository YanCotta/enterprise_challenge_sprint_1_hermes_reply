import uuid
from typing import Optional, Dict, Any
from pydantic import ValidationError
from data.agent_schemas import SensorReadingCreate 
from data.exceptions import DataValidationException

class DataValidator:
    def validate(self, raw_data: Dict[str, Any], correlation_id: Optional[uuid.UUID] = None) -> SensorReadingCreate:
        data_for_model = raw_data.copy()
        if 'correlation_id' not in data_for_model and correlation_id is not None:
            data_for_model['correlation_id'] = correlation_id
        elif 'correlation_id' in data_for_model and data_for_model['correlation_id'] is None and correlation_id is not None:
            data_for_model['correlation_id'] = correlation_id

        try:
            validated_data = SensorReadingCreate(**data_for_model)

            if validated_data.value is not None and validated_data.value < 0:
                raise DataValidationException(f"Sensor value cannot be negative: {validated_data.value}")
            return validated_data
        except ValidationError as e:
            raise e
        except DataValidationException as e:
            raise e
        except Exception as e:
            raise DataValidationException(f"An unexpected error occurred during validation: {str(e)}")
