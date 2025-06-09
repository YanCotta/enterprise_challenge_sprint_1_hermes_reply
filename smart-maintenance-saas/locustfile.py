"""
Load testing script for Smart Maintenance SaaS API using Locust.

This script defines two user behaviors:
1. SensorIngestionUser - High-frequency sensor data ingestion (weight=3)
2. ReportRequestUser - Lower-frequency report generation requests (weight=1)

Usage:
    locust -f locustfile.py --host=http://localhost:8000

The script dynamically generates realistic sensor data and report requests,
providing comprehensive load testing for the database-integrated API.
"""

import random
import uuid
from datetime import datetime, timedelta
from locust import HttpUser, task, between
from typing import Dict, Any


class SensorIngestionUser(HttpUser):
    """
    High-volume user simulating continuous sensor data ingestion.
    
    This user represents IoT sensors continuously sending readings
    to the maintenance system. Weight=3 means this behavior is 3x
    more likely to be executed than ReportRequestUser.
    """
    
    weight = 3
    wait_time = between(0.5, 2.0)  # Wait 0.5-2 seconds between requests
    
    def on_start(self):
        """Initialize user-specific sensor configurations."""
        self.sensor_types = ["temperature", "vibration", "pressure"]
        self.sensor_units = {
            "temperature": "°C",
            "vibration": "mm/s", 
            "pressure": "hPa"
        }
        # Generate 5-10 unique sensor IDs for this user
        self.sensor_ids = [f"sensor_{self.sensor_type}_{i:03d}" 
                          for i in range(random.randint(5, 10))
                          for self.sensor_type in self.sensor_types]
        
    def _generate_sensor_reading(self) -> Dict[str, Any]:
        """Generate a realistic sensor reading payload."""
        sensor_id = random.choice(self.sensor_ids)
        sensor_type = random.choice(self.sensor_types)
        
        # Generate realistic values based on sensor type
        if sensor_type == "temperature":
            value = round(random.normalvariate(25.0, 3.0), 2)  # Normal around 25°C
        elif sensor_type == "vibration":
            value = round(random.gammavariate(2, 0.05), 3)  # Low positive values
        else:  # pressure
            value = round(random.normalvariate(1013.25, 10.0), 2)  # Atmospheric pressure
            
        return {
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "value": value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "unit": self.sensor_units[sensor_type],
            "quality": round(random.uniform(0.85, 1.0), 3),
            "correlation_id": str(uuid.uuid4()),
            "metadata": {
                "location": random.choice(["factory_floor", "warehouse", "office"]),
                "device_model": f"Model_{random.choice(['A', 'B', 'C'])}{random.randint(100, 999)}"
            }
        }
    
    @task(10)
    def ingest_normal_sensor_data(self):
        """Send normal sensor reading to ingestion endpoint."""
        payload = self._generate_sensor_reading()
        
        with self.client.post(
            "/api/v1/data/ingest",
            headers={"X-API-Key": "your_default_api_key"},
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Ingestion failed: {response.status_code} - {response.text}")
    
    @task(2)
    def ingest_anomalous_sensor_data(self):
        """Send anomalous sensor reading to test anomaly detection under load."""
        payload = self._generate_sensor_reading()
        
        # Introduce anomalies to test detection performance
        anomaly_type = random.choice(["spike", "drift", "stuck"])
        if anomaly_type == "spike":
            payload["value"] *= random.uniform(3.0, 5.0)  # Spike anomaly
        elif anomaly_type == "drift":
            payload["value"] += payload["value"] * 0.8  # Drift anomaly
        else:  # stuck
            payload["value"] = 0.0  # Stuck at zero
            
        payload["metadata"]["anomaly_injected"] = anomaly_type
        
        with self.client.post(
            "/api/v1/data/ingest",
            headers={"X-API-Key": "your_default_api_key"},
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Anomaly ingestion failed: {response.status_code} - {response.text}")


class ReportRequestUser(HttpUser):
    """
    Lower-volume user simulating report generation requests.
    
    This user represents maintenance managers and analysts requesting
    various types of reports from the system. Weight=1 means this
    behavior is less frequent than sensor ingestion.
    """
    
    weight = 1
    wait_time = between(5.0, 15.0)  # Wait 5-15 seconds between requests
    
    def on_start(self):
        """Initialize report request configurations."""
        self.report_types = [
            "anomaly_summary",
            "maintenance_overview", 
            "system_health",
            "sensor_performance",
            "predictive_insights"
        ]
        self.report_formats = ["json", "text"]
        
    def _generate_report_request(self) -> Dict[str, Any]:
        """Generate a realistic report request payload."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=random.randint(1, 30))
        
        return {
            "report_type": random.choice(self.report_types),
            "format": random.choice(self.report_formats),
            "time_range_start": start_time.isoformat() + "Z",
            "time_range_end": end_time.isoformat() + "Z",
            "parameters": {
                "include_charts": random.choice([True, False]),
                "detail_level": random.choice(["summary", "detailed", "comprehensive"]),
                "sensor_filter": random.choice([None, "temperature", "vibration", "pressure"]),
                "severity_threshold": random.choice(["low", "medium", "high"]),
                "max_records": random.randint(100, 1000)
            }
        }
    
    @task(5)
    def request_anomaly_summary(self):
        """Request anomaly summary report."""
        payload = self._generate_report_request()
        payload["report_type"] = "anomaly_summary"
        
        with self.client.post(
            "/api/v1/reports/generate",
            headers={"X-API-Key": "your_default_api_key"},
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Report generation failed: {response.status_code} - {response.text}")
    
    @task(3)
    def request_system_health_report(self):
        """Request system health report."""
        payload = self._generate_report_request()
        payload["report_type"] = "system_health"
        
        with self.client.post(
            "/api/v1/reports/generate", 
            headers={"X-API-Key": "your_default_api_key"},
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health report failed: {response.status_code} - {response.text}")
    
    @task(2)
    def request_maintenance_overview(self):
        """Request maintenance overview report."""
        payload = self._generate_report_request()
        payload["report_type"] = "maintenance_overview"
        
        with self.client.post(
            "/api/v1/reports/generate",
            headers={"X-API-Key": "your_default_api_key"},
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Maintenance report failed: {response.status_code} - {response.text}")
    
    @task(1)
    def request_custom_report(self):
        """Request a custom report with varying parameters."""
        payload = self._generate_report_request()
        # Add custom parameters for stress testing
        payload["parameters"].update({
            "custom_query": f"sensor_type:{random.choice(['temperature', 'vibration', 'pressure'])}",
            "aggregation_interval": random.choice(["1h", "4h", "1d"]),
            "export_format": random.choice(["csv", "xlsx", "pdf"]),
            "notification_email": f"test_{random.randint(1, 100)}@example.com"
        })
        
        with self.client.post(
            "/api/v1/reports/generate",
            headers={"X-API-Key": "your_default_api_key"},
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Custom report failed: {response.status_code} - {response.text}")


# Load test configuration
class WebsiteUser(HttpUser):
    """
    Combined user class that inherits behaviors from both user types.
    Locust will instantiate this class and randomly choose tasks based on weights.
    """
    
    # Define the tasks from both user classes
    tasks = [SensorIngestionUser, ReportRequestUser]
    
    # Global wait time between task executions
    wait_time = between(1, 3)
    
    def on_start(self):
        """Health check on user start."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
