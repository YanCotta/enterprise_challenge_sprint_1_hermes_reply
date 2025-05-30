import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DataValidator:
    """
    Validates raw sensor data against a predefined schema.
    """

    def __init__(self, schema: Dict[str, Any] = None):
        """
        Initializes the DataValidator.

        Args:
            schema (Dict[str, Any], optional): A dictionary defining the expected schema.
                                               Keys are field names, values can be types or specific checks.
                                               If None, a default schema will be used.
        """
        if schema is None:
            self.schema = {
                "sensor_id": {"type": str, "required": True},
                "timestamp": {"type": (int, float), "required": True}, # Allow int or float for timestamp
                "value": {"type": (int, float, str, dict, list), "required": True}, # Value can be various types
                # Optional fields can be defined without "required": True
                "unit": {"type": str, "required": False},
                "location": {"type": str, "required": False}
            }
            logger.info("DataValidator initialized with default schema.")
        else:
            self.schema = schema
            logger.info(f"DataValidator initialized with provided schema: {schema}")

    def validate(self, raw_data: Dict[str, Any]) -> bool:
        """
        Validates the raw_data against the schema.

        Args:
            raw_data (Dict[str, Any]): The raw data to validate.

        Returns:
            bool: True if the data is valid, False otherwise.

        Raises:
            ValueError: If validation fails, detailing the reason.
        """
        if not isinstance(raw_data, dict):
            raise ValueError("Input data must be a dictionary.")

        for field_name, rules in self.schema.items():
            is_required = rules.get("required", False)
            field_type = rules.get("type")

            if is_required and field_name not in raw_data:
                msg = f"Missing required field: '{field_name}'"
                logger.warning(msg)
                raise ValueError(msg)

            if field_name in raw_data:
                value = raw_data[field_name]
                if field_type and not isinstance(value, field_type):
                    msg = f"Invalid type for field '{field_name}'. Expected {field_type}, got {type(value)}."
                    logger.warning(msg)
                    raise ValueError(msg)

                # Add more specific validation rules here if needed
                # For example, check ranges, patterns, etc.

        # Check for unexpected fields (optional, depending on strictness)
        # for field_name in raw_data:
        #     if field_name not in self.schema:
        #         logger.warning(f"Unexpected field: '{field_name}' in raw_data.")

        logger.debug(f"Data validation successful for data (keys: {list(raw_data.keys())}).")
        return True

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    logging.basicConfig(level=logging.INFO)

    validator = DataValidator()

    valid_data_1 = {"sensor_id": "temp-001", "timestamp": 1678886400, "value": 25.5}
    valid_data_2 = {"sensor_id": "humid-002", "timestamp": 1678886400.500, "value": 60, "unit": "%RH"}
    valid_data_3 = {"sensor_id": "volt-003", "timestamp": 1678886500, "value": {"current": 1.5, "voltage": 12.1}, "location": "panel_A"}


    invalid_data_1 = {"sensor_id": "temp-001", "value": 25.5} # Missing timestamp
    invalid_data_2 = {"sensor_id": 123, "timestamp": 1678886400, "value": 25.5} # Invalid sensor_id type
    invalid_data_3 = {"sensor_id": "temp-001", "timestamp": "not_a_timestamp", "value": 25.5} # Invalid timestamp type

    print("Validating data samples:")
    try:
        print(f"Validating: {valid_data_1} -> {validator.validate(valid_data_1)}")
        print(f"Validating: {valid_data_2} -> {validator.validate(valid_data_2)}")
        print(f"Validating: {valid_data_3} -> {validator.validate(valid_data_3)}")
    except ValueError as e:
        print(f"Error validating valid data: {e}")

    print("\nValidating invalid data samples (expecting ValueErrors):")
    for i, data in enumerate([invalid_data_1, invalid_data_2, invalid_data_3]):
        try:
            validator.validate(data)
            print(f"Validation unexpectedly passed for invalid_data_{i+1}")
        except ValueError as e:
            print(f"Correctly caught ValueError for invalid_data_{i+1}: {e}")

    # Example with a custom schema
    custom_schema = {
        "event_name": {"type": str, "required": True},
        "payload": {"type": dict, "required": True},
        "priority": {"type": int, "required": False}
    }
    custom_validator = DataValidator(schema=custom_schema)
    valid_custom_data = {"event_name": "user_login", "payload": {"user_id": "xyz"}, "priority": 1}
    invalid_custom_data = {"event_name": "user_logout"} # Missing payload

    print("\nValidating with custom schema:")
    try:
        print(f"Validating: {valid_custom_data} -> {custom_validator.validate(valid_custom_data)}")
    except ValueError as e:
        print(f"Error validating custom data: {e}")

    try:
        custom_validator.validate(invalid_custom_data)
        print(f"Validation unexpectedly passed for invalid_custom_data")
    except ValueError as e:
        print(f"Correctly caught ValueError for invalid_custom_data: {e}")
