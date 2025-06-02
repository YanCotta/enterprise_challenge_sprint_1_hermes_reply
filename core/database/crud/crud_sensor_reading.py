from typing import List, Optional, Any
from datetime import datetime, timedelta
import logging

# Assuming SensorReading model is defined in core.models.data_models
# from core.models.data_models import SensorReading
# For now, we'll define a placeholder if the import above is an issue during standalone execution
try:
    from core.models.data_models import SensorReading
except ImportError:
    # Placeholder for SensorReading if core.models.data_models is not found
    # This is for testing this CRUD file in isolation, actual system should find the import
    logging.warning(
        "CRUDSensorReading: core.models.data_models.SensorReading not found. Using placeholder."
    )

    class SensorReading:
        def __init__(
            self,
            sensor_id: str,
            timestamp: datetime,
            value: Any,
            sensor_type: str,
            unit: Optional[str] = None,
            quality: float = 1.0,
        ):
            self.sensor_id = sensor_id
            self.timestamp = timestamp
            self.value = value
            self.sensor_type = sensor_type
            self.unit = unit
            self.quality = quality

        def model_dump(self):  # Pydantic v2 uses model_dump, v1 used dict()
            return self.__dict__


class CRUDSensorReading:
    """
    Placeholder CRUD operations for SensorReadings.
    In a real application, this would interact with a database.
    """

    def __init__(
        self, db_session: Optional[Any] = None
    ):  # db_session could be SQLAlchemy session, DB connection, etc.
        self.logger = logging.getLogger(__name__)
        self._db_session = db_session  # Not used in this placeholder, but shows intent

        # Initialize with some dummy historical data for testing
        self._dummy_data: List[SensorReading] = []
        self._populate_dummy_data()

    def _populate_dummy_data(self):
        now = datetime.utcnow()
        sensor_ids = ["temp_sensor_001", "pressure_sensor_002", "vibration_sensor_003"]
        sensor_types_map = {
            "temp_sensor_001": (
                "TEMPERATURE",
                "°C",
                (15, 30),
            ),  # type, unit, (min_val, max_val) for dummy data
            "pressure_sensor_002": ("PRESSURE", "PSI", (1000, 1020)),
            "vibration_sensor_003": ("VIBRATION", "mm/s", (0.1, 2.0)),
        }

        for sensor_id in sensor_ids:
            stype, sunit, (smin, smax) = sensor_types_map[sensor_id]
            # Generate 100 readings for each sensor, one every hour for the past 100 hours
            for i in range(100):
                ts = now - timedelta(hours=i)
                # Simple value generation, could be more complex (e.g. random walk)
                val = smin + ((i % 10) / 10.0) * (smax - smin)  # Creates some pattern
                if (
                    sensor_id == "temp_sensor_001" and i % 20 == 0
                ):  # Introduce some occasional 'anomalies'
                    val *= 1.5

                self._dummy_data.append(
                    SensorReading(
                        sensor_id=sensor_id,
                        timestamp=ts,
                        value=val,
                        sensor_type=stype,
                        unit=sunit,
                        quality=0.9 if i % 10 != 0 else 0.6,  # Occasional poor quality
                    )
                )
        # Sort data by timestamp descending (as if fetched from DB with ORDER BY timestamp DESC)
        self._dummy_data.sort(key=lambda r: r.timestamp, reverse=True)
        self.logger.info(
            f"CRUDSensorReading initialized with {len(self._dummy_data)} dummy readings."
        )

    async def get_sensor_readings_by_sensor_id(
        self,
        sensor_id: str,
        limit: int = 20,
        before_timestamp: Optional[datetime] = None,
        after_timestamp: Optional[datetime] = None,  # New parameter
    ) -> List[SensorReading]:
        """
        Fetches sensor readings for a given sensor_id, sorted by timestamp descending.
        Can filter by timestamps.
        """
        self.logger.debug(
            f"Fetching up to {limit} readings for sensor '{sensor_id}' before {before_timestamp} and after {after_timestamp}"
        )

        results = []
        for reading in self._dummy_data:
            if reading.sensor_id == sensor_id:
                if before_timestamp and reading.timestamp >= before_timestamp:
                    continue
                if after_timestamp and reading.timestamp <= after_timestamp:
                    continue
                results.append(reading)
                if len(results) >= limit:
                    break

        self.logger.debug(
            f"Found {len(results)} readings for sensor '{sensor_id}' with given criteria."
        )
        return results

    async def get_latest_sensor_reading(
        self, sensor_id: str
    ) -> Optional[SensorReading]:
        """Fetches the most recent sensor reading for a given sensor_id."""
        self.logger.debug(f"Fetching latest reading for sensor '{sensor_id}'")
        for (
            reading
        ) in self._dummy_data:  # Assumes _dummy_data is sorted reverse chronologically
            if reading.sensor_id == sensor_id:
                return reading
        return None

    async def add_sensor_reading(self, reading: SensorReading) -> SensorReading:
        """Adds a new sensor reading. In a real DB, this would be an INSERT."""
        self.logger.debug(
            f"Adding new reading for sensor '{reading.sensor_id}' at {reading.timestamp}"
        )
        # Insert in sorted order (or append and re-sort if performance is not critical for dummy)
        self._dummy_data.append(reading)
        self._dummy_data.sort(key=lambda r: r.timestamp, reverse=True)
        return reading


# Example Usage
if __name__ == "__main__":
    import asyncio

    async def main():
        logging.basicConfig(level=logging.DEBUG)
        crud = CRUDSensorReading()

        # Test fetching
        sensor_id_to_test = "temp_sensor_001"

        print(
            f"\n--- Testing get_sensor_readings_by_sensor_id for {sensor_id_to_test} ---"
        )
        current_time = datetime.utcnow() - timedelta(
            hours=5
        )  # Simulate a point in time

        readings = await crud.get_sensor_readings_by_sensor_id(
            sensor_id=sensor_id_to_test, limit=5, before_timestamp=current_time
        )
        print(f"Found {len(readings)} readings before {current_time}:")
        for r in readings:
            print(f"  {r.timestamp} - Value: {r.value}, Quality: {r.quality}")

        print(f"\n--- Testing get_latest_sensor_reading for {sensor_id_to_test} ---")
        latest = await crud.get_latest_sensor_reading(sensor_id_to_test)
        if latest:
            print(f"  Latest: {latest.timestamp} - Value: {latest.value}")

        print(f"\n--- Testing add_sensor_reading for {sensor_id_to_test} ---")
        new_reading_val = SensorReading(
            sensor_id=sensor_id_to_test,
            timestamp=datetime.utcnow()
            + timedelta(seconds=1),  # Ensure it's the newest
            value=99.9,
            sensor_type="TEMPERATURE",
            unit="°C",
            quality=0.99,
        )
        added_reading = await crud.add_sensor_reading(new_reading_val)
        print(
            f"Added reading: {added_reading.timestamp} - Value: {added_reading.value}"
        )

        latest_after_add = await crud.get_latest_sensor_reading(sensor_id_to_test)
        if latest_after_add:
            print(
                f"  Latest after add: {latest_after_add.timestamp} - Value: {latest_after_add.value}, Expected: 99.9"
            )

    asyncio.run(main())
