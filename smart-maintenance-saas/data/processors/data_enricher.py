import logging
from typing import Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class DataEnricher:
    """
    Enriches validated sensor data with additional information.
    """

    def __init__(self):
        """
        Initializes the DataEnricher.
        """
        logger.info("DataEnricher initialized.")

    def enrich(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriches the validated data.

        Args:
            validated_data (Dict[str, Any]): The data that has already passed validation.

        Returns:
            Dict[str, Any]: The enriched data.
        """
        if not isinstance(validated_data, dict):
            # This should ideally not happen if DataValidator is used first
            logger.error("Input data for enrichment must be a dictionary.")
            raise ValueError("Input data for enrichment must be a dictionary.")

        enriched_data = validated_data.copy()

        # 1. Add a 'processed_at' timestamp
        enriched_data['processed_at_utc'] = datetime.now(timezone.utc).isoformat()

        # 2. Example: Convert temperature if applicable
        #    This is a placeholder for more complex enrichment logic.
        #    In a real scenario, you might have specific rules based on sensor_id or data type.
        if 'value' in enriched_data and 'unit' in enriched_data:
            if isinstance(enriched_data['value'], (int, float)):
                if enriched_data['unit'].upper() == 'C':
                    # Example: add Fahrenheit if Celsius is provided
                    # enriched_data['value_fahrenheit'] = (validated_data['value'] * 9/5) + 32
                    pass # Placeholder for now
                elif enriched_data['unit'].upper() == 'F':
                    # Example: add Celsius if Fahrenheit is provided
                    # enriched_data['value_celsius'] = (validated_data['value'] - 32) * 5/9
                    pass # Placeholder for now

        # 3. Example: Add a flag or category based on value
        # if 'value' in enriched_data and isinstance(enriched_data['value'], (int, float)):
        #     if enriched_data['value'] > 100: # Some arbitrary threshold
        #         enriched_data['value_category'] = 'high'
        #     elif enriched_data['value'] < 0:
        #         enriched_data['value_category'] = 'low'
        #     else:
        #         enriched_data['value_category'] = 'normal'

        logger.debug(f"Data enrichment successful. Added fields: 'processed_at_utc'. Original keys: {list(validated_data.keys())}, Enriched keys: {list(enriched_data.keys())}")
        return enriched_data

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    logging.basicConfig(level=logging.INFO)

    enricher = DataEnricher()

    sample_data_1 = {"sensor_id": "temp-001", "timestamp": 1678886400, "value": 25.5, "unit": "C"}
    sample_data_2 = {"sensor_id": "load-001", "timestamp": 1678886500, "value": {"current": 1.5, "voltage": 12.1}}
    sample_data_3 = {"sensor_id": "count-xyz", "timestamp": 1678886600, "value": 1050}


    print("Enriching data samples:")
    enriched_1 = enricher.enrich(sample_data_1)
    print(f"Original: {sample_data_1} -> Enriched: {enriched_1}")

    enriched_2 = enricher.enrich(sample_data_2)
    print(f"Original: {sample_data_2} -> Enriched: {enriched_2}")

    enriched_3 = enricher.enrich(sample_data_3)
    print(f"Original: {sample_data_3} -> Enriched: {enriched_3}")

    # Example of how it might be used with a validator
    # from data_validator import DataValidator # Assuming data_validator.py is in the same directory for this test
    # validator = DataValidator()
    # test_valid_data = {"sensor_id": "test-007", "timestamp": 1678886400, "value": "active"}
    # try:
    #     if validator.validate(test_valid_data):
    #         enriched_validated = enricher.enrich(test_valid_data)
    #         print(f"Validated and Enriched: {enriched_validated}")
    # except ValueError as e:
    #     print(f"Validation failed: {e}")
