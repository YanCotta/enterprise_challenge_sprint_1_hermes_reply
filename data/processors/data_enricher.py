from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import uuid4, UUID
from data.schemas import SensorReadingCreate, SensorReading
from data.exceptions import DataEnrichmentException # Ensure this is used if needed

class DataEnricher:
    def __init__(self, default_data_source_system: str = "unknown_source_system"):
        self.default_data_source_system = default_data_source_system

    def enrich(self, data_to_enrich: SensorReadingCreate, data_source_system_override: Optional[str] = None) -> SensorReading:
        # Ensure metadata exists and is a copy, using default_factory from Pydantic model if data_to_enrich.metadata is None
        current_metadata = data_to_enrich.metadata.copy() if data_to_enrich.metadata is not None else {}

        current_metadata['ingestion_timestamp_utc'] = datetime.now(timezone.utc).isoformat()

        source_system = data_source_system_override if data_source_system_override is not None else self.default_data_source_system
        current_metadata['data_source_system'] = source_system

        # Ensure correlation_id is handled: use existing, or generate new if None
        correlation_id_to_use = data_to_enrich.correlation_id
        if correlation_id_to_use is None:
            # The previous agent implementation's enricher generated a uuid4 if correlation_id was None.
            # The SensorReading schema itself has Optional[UUID]=None, but the agent might expect one.
            # For consistency with previous DAQ agent logic, let's ensure one is generated if not present.
            # However, the SensorReadingCreate now has it as optional, so if the validator passed it as None,
            # this enricher should probably respect that unless specifically told to generate.
            # The DAQ agent itself ensures correlation_id on the SensorReadingCreate from the event.
            # Let's simplify: the enricher just passes through correlation_id from SensorReadingCreate.
            # The DAQ agent is responsible for ensuring SensorReadingCreate has one if the event had one.
            # The SensorReading schema itself allows correlation_id to be None.
            correlation_id_to_use = uuid4() # Generate a new UUID if correlation_id is None

        return SensorReading(
            sensor_id=data_to_enrich.sensor_id,
            value=data_to_enrich.value,
            timestamp_utc=data_to_enrich.timestamp_utc,
            metadata=current_metadata,
            correlation_id=correlation_id_to_use
        )
