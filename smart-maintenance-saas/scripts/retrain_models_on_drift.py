#!/usr/bin/env python3
"""
Model Retraining Hook Agent

This script acts as a Redis event consumer that listens for DriftDetectedEvent
messages and automatically triggers model retraining when significant drift
is detected.

Features:
- Redis event bus subscriber for drift events
- Automated model retraining using Makefile commands
- Configurable retraining policies and cooldown periods
- Comprehensive logging and error handling
- Integration with MLflow for model versioning
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

import redis.asyncio as redis

# Add project root to path for importing our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.notifications.email_service import email_service

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelRetrainingAgent:
    """Automated model retraining triggered by drift detection events"""
    
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.event_channel = os.getenv('DRIFT_EVENT_CHANNEL', 'drift_events')
        
        # Retraining configuration
        self.retraining_enabled = os.getenv('RETRAINING_ENABLED', 'true').lower() == 'true'
        self.cooldown_hours = int(os.getenv('RETRAINING_COOLDOWN_HOURS', '24'))
        self.max_concurrent_retraining = int(os.getenv('MAX_CONCURRENT_RETRAINING', '1'))
        
        # Model configuration
        self.models_to_retrain = self._parse_model_list()
        self.training_timeout_minutes = int(os.getenv('TRAINING_TIMEOUT_MINUTES', '60'))
        
        # State tracking
        self.last_retraining_times = {}
        self.active_retraining_jobs = set()
        
        # Initialize Redis client
        self.redis_client = None
        self.running = False
        
    def _parse_model_list(self) -> Dict[str, str]:
        """Parse model retraining configuration from environment"""
        # Default models to retrain when drift is detected
        models = {
            'anomaly': 'train-anomaly',
            'forecast': 'train-forecast'
        }
        
        # Allow override via environment variable
        model_config = os.getenv('MODELS_TO_RETRAIN', 'anomaly:train-anomaly,forecast:train-forecast')
        if model_config:
            try:
                models = {}
                for pair in model_config.split(','):
                    model_type, make_target = pair.strip().split(':')
                    models[model_type.strip()] = make_target.strip()
            except ValueError:
                logger.warning(f"Invalid MODELS_TO_RETRAIN format: {model_config}, using defaults")
        
        return models
    
    async def start(self):
        """Initialize and start the retraining agent"""
        logger.info("🤖 Starting Model Retraining Agent...")
        
        if not self.retraining_enabled:
            logger.warning("⚠️  Retraining is DISABLED by configuration")
            return
        
        # Initialize Redis connection
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            return
        
        logger.info(f"👂 Listening for drift events on channel: {self.event_channel}")
        logger.info(f"🔄 Models configured for retraining: {list(self.models_to_retrain.keys())}")
        logger.info(f"⏰ Retraining cooldown: {self.cooldown_hours} hours")
        
        self.running = True
        
        # Start event listening
        await self.listen_for_drift_events()
    
    async def listen_for_drift_events(self):
        """Listen for drift detection events from Redis"""
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(self.event_channel)
            
            logger.info(f"📡 Subscribed to {self.event_channel}, waiting for drift events...")
            
            async for message in pubsub.listen():
                if not self.running:
                    break
                    
                if message['type'] == 'message':
                    await self.handle_drift_event(message['data'])
                    
        except Exception as e:
            logger.error(f"❌ Error listening for events: {e}")
        finally:
            if self.redis_client:
                await pubsub.unsubscribe(self.event_channel)
    
    async def handle_drift_event(self, event_data: bytes):
        """Process a drift detection event and trigger retraining if needed"""
        try:
            event = json.loads(event_data.decode('utf-8'))
            correlation_id = event.get('correlation_id', str(uuid.uuid4()))
            
            logger.info(f"📨 Received drift event: {event} [correlation_id={correlation_id}]")
            
            # Validate event structure
            if event.get('event_type') != 'DriftDetectedEvent':
                logger.warning(f"⚠️  Ignoring non-drift event: {event.get('event_type')}")
                return
            
            sensor_id = event.get('sensor_id')
            drift_score = event.get('drift_score', 0.0)
            
            if not sensor_id:
                logger.error(f"❌ Invalid drift event - missing sensor_id: {event}")
                return
            
            # Check if retraining is needed and allowed
            if await self.should_trigger_retraining(sensor_id, drift_score, correlation_id):
                await self.trigger_model_retraining(sensor_id, event, correlation_id)
            else:
                logger.info(f"⏭️  Skipping retraining for sensor {sensor_id} [correlation_id={correlation_id}]")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in drift event: {e}")
        except Exception as e:
            logger.error(f"❌ Error handling drift event: {e}")
    
    async def should_trigger_retraining(self, sensor_id: str, drift_score: float, correlation_id: str) -> bool:
        """Determine if retraining should be triggered based on policies"""
        
        # Check concurrent retraining limit
        if len(self.active_retraining_jobs) >= self.max_concurrent_retraining:
            logger.warning(f"🚫 Max concurrent retraining limit reached ({self.max_concurrent_retraining}) [correlation_id={correlation_id}]")
            return False
        
        # Check cooldown period
        last_retraining = self.last_retraining_times.get(sensor_id)
        if last_retraining:
            cooldown_end = last_retraining + timedelta(hours=self.cooldown_hours)
            if datetime.now() < cooldown_end:
                remaining = cooldown_end - datetime.now()
                logger.info(f"⏰ Retraining cooldown active for sensor {sensor_id}: {remaining} remaining [correlation_id={correlation_id}]")
                return False
        
        logger.info(f"✅ Retraining criteria met for sensor {sensor_id} [correlation_id={correlation_id}]")
        return True
    
    async def trigger_model_retraining(self, sensor_id: str, drift_event: Dict, correlation_id: str):
        """Trigger automated model retraining for all configured models"""
        logger.warning(f"🔄 INITIATING MODEL RETRAINING for sensor {sensor_id} [correlation_id={correlation_id}]")
        
        # Update state
        self.last_retraining_times[sensor_id] = datetime.now()
        retraining_job_id = f"{sensor_id}_{int(time.time())}"
        self.active_retraining_jobs.add(retraining_job_id)
        
        try:
            # Retrain each configured model
            for model_type, make_target in self.models_to_retrain.items():
                success = await self.retrain_model(model_type, make_target, sensor_id, correlation_id)
                
                if success:
                    logger.info(f"✅ Successfully retrained {model_type} model [correlation_id={correlation_id}]")
                else:
                    logger.error(f"❌ Failed to retrain {model_type} model [correlation_id={correlation_id}]")
            
            # Log retraining completion
            logger.info(f"🎯 Model retraining cycle completed for sensor {sensor_id} [correlation_id={correlation_id}]")
            
            # Send email notification for successful retraining
            await self.send_email_notification(sensor_id, correlation_id)
            
            # Publish retraining completion event
            await self.publish_retraining_event(sensor_id, drift_event, correlation_id)
            
        except Exception as e:
            logger.error(f"❌ Retraining process failed for sensor {sensor_id}: {e} [correlation_id={correlation_id}]")
        finally:
            # Cleanup
            self.active_retraining_jobs.discard(retraining_job_id)
    
    async def retrain_model(self, model_type: str, make_target: str, sensor_id: str, correlation_id: str) -> bool:
        """Execute model retraining using Makefile target"""
        logger.info(f"🏭 Starting {model_type} model retraining using: make {make_target} [correlation_id={correlation_id}]")
        
        try:
            # Prepare environment
            env = os.environ.copy()
            env['CORRELATION_ID'] = correlation_id
            env['TRIGGER_SENSOR_ID'] = sensor_id
            env['RETRAINING_TIMESTAMP'] = datetime.utcnow().isoformat()
            
            # Execute retraining command
            result = subprocess.run(
                ['make', make_target],
                cwd='/app',  # Assuming we're running in Docker
                env=env,
                capture_output=True,
                text=True,
                timeout=self.training_timeout_minutes * 60
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {model_type} retraining completed successfully")
                logger.debug(f"📝 Training output: {result.stdout}")
                return True
            else:
                logger.error(f"❌ {model_type} retraining failed with exit code {result.returncode}")
                logger.error(f"📝 Error output: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ {model_type} retraining timed out after {self.training_timeout_minutes} minutes")
            return False
        except Exception as e:
            logger.error(f"❌ Exception during {model_type} retraining: {e}")
            return False
    
    async def publish_retraining_event(self, sensor_id: str, original_drift_event: Dict, correlation_id: str):
        """Publish retraining completion event"""
        if not self.redis_client:
            return
        
        try:
            retraining_event = {
                "event_type": "ModelRetrainingCompletedEvent",
                "sensor_id": sensor_id,
                "retraining_timestamp": datetime.utcnow().isoformat(),
                "models_retrained": list(self.models_to_retrain.keys()),
                "triggered_by_drift": original_drift_event,
                "correlation_id": correlation_id
            }
            
            await self.redis_client.publish('retraining_events', json.dumps(retraining_event))
            logger.info(f"📡 Published retraining completion event [correlation_id={correlation_id}]")
            
        except Exception as e:
            logger.error(f"❌ Failed to publish retraining event: {e}")
    
    async def send_email_notification(self, sensor_id: str, correlation_id: str):
        """Send email notification for successful retraining"""
        try:
            # Get email recipient from environment variable
            recipient = os.getenv('RETRAIN_SUCCESS_EMAIL')
            if not recipient:
                logger.info("📧 No email recipient configured for retraining notifications (RETRAIN_SUCCESS_EMAIL not set)")
                return
            
            # Prepare model information
            model_name = f"sensor-{sensor_id}-models"
            new_version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")  # Timestamp-based version
            
            # Collect metrics if available (mock for now)
            metrics = {
                "retrained_models": ", ".join(self.models_to_retrain.keys()),
                "training_duration": "N/A",  # Could be tracked in future
                "correlation_id": correlation_id
            }
            
            # Use the email service to send retraining success notification
            success = email_service.send_retrain_success(
                model_name=model_name,
                new_version=new_version,
                correlation_id=correlation_id,
                metrics=metrics
            )
            
            if success:
                logger.info(f"📧 Retraining success email sent to {recipient} for sensor {sensor_id}")
            else:
                logger.error(f"❌ Failed to send retraining success email for sensor {sensor_id}")
                
        except Exception as e:
            logger.error(f"❌ Email notification error: {e}")
    
    async def stop(self):
        """Gracefully stop the retraining agent"""
        logger.info("🛑 Stopping Model Retraining Agent...")
        
        self.running = False
        
        # Wait for active retraining jobs to complete (with timeout)
        if self.active_retraining_jobs:
            logger.info(f"⏳ Waiting for {len(self.active_retraining_jobs)} active retraining jobs to complete...")
            
            wait_timeout = 300  # 5 minutes
            start_time = time.time()
            
            while self.active_retraining_jobs and (time.time() - start_time) < wait_timeout:
                await asyncio.sleep(5)
            
            if self.active_retraining_jobs:
                logger.warning(f"⚠️  Timeout waiting for retraining jobs: {self.active_retraining_jobs}")
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("✅ Model Retraining Agent stopped")

async def main():
    """Main entry point for the model retraining agent"""
    agent = ModelRetrainingAgent()
    
    try:
        await agent.start()
        
        # Keep running until interrupted
        if agent.running:
            logger.info("⏳ Retraining agent running... Press Ctrl+C to stop")
            while agent.running:
                await asyncio.sleep(10)
        
    except KeyboardInterrupt:
        logger.info("🔄 Received shutdown signal")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())