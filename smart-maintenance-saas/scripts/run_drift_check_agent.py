#!/usr/bin/env python3
"""
Automated Drift Monitoring Agent

This script runs as a scheduled service to continuously monitor ML model drift
by making periodic API calls to the drift detection endpoint and triggering
alerts when significant drift is detected.

Features:
- Configurable drift detection schedule (daily by default)
- Multiple sensor monitoring with individual thresholds
- Redis event bus integration for drift notifications
- Slack webhook notifications for critical alerts
- Comprehensive logging with correlation IDs
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
import redis.asyncio as redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DriftDetectedEvent:
    """Event published when drift is detected"""
    def __init__(self, sensor_id: str, drift_score: float, threshold: float, 
                 timestamp: str, correlation_id: str):
        self.sensor_id = sensor_id
        self.drift_score = drift_score
        self.threshold = threshold
        self.timestamp = timestamp
        self.correlation_id = correlation_id
        self.event_type = "DriftDetectedEvent"
    
    def to_dict(self) -> Dict:
        return {
            "event_type": self.event_type,
            "sensor_id": self.sensor_id,
            "drift_score": self.drift_score,
            "threshold": self.threshold,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id
        }

class DriftCheckAgent:
    """Automated drift monitoring agent with scheduling and alerting"""
    
    def __init__(self):
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        
        # Drift detection configuration
        self.drift_threshold = float(os.getenv('DRIFT_THRESHOLD', '0.1'))
        self.window_minutes = int(os.getenv('DRIFT_WINDOW_MINUTES', '60'))
        self.min_samples = int(os.getenv('DRIFT_MIN_SAMPLES', '10'))
        
        # Monitoring configuration
        self.sensors_to_monitor = self._parse_sensor_list()
        self.check_schedule = os.getenv('DRIFT_CHECK_SCHEDULE', '0 9 * * *')  # Daily at 9 AM
        
        # Initialize components
        self.scheduler = AsyncIOScheduler()
        self.redis_client = None
        self.session = None
        
    def _parse_sensor_list(self) -> List[str]:
        """Parse sensor list from environment variable"""
        sensor_list = os.getenv('SENSORS_TO_MONITOR', 'sensor-001,sensor-002,sensor-003')
        return [s.strip() for s in sensor_list.split(',') if s.strip()]
    
    async def start(self):
        """Initialize and start the drift monitoring agent"""
        logger.info("Starting Drift Check Agent...")
        
        # Initialize Redis connection
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None
        
        # Initialize HTTP session
        self.session = aiohttp.ClientSession()
        
        # Schedule drift checks
        self.scheduler.add_job(
            self.run_drift_checks,
            CronTrigger.from_crontab(self.check_schedule),
            id='drift_check_job',
            name='Automated Drift Detection',
            max_instances=1
        )
        
        logger.info(f"📅 Scheduled drift checks: {self.check_schedule}")
        logger.info(f"🎯 Monitoring sensors: {self.sensors_to_monitor}")
        logger.info(f"⚠️  Drift threshold: {self.drift_threshold}")
        
        # Start scheduler
        self.scheduler.start()
        logger.info("🚀 Drift Check Agent started successfully")
        
        # Manual drift check on startup for testing
        if os.getenv('RUN_STARTUP_CHECK', 'false').lower() == 'true':
            logger.info("🔍 Running startup drift check...")
            await self.run_drift_checks()
    
    async def run_drift_checks(self):
        """Execute drift detection checks for all monitored sensors"""
        correlation_id = str(uuid.uuid4())
        logger.info(f"🔍 Starting drift detection cycle [correlation_id={correlation_id}]")
        
        drift_detected_count = 0
        
        for sensor_id in self.sensors_to_monitor:
            try:
                drift_result = await self.check_sensor_drift(sensor_id, correlation_id)
                
                if drift_result and drift_result.get('drift_detected', False):
                    drift_detected_count += 1
                    await self.handle_drift_detection(sensor_id, drift_result, correlation_id)
                else:
                    logger.info(f"✅ No drift detected for sensor {sensor_id}")
                    
            except Exception as e:
                logger.error(f"❌ Error checking drift for sensor {sensor_id}: {e}")
        
        logger.info(f"📊 Drift detection cycle complete: {drift_detected_count}/{len(self.sensors_to_monitor)} sensors show drift [correlation_id={correlation_id}]")
    
    async def check_sensor_drift(self, sensor_id: str, correlation_id: str) -> Optional[Dict]:
        """Check drift for a specific sensor using the API endpoint"""
        if not self.session:
            logger.error("HTTP session not initialized")
            return None
        
        payload = {
            "sensor_id": sensor_id,
            "window_minutes": self.window_minutes,
            "p_value_threshold": self.drift_threshold,
            "min_samples": self.min_samples
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-Request-ID': correlation_id
        }
        
        try:
            async with self.session.post(
                f"{self.api_base_url}/api/v1/ml/check_drift",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"🔍 Drift check for {sensor_id}: p_value={result.get('p_value', 'N/A')}, drift={result.get('drift_detected', False)}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Drift API error for {sensor_id}: {response.status} - {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error(f"⏰ Timeout checking drift for sensor {sensor_id}")
            return None
        except Exception as e:
            logger.error(f"❌ Exception checking drift for {sensor_id}: {e}")
            return None
    
    async def handle_drift_detection(self, sensor_id: str, drift_result: Dict, correlation_id: str):
        """Handle drift detection by publishing events and sending notifications"""
        drift_score = drift_result.get('p_value', 0.0)
        ks_statistic = drift_result.get('ks_statistic', 0.0)
        
        logger.warning(f"⚠️  DRIFT DETECTED! Sensor: {sensor_id}, P-value: {drift_score}, KS: {ks_statistic}")
        
        # Create drift event
        drift_event = DriftDetectedEvent(
            sensor_id=sensor_id,
            drift_score=drift_score,
            threshold=self.drift_threshold,
            timestamp=datetime.utcnow().isoformat(),
            correlation_id=correlation_id
        )
        
        # Publish to Redis event bus
        await self.publish_drift_event(drift_event)
        
        # Send Slack notification if configured
        if self.slack_webhook_url:
            await self.send_slack_notification(drift_event, drift_result)
    
    async def publish_drift_event(self, event: DriftDetectedEvent):
        """Publish drift event to Redis event bus"""
        if not self.redis_client:
            logger.warning("📡 Redis not available - skipping event publication")
            return
        
        try:
            event_data = json.dumps(event.to_dict())
            await self.redis_client.publish('drift_events', event_data)
            logger.info(f"📡 Published DriftDetectedEvent for sensor {event.sensor_id} [correlation_id={event.correlation_id}]")
        except Exception as e:
            logger.error(f"❌ Failed to publish drift event: {e}")
    
    async def send_slack_notification(self, event: DriftDetectedEvent, drift_result: Dict):
        """Send Slack notification for drift detection"""
        try:
            message = {
                "text": "🚨 ML Model Drift Detected",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*🚨 ML Model Drift Alert*\n\n*Sensor:* {event.sensor_id}\n*P-value:* {event.drift_score:.6f}\n*Threshold:* {event.threshold}\n*KS Statistic:* {drift_result.get('ks_statistic', 'N/A')}\n*Timestamp:* {event.timestamp}\n\n*Action Required:* Model retraining recommended"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Correlation ID:* `{event.correlation_id}`"
                        }
                    }
                ]
            }
            
            async with self.session.post(
                self.slack_webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    logger.info(f"📱 Slack notification sent for sensor {event.sensor_id}")
                else:
                    logger.error(f"❌ Slack notification failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ Slack notification error: {e}")
    
    async def stop(self):
        """Gracefully stop the drift monitoring agent"""
        logger.info("🛑 Stopping Drift Check Agent...")
        
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
        
        if self.session:
            await self.session.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("✅ Drift Check Agent stopped")

async def main():
    """Main entry point for the drift monitoring agent"""
    agent = DriftCheckAgent()
    
    try:
        await agent.start()
        
        # Keep running until interrupted
        logger.info("⏳ Agent running... Press Ctrl+C to stop")
        while True:
            await asyncio.sleep(60)  # Check every minute if we should continue
            
    except KeyboardInterrupt:
        logger.info("🔄 Received shutdown signal")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())