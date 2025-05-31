from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import uuid4, UUID
from data.agent_schemas import SensorReadingCreate, SensorReading 
from data.exceptions import DataEnrichmentException

class DataEnricher:
    def __init__(self, default_data_source_system: str = "unknown_source_system"):
        self.default_data_source_system = default_data_source_system

    def enrich(self, data_to_enrich: SensorReadingCreate, data_source_system_override: Optional[str] = None) -> SensorReading:
        current_metadata = data_to_enrich.metadata.copy() if data_to_enrich.metadata is not None else {}

        current_metadata['ingestion_timestamp_utc'] = datetime.now(timezone.utc).isoformat()

        source_system = data_source_system_override if data_source_system_override is not None else self.default_data_source_system
        current_metadata['data_source_system'] = source_system

        correlation_id_to_use = data_to_enrich.correlation_id
        if correlation_id_to_use is None:
            correlation_id_to_use = uuid4() 

        return SensorReading(
            sensor_id=data_to_enrich.sensor_id,
            value=data_to_enrich.value,
            timestamp_utc=data_to_enrich.timestamp_utc,
            metadata=current_metadata,
            correlation_id=correlation_id_to_use
        )
