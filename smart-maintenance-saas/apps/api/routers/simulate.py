"""
Live Demo Simulator API Router

This router provides endpoints for simulating various system events
to demonstrate the Smart Maintenance SaaS capabilities in real-time.
"""

import asyncio
import logging
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
import requests
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from core.database.session import AsyncSessionLocal
from core.database.crud.crud_sensor_reading import CRUDSensorReading
from data.schemas import SensorReadingCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/simulate", tags=["simulation"])


class SimulationResponse(BaseModel):
    """Response model for simulation endpoints"""
    status: str
    message: str
    simulation_id: str
    events_generated: int
    correlation_id: str


class DriftSimulationRequest(BaseModel):
    """Request model for drift event simulation"""
    sensor_id: Optional[str] = Field(default="demo-sensor-001", description="Sensor ID to simulate drift for")
    drift_magnitude: Optional[float] = Field(default=2.0, description="Magnitude of drift (standard deviations)")
    num_samples: Optional[int] = Field(default=50, description="Number of drift samples to generate")
    base_value: Optional[float] = Field(default=25.0, description="Base sensor value")
    noise_level: Optional[float] = Field(default=1.0, description="Noise level for synthetic data")


@router.post("/drift-event", response_model=SimulationResponse)
async def simulate_drift_event(
    request: DriftSimulationRequest,
    background_tasks: BackgroundTasks
) -> SimulationResponse:
    """
    Simulate a model drift event by generating synthetic sensor data with clear drift.
    
    This endpoint generates synthetic sensor data that exhibits statistical drift
    and injects it into the system via the ingestion API. This demonstrates
    the complete MLOps loop: data ingestion → drift detection → alerting → retraining.
    """
    simulation_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    
    logger.info(f"🎭 Starting drift simulation for sensor {request.sensor_id} [simulation_id={simulation_id}]")
    
    try:
        # Generate synthetic data with drift
        synthetic_data = generate_drift_data(
            sensor_id=request.sensor_id,
            drift_magnitude=request.drift_magnitude,
            num_samples=request.num_samples,
            base_value=request.base_value,
            noise_level=request.noise_level
        )
        
        # Schedule background ingestion of synthetic data
        background_tasks.add_task(
            ingest_synthetic_data,
            synthetic_data,
            correlation_id,
            simulation_id
        )
        
        logger.info(f"✅ Drift simulation initiated: {len(synthetic_data)} samples generated [simulation_id={simulation_id}]")
        
        return SimulationResponse(
            status="success",
            message=f"Drift simulation started for sensor {request.sensor_id}. Generated {len(synthetic_data)} samples with {request.drift_magnitude}σ drift.",
            simulation_id=simulation_id,
            events_generated=len(synthetic_data),
            correlation_id=correlation_id
        )
        
    except Exception as e:
        logger.error(f"❌ Drift simulation failed: {e} [simulation_id={simulation_id}]")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.post("/anomaly-event", response_model=SimulationResponse)
async def simulate_anomaly_event(
    background_tasks: BackgroundTasks,
    sensor_id: str = "demo-sensor-002",
    anomaly_magnitude: float = 5.0,
    num_anomalies: int = 10
) -> SimulationResponse:
    """
    Simulate anomalous sensor readings to demonstrate anomaly detection capabilities.
    
    This endpoint generates synthetic sensor data with clear anomalies
    and injects it into the system to trigger anomaly detection alerts.
    """
    simulation_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    
    logger.info(f"🚨 Starting anomaly simulation for sensor {sensor_id} [simulation_id={simulation_id}]")
    
    try:
        # Generate synthetic data with anomalies
        synthetic_data = generate_anomaly_data(
            sensor_id=sensor_id,
            anomaly_magnitude=anomaly_magnitude,
            num_anomalies=num_anomalies
        )
        
        # Schedule background ingestion of synthetic data
        background_tasks.add_task(
            ingest_synthetic_data,
            synthetic_data,
            correlation_id,
            simulation_id
        )
        
        logger.info(f"✅ Anomaly simulation initiated: {len(synthetic_data)} samples generated [simulation_id={simulation_id}]")
        
        return SimulationResponse(
            status="success",
            message=f"Anomaly simulation started for sensor {sensor_id}. Generated {num_anomalies} anomalies.",
            simulation_id=simulation_id,
            events_generated=len(synthetic_data),
            correlation_id=correlation_id
        )
        
    except Exception as e:
        logger.error(f"❌ Anomaly simulation failed: {e} [simulation_id={simulation_id}]")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.post("/normal-data", response_model=SimulationResponse)
async def simulate_normal_data(
    background_tasks: BackgroundTasks,
    sensor_id: str = "demo-sensor-003",
    num_samples: int = 100,
    duration_minutes: int = 60
) -> SimulationResponse:
    """
    Simulate normal sensor operation to populate the system with baseline data.
    
    This endpoint generates realistic sensor data that follows normal patterns
    to establish baseline behavior for comparison with drift and anomalies.
    """
    simulation_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    
    logger.info(f"📊 Starting normal data simulation for sensor {sensor_id} [simulation_id={simulation_id}]")
    
    try:
        # Generate normal synthetic data
        synthetic_data = generate_normal_data(
            sensor_id=sensor_id,
            num_samples=num_samples,
            duration_minutes=duration_minutes
        )
        
        # Schedule background ingestion of synthetic data
        background_tasks.add_task(
            ingest_synthetic_data,
            synthetic_data,
            correlation_id,
            simulation_id
        )
        
        logger.info(f"✅ Normal data simulation initiated: {len(synthetic_data)} samples generated [simulation_id={simulation_id}]")
        
        return SimulationResponse(
            status="success",
            message=f"Normal data simulation started for sensor {sensor_id}. Generated {len(synthetic_data)} samples over {duration_minutes} minutes.",
            simulation_id=simulation_id,
            events_generated=len(synthetic_data),
            correlation_id=correlation_id
        )
        
    except Exception as e:
        logger.error(f"❌ Normal data simulation failed: {e} [simulation_id={simulation_id}]")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


def generate_drift_data(
    sensor_id: str,
    drift_magnitude: float,
    num_samples: int,
    base_value: float,
    noise_level: float
) -> List[Dict]:
    """
    Generate synthetic sensor data with statistical drift.
    
    The data starts with normal values and gradually shifts to exhibit clear drift
    that should be detectable by statistical tests like Kolmogorov-Smirnov.
    """
    np.random.seed(42)  # For reproducible demos
    
    data = []
    now = datetime.utcnow()
    
    for i in range(num_samples):
        # Create gradual drift: starts normal, becomes increasingly shifted
        drift_factor = (i / num_samples) * drift_magnitude
        
        # Generate value with drift and noise
        value = base_value + drift_factor + np.random.normal(0, noise_level)
        
        # Ensure realistic sensor bounds
        value = max(0, min(100, value))
        
        # Create timestamp (spaced 1 minute apart for recent data)
        timestamp = now - timedelta(minutes=num_samples - i)
        
        reading = {
            "sensor_id": sensor_id,
            "sensor_type": "temperature",
            "value": round(value, 2),
            "unit": "celsius",
            "timestamp": timestamp.isoformat() + "Z",
            "location": "Demo Zone",
            "metadata": {
                "simulation": True,
                "drift_simulation": True,
                "drift_magnitude": drift_magnitude,
                "sample_index": i
            }
        }
        data.append(reading)
    
    return data


def generate_anomaly_data(
    sensor_id: str,
    anomaly_magnitude: float,
    num_anomalies: int
) -> List[Dict]:
    """
    Generate synthetic sensor data with clear anomalies.
    
    Creates a mix of normal readings and obvious anomalies that should
    trigger anomaly detection algorithms.
    """
    np.random.seed(123)  # Different seed for anomaly data
    
    data = []
    now = datetime.utcnow()
    
    # Generate more normal data than anomalies for realistic ratio
    total_samples = num_anomalies * 5  # 20% anomalies
    anomaly_indices = np.random.choice(total_samples, size=num_anomalies, replace=False)
    
    for i in range(total_samples):
        if i in anomaly_indices:
            # Generate anomalous value
            base_value = 25.0
            if np.random.random() > 0.5:
                value = base_value + anomaly_magnitude * np.random.uniform(3, 5)  # High anomaly
            else:
                value = base_value - anomaly_magnitude * np.random.uniform(2, 3)  # Low anomaly
            is_anomaly = True
        else:
            # Generate normal value
            value = np.random.normal(25.0, 1.0)  # Normal temperature
            is_anomaly = False
        
        # Ensure realistic bounds
        value = max(-10, min(60, value))
        
        # Create timestamp
        timestamp = now - timedelta(minutes=total_samples - i)
        
        reading = {
            "sensor_id": sensor_id,
            "sensor_type": "temperature",
            "value": round(value, 2),
            "unit": "celsius",
            "timestamp": timestamp.isoformat() + "Z",
            "location": "Demo Zone",
            "metadata": {
                "simulation": True,
                "anomaly_simulation": True,
                "is_anomaly": is_anomaly,
                "sample_index": i
            }
        }
        data.append(reading)
    
    return data


def generate_normal_data(
    sensor_id: str,
    num_samples: int,
    duration_minutes: int
) -> List[Dict]:
    """
    Generate normal synthetic sensor data for baseline establishment.
    
    Creates realistic sensor readings that follow normal patterns
    with typical noise and variations.
    """
    np.random.seed(456)  # Another seed for normal data
    
    data = []
    now = datetime.utcnow()
    
    # Create time intervals
    time_intervals = np.linspace(0, duration_minutes, num_samples)
    
    for i, time_offset in enumerate(time_intervals):
        # Generate realistic temperature with daily variation
        hour_of_day = ((now - timedelta(minutes=duration_minutes - time_offset)).hour) % 24
        daily_variation = 3 * np.sin(2 * np.pi * hour_of_day / 24)  # Simple daily cycle
        
        base_value = 23.0 + daily_variation  # Temperature with daily cycle
        noise = np.random.normal(0, 0.5)  # Small amount of noise
        value = base_value + noise
        
        # Ensure realistic bounds
        value = max(15, min(35, value))
        
        # Create timestamp
        timestamp = now - timedelta(minutes=duration_minutes - time_offset)
        
        reading = {
            "sensor_id": sensor_id,
            "sensor_type": "temperature",
            "value": round(value, 2),
            "unit": "celsius",
            "timestamp": timestamp.isoformat() + "Z",
            "location": "Demo Zone",
            "metadata": {
                "simulation": True,
                "normal_simulation": True,
                "daily_hour": hour_of_day,
                "sample_index": i
            }
        }
        data.append(reading)
    
    return data


async def ingest_synthetic_data(
    synthetic_data: List[Dict],
    correlation_id: str,
    simulation_id: str
):
    """
    Ingest synthetic data directly using database operations.
    
    This function runs in the background to avoid blocking the simulation response.
    It directly inserts each synthetic reading into the database, bypassing HTTP calls.
    """
    logger.info(f"📤 Starting ingestion of {len(synthetic_data)} synthetic samples [simulation_id={simulation_id}]")
    
    successful_ingestions = 0
    failed_ingestions = 0
    crud = CRUDSensorReading()
    
    async with AsyncSessionLocal() as db:
        try:
            for i, reading in enumerate(synthetic_data):
                try:
                    # Convert the dict to SensorReadingCreate schema
                    sensor_reading = SensorReadingCreate(
                        sensor_id=reading["sensor_id"],
                        value=reading["value"],
                        timestamp=datetime.fromisoformat(reading["timestamp"].replace('Z', '+00:00')),
                        sensor_type=reading.get("sensor_type"),
                        unit=reading.get("unit"),
                        metadata=reading.get("metadata", {})
                    )
                    
                    # Direct database insertion
                    await crud.create_sensor_reading(db=db, obj_in=sensor_reading)
                    successful_ingestions += 1
                    
                    if i % 10 == 0:  # Log every 10th ingestion
                        logger.debug(f"📥 Ingested sample {i+1}/{len(synthetic_data)} [simulation_id={simulation_id}]")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to ingest sample {i+1}: {e}")
                    failed_ingestions += 1
                
                # Small delay to avoid overwhelming the database
                await asyncio.sleep(0.01)
            
            # Commit all insertions
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Database transaction failed: {e}")
            raise
    
    logger.info(f"📊 Ingestion complete: {successful_ingestions} successful, {failed_ingestions} failed [simulation_id={simulation_id}]")
    
    # If we have mostly successful ingestions, wait a bit then trigger drift check
    if successful_ingestions > len(synthetic_data) * 0.8:  # 80% success rate
        logger.info(f"⏰ Waiting 30 seconds before triggering drift check [simulation_id={simulation_id}]")
        await asyncio.sleep(30)
        await trigger_drift_check(correlation_id, simulation_id)


async def trigger_drift_check(correlation_id: str, simulation_id: str):
    """
    Trigger a drift check after synthetic data ingestion.
    
    This helps demonstrate the complete MLOps loop by automatically
    checking for drift after injecting synthetic drift data.
    """
    try:
        # Use the internal API endpoint for drift check
        drift_check_url = "http://api:8000/api/v1/ml/check_drift"
        fallback_url = "http://localhost:8000/api/v1/ml/check_drift"
        
        headers = {
            "Content-Type": "application/json",
            "X-Request-ID": correlation_id,
            "X-Simulation-ID": simulation_id,
            "X-API-KEY": os.getenv("API_KEY", "")
        }
        
        # Check drift for the demo sensor
        payload = {
            "sensor_id": "demo-sensor-001",
            "window_minutes": 60,
            "p_value_threshold": 0.05,
            "min_samples": 10
        }
        
        for url in [drift_check_url, fallback_url]:
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"🔍 Triggered drift check: drift_detected={result.get('drift_detected', False)} [simulation_id={simulation_id}]")
                    break
                else:
                    logger.warning(f"⚠️  Drift check failed: HTTP {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                if url == drift_check_url:
                    continue  # Try fallback
                else:
                    raise
                    
    except Exception as e:
        logger.error(f"❌ Failed to trigger drift check: {e} [simulation_id={simulation_id}]")