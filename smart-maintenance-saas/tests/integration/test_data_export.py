"""
Integration test for data export functionality.

This test validates the incremental export feature of the sensor data
CSV export script by testing both full and incremental export modes.
"""

import asyncio
import os
import tempfile
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator

import pandas as pd
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.crud.crud_sensor_reading import crud_sensor_reading
from data.schemas import SensorReadingCreate, SensorType
from scripts.export_sensor_data_csv import export_sensor_data, get_last_exported_timestamp


class TestDataExport:
    """Test cases for the data export functionality."""

    @pytest.fixture
    async def sample_sensor_data(self, db_session: AsyncSession):
        """Create sample sensor readings for testing."""
        base_time = datetime.now(timezone.utc) - timedelta(hours=2)
        
        # Create initial sensor readings
        initial_readings = [
            SensorReadingCreate(
                sensor_id="test_sensor_001",
                value=25.5,
                timestamp=base_time,
                sensor_type=SensorType.TEMPERATURE,
                unit="celsius",
                quality=0.95,
                metadata={"location": "test_lab"}
            ),
            SensorReadingCreate(
                sensor_id="test_sensor_002", 
                value=60.0,
                timestamp=base_time + timedelta(minutes=30),
                sensor_type=SensorType.HUMIDITY,
                unit="percent",
                quality=0.98,
                metadata={"location": "test_lab"}
            )
        ]
        
        # Insert initial readings
        created_readings = []
        for reading in initial_readings:
            created = await crud_sensor_reading.create_sensor_reading(
                db_session, obj_in=reading
            )
            created_readings.append(created)
        
        # Return base time for calculating newer readings
        return {
            "initial_readings": created_readings,
            "base_time": base_time,
            "latest_time": base_time + timedelta(minutes=30)
        }

    @pytest.fixture
    def temp_csv_file(self):
        """Create a temporary CSV file for testing."""
        # Create a temporary file
        fd, temp_path = tempfile.mkstemp(suffix='.csv', prefix='test_export_')
        os.close(fd)  # Close the file descriptor, we'll open it later
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

    async def test_full_export(self, db_session: AsyncSession, sample_sensor_data, temp_csv_file):
        """Test full export functionality."""
        # Perform full export
        export_sensor_data(temp_csv_file, incremental=False)
        
        # Verify CSV file was created
        assert os.path.exists(temp_csv_file)
        
        # Read and validate CSV content
        df = pd.read_csv(temp_csv_file)
        
        # Should have header + 2 data rows
        assert len(df) == 2
        
        # Verify columns are present
        expected_columns = ["sensor_id", "sensor_type", "value", "unit", "timestamp", "quality"]
        for col in expected_columns:
            assert col in df.columns
        
        # Verify data content
        sensor_ids = df['sensor_id'].tolist()
        assert "test_sensor_001" in sensor_ids
        assert "test_sensor_002" in sensor_ids
        
        # Verify timestamp format (should be ISO format)
        timestamps = df['timestamp'].tolist()
        for ts in timestamps:
            # Should be able to parse as ISO timestamp
            datetime.fromisoformat(ts.replace('Z', '+00:00'))

    async def test_incremental_export_with_new_data(
        self, db_session: AsyncSession, sample_sensor_data, temp_csv_file
    ):
        """Test incremental export with new data added after initial export."""
        # Step 1: Perform initial full export
        export_sensor_data(temp_csv_file, incremental=False)
        
        # Verify initial export
        initial_df = pd.read_csv(temp_csv_file)
        initial_count = len(initial_df)
        assert initial_count == 2
        
        # Step 2: Add new sensor reading with more recent timestamp
        new_time = sample_sensor_data["latest_time"] + timedelta(minutes=30)
        new_reading = SensorReadingCreate(
            sensor_id="test_sensor_003",
            value=22.0,
            timestamp=new_time,
            sensor_type=SensorType.TEMPERATURE,
            unit="celsius",
            quality=0.97,
            metadata={"location": "test_lab_new"}
        )
        
        await crud_sensor_reading.create_sensor_reading(db_session, obj_in=new_reading)
        
        # Step 3: Perform incremental export
        export_sensor_data(temp_csv_file, incremental=True)
        
        # Step 4: Verify the CSV now contains all data
        final_df = pd.read_csv(temp_csv_file)
        final_count = len(final_df)
        
        # Should have original 2 + new 1 = 3 total rows
        assert final_count == 3
        
        # Verify the new sensor data is present
        sensor_ids = final_df['sensor_id'].tolist()
        assert "test_sensor_003" in sensor_ids
        
        # Verify no duplicate headers (a common issue with append mode)
        assert "sensor_id" not in final_df['sensor_id'].tolist()

    async def test_incremental_export_without_existing_file(
        self, db_session: AsyncSession, sample_sensor_data, temp_csv_file
    ):
        """Test incremental export when no existing file exists (should fallback to full export)."""
        # Ensure the file doesn't exist
        if os.path.exists(temp_csv_file):
            os.remove(temp_csv_file)
        
        # Perform incremental export on non-existent file
        export_sensor_data(temp_csv_file, incremental=True)
        
        # Should create the file with all data
        assert os.path.exists(temp_csv_file)
        
        df = pd.read_csv(temp_csv_file)
        assert len(df) == 2  # Should have both initial sensor readings
        
        # Verify it has proper headers
        expected_columns = ["sensor_id", "sensor_type", "value", "unit", "timestamp", "quality"]
        for col in expected_columns:
            assert col in df.columns

    async def test_get_last_exported_timestamp(self, temp_csv_file):
        """Test the timestamp extraction utility function."""
        # Test with non-existent file
        assert get_last_exported_timestamp("nonexistent.csv") is None
        
        # Create a test CSV with known timestamps
        test_data = {
            'sensor_id': ['sensor1', 'sensor2', 'sensor3'],
            'sensor_type': ['temperature', 'pressure', 'temperature'],
            'value': [25.0, 101.3, 26.0],
            'unit': ['celsius', 'kPa', 'celsius'],
            'timestamp': [
                '2025-08-23T10:00:00+00:00',
                '2025-08-23T11:00:00+00:00', 
                '2025-08-23T12:00:00+00:00'  # This should be the latest
            ],
            'quality': [0.95, 0.97, 0.96]
        }
        
        df = pd.DataFrame(test_data)
        df.to_csv(temp_csv_file, index=False)
        
        # Test timestamp extraction
        last_timestamp = get_last_exported_timestamp(temp_csv_file)
        assert last_timestamp == '2025-08-23T12:00:00+00:00'

    async def test_incremental_export_no_new_data(
        self, db_session: AsyncSession, sample_sensor_data, temp_csv_file
    ):
        """Test incremental export when no new data exists since last export."""
        # Perform initial full export
        export_sensor_data(temp_csv_file, incremental=False)
        
        initial_df = pd.read_csv(temp_csv_file)
        initial_count = len(initial_df)
        
        # Perform incremental export without adding new data
        export_sensor_data(temp_csv_file, incremental=True)
        
        # Should have same number of rows (no new data added)
        final_df = pd.read_csv(temp_csv_file)
        final_count = len(final_df)
        
        assert final_count == initial_count

    async def test_incremental_export_preserves_data_integrity(
        self, db_session: AsyncSession, sample_sensor_data, temp_csv_file
    ):
        """Test that incremental export preserves all data integrity."""
        # Perform full export
        export_sensor_data(temp_csv_file, incremental=False)
        full_df = pd.read_csv(temp_csv_file)
        
        # Add new data point
        new_time = sample_sensor_data["latest_time"] + timedelta(hours=1)
        new_reading = SensorReadingCreate(
            sensor_id="test_sensor_004",
            value=30.5,
            timestamp=new_time,
            sensor_type=SensorType.TEMPERATURE,
            unit="celsius",
            quality=0.99,
            metadata={"location": "test_lab_final"}
        )
        
        await crud_sensor_reading.create_sensor_reading(db_session, obj_in=new_reading)
        
        # Perform incremental export
        export_sensor_data(temp_csv_file, incremental=True)
        
        # Read final result
        incremental_df = pd.read_csv(temp_csv_file)
        
        # Verify all original data is still present
        original_sensor_ids = set(full_df['sensor_id'].tolist())
        final_sensor_ids = set(incremental_df['sensor_id'].tolist())
        
        assert original_sensor_ids.issubset(final_sensor_ids)
        
        # Verify new data is present
        assert "test_sensor_004" in final_sensor_ids
        assert len(incremental_df) == len(full_df) + 1
        
        # Verify data types and format consistency
        assert incremental_df['value'].dtype == full_df['value'].dtype
        assert incremental_df['quality'].dtype == full_df['quality'].dtype