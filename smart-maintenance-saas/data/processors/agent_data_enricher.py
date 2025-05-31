from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import uuid4, UUID
from data.schemas import SensorReadingCreate, SensorReading 
from data.exceptions import DataEnrichmentException

class DataEnricher:
    """
    Enriches validated sensor readings with additional metadata and required fields.
    """
    def __init__(self, default_data_source_system: str = "unknown_source_system"):
        """
        Initialize the enricher with a default data source system identifier.
        
        Args:
            default_data_source_system: Default identifier for the data source
        """
        self.default_data_source_system = default_data_source_system

    def enrich(self, data_to_enrich: SensorReadingCreate, data_source_system_override: Optional[str] = None) -> SensorReading:
        """
        Enriches a validated sensor reading with additional metadata.
        
        Args:
            data_to_enrich: Validated sensor reading data
            data_source_system_override: Optional override for the data source system
        
        Returns:
            SensorReading: Enriched sensor reading with all required fields
        """
        try:
            # Start with the base reading data
            enriched_data = data_to_enrich.model_dump()
            
            # Update metadata
            metadata = enriched_data.get('metadata', {}).copy()
            metadata['data_source_system'] = (
                data_source_system_override if data_source_system_override is not None 
                else self.default_data_source_system
            )
            
            # Create enriched reading with all required fields
            return SensorReading(
                **enriched_data,
                metadata=metadata,
                ingestion_timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            raise DataEnrichmentException(f"Failed to enrich sensor reading: {str(e)}")
