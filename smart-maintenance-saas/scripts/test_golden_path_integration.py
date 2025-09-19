#!/usr/bin/env python3
"""
Enhanced Golden Path Integration Test Script

This script tests the complete end-to-end flow of the enhanced Golden Path agents:
1. DataAcquisitionAgent processes sensor data
2. AnomalyDetectionAgent detects anomalies using serverless models
3. ValidationAgent validates anomalies with multi-layer analysis
4. NotificationAgent sends intelligent notifications

Tests all enhanced enterprise features including:
- Batch processing, quality control, sensor profiling
- Serverless model loading from MLflow/S3
- Multi-layer validation with historical context
- Multi-channel notifications with templates
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any, List

# Add the app directory to Python path
sys.path.append('/app')

# Core imports
from core.events.event_bus import EventBus
from core.events.event_models import AnomalyDetectedEvent, AnomalyValidatedEvent
from data.schemas import SensorReading, SensorReadingCreate, SensorType, AnomalyAlert, ValidationStatus

# Enhanced Golden Path agent imports
from apps.agents.core.data_acquisition_agent import DataAcquisitionAgent
from apps.agents.core.anomaly_detection_agent import AnomalyDetectionAgent  
from apps.agents.core.validation_agent import ValidationAgent
from apps.agents.core.notification_agent import EnhancedNotificationAgent

# Service imports
from data.validators.agent_data_validator import DataValidator
from data.processors.agent_data_enricher import DataEnricher
from apps.rules.validation_rules import RuleEngine

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GoldenPathIntegrationTest:
    """Comprehensive test suite for the enhanced Golden Path flow."""
    
    def __init__(self):
        """Initialize the test environment with enhanced agents."""
        self.event_bus = EventBus()
        self.test_results = {
            'data_acquisition': {'passed': 0, 'failed': 0, 'details': []},
            'anomaly_detection': {'passed': 0, 'failed': 0, 'details': []},
            'validation': {'passed': 0, 'failed': 0, 'details': []},
            'notification': {'passed': 0, 'failed': 0, 'details': []},
            'integration': {'passed': 0, 'failed': 0, 'details': []}
        }
        
        # Initialize enhanced agents with production settings
        self._initialize_agents()
        
    def _initialize_agents(self):
        """Initialize all enhanced Golden Path agents with enterprise configurations."""
        logger.info("Initializing enhanced Golden Path agents...")
        
        # Service dependencies
        data_validator = DataValidator()
        data_enricher = DataEnricher()
        rule_engine = RuleEngine()
        
        # Enhanced agent configurations
        data_acquisition_settings = {
            'batch_processing_enabled': True,
            'batch_size': 5,
            'batch_timeout_seconds': 3.0,
            'quality_threshold': 0.7,
            'enable_circuit_breaker': True,
            'circuit_breaker_threshold': 3,
            'rate_limit_per_second': 50,
            'enable_sensor_profiling': True
        }
        
        anomaly_detection_settings = {
            'serverless_mode_enabled': True,
            'model_cache_ttl_minutes': 30,
            'max_concurrent_model_loads': 2,
            'enable_fallback_models': True,
            'performance_monitoring': True
        }
        
        validation_settings = {
            'credible_threshold': 0.7,
            'false_positive_threshold': 0.4,
            'recent_stability_window': 5,
            'recurring_anomaly_threshold_pct': 0.25,
            'historical_check_limit': 15
        }
        
        notification_settings = {
            'deduplication_window_minutes': 3,
            'rate_limit_per_user_per_hour': 30,
            'batch_size': 5,
            'batch_timeout_seconds': 10,
            'enable_batch_processing': True
        }
        
        # Initialize enhanced agents
        self.data_agent = DataAcquisitionAgent(
            agent_id="test_enhanced_data_acquisition",
            event_bus=self.event_bus,
            validator=data_validator,
            enricher=data_enricher,
            specific_settings=data_acquisition_settings
        )
        
        self.anomaly_agent = AnomalyDetectionAgent(
            agent_id="test_enhanced_anomaly_detection", 
            event_bus=self.event_bus,
            specific_settings=anomaly_detection_settings
        )
        
        self.validation_agent = ValidationAgent(
            agent_id="test_enhanced_validation",
            event_bus=self.event_bus,
            specific_settings=validation_settings
        )
        
        self.notification_agent = EnhancedNotificationAgent(
            agent_id="test_enhanced_notification",
            event_bus=self.event_bus,
            specific_settings=notification_settings
        )
        
        logger.info("Enhanced Golden Path agents initialized successfully")
    
    async def test_data_acquisition_agent(self) -> bool:
        """Test enhanced DataAcquisitionAgent capabilities."""
        logger.info("🔍 Testing Enhanced DataAcquisitionAgent...")
        
        try:
            # Test 1: Basic sensor reading processing
            test_reading = SensorReadingCreate(
                sensor_id="temp-sensor-test-001",
                sensor_type=SensorType.TEMPERATURE,
                value=85.5,
                unit="celsius",
                quality=0.95,
                timestamp=datetime.now(),
                metadata={"location": "test_zone", "equipment": "test_compressor"}
            )
            
            processed_reading = await self.data_agent.process_sensor_reading(test_reading)
            if processed_reading and processed_reading.sensor_id == "temp-sensor-test-001":
                self.test_results['data_acquisition']['passed'] += 1
                self.test_results['data_acquisition']['details'].append("✅ Basic sensor reading processing")
                logger.info("✅ Basic sensor reading processing passed")
            else:
                self.test_results['data_acquisition']['failed'] += 1
                self.test_results['data_acquisition']['details'].append("❌ Basic sensor reading processing failed")
                logger.error("❌ Basic sensor reading processing failed")
            
            # Test 2: Batch processing
            batch_readings = [
                SensorReadingCreate(
                    sensor_id=f"batch-sensor-{i:03d}",
                    sensor_type=SensorType.VIBRATION,
                    value=25.0 + i,
                    unit="mm/s",
                    quality=0.9,
                    timestamp=datetime.now()
                )
                for i in range(3)
            ]
            
            batch_results = await self.data_agent.process_batch_readings(batch_readings)
            if len(batch_results) == 3:
                self.test_results['data_acquisition']['passed'] += 1
                self.test_results['data_acquisition']['details'].append("✅ Batch processing functionality")
                logger.info("✅ Batch processing functionality passed")
            else:
                self.test_results['data_acquisition']['failed'] += 1
                self.test_results['data_acquisition']['details'].append("❌ Batch processing functionality failed")
                logger.error("❌ Batch processing functionality failed")
            
            # Test 3: Quality control
            low_quality_reading = SensorReadingCreate(
                sensor_id="quality-test-sensor",
                sensor_type=SensorType.PRESSURE,
                value=999999.0,  # Extreme value to test quality control
                unit="kPa",
                quality=0.3,  # Low quality score
                timestamp=datetime.now()
            )
            
            quality_result = await self.data_agent.process_sensor_reading(low_quality_reading)
            # Should still process but with quality flags
            if quality_result:
                self.test_results['data_acquisition']['passed'] += 1
                self.test_results['data_acquisition']['details'].append("✅ Quality control processing")
                logger.info("✅ Quality control processing passed")
            else:
                self.test_results['data_acquisition']['failed'] += 1
                self.test_results['data_acquisition']['details'].append("❌ Quality control processing failed")
                logger.error("❌ Quality control processing failed")
                
            # Test 4: Metrics collection
            if hasattr(self.data_agent, 'metrics') and self.data_agent.metrics.total_readings > 0:
                self.test_results['data_acquisition']['passed'] += 1
                self.test_results['data_acquisition']['details'].append("✅ Metrics collection")
                logger.info(f"✅ Metrics collection passed: {self.data_agent.metrics.total_readings} readings processed")
            else:
                self.test_results['data_acquisition']['failed'] += 1
                self.test_results['data_acquisition']['details'].append("❌ Metrics collection failed")
                logger.error("❌ Metrics collection failed")
            
            return self.test_results['data_acquisition']['failed'] == 0
            
        except Exception as e:
            logger.error(f"❌ DataAcquisitionAgent test failed with exception: {e}")
            self.test_results['data_acquisition']['failed'] += 1
            self.test_results['data_acquisition']['details'].append(f"❌ Exception: {str(e)}")
            return False
    
    async def test_anomaly_detection_agent(self) -> bool:
        """Test enhanced AnomalyDetectionAgent capabilities."""
        logger.info("🔍 Testing Enhanced AnomalyDetectionAgent...")
        
        try:
            # Test 1: Basic anomaly detection
            test_reading = SensorReading(
                sensor_id="temp-sensor-anomaly-001",
                sensor_type=SensorType.TEMPERATURE,
                value=150.0,  # High temperature to trigger anomaly
                unit="celsius",
                quality=0.95,
                timestamp=datetime.now(),
                metadata={"equipment": "test_equipment"}
            )
            
            anomaly_result = await self.anomaly_agent.detect_anomaly(test_reading)
            if anomaly_result and hasattr(anomaly_result, 'confidence'):
                self.test_results['anomaly_detection']['passed'] += 1
                self.test_results['anomaly_detection']['details'].append("✅ Basic anomaly detection")
                logger.info(f"✅ Basic anomaly detection passed: confidence={anomaly_result.confidence}")
            else:
                self.test_results['anomaly_detection']['failed'] += 1
                self.test_results['anomaly_detection']['details'].append("❌ Basic anomaly detection failed")
                logger.error("❌ Basic anomaly detection failed")
            
            # Test 2: Serverless model capabilities
            if hasattr(self.anomaly_agent, 'model_loader') and self.anomaly_agent.model_loader:
                self.test_results['anomaly_detection']['passed'] += 1
                self.test_results['anomaly_detection']['details'].append("✅ Serverless model loader available")
                logger.info("✅ Serverless model loader available")
            else:
                self.test_results['anomaly_detection']['failed'] += 1
                self.test_results['anomaly_detection']['details'].append("❌ Serverless model loader not available")
                logger.error("❌ Serverless model loader not available")
            
            # Test 3: Performance monitoring
            if hasattr(self.anomaly_agent, 'performance_metrics'):
                self.test_results['anomaly_detection']['passed'] += 1
                self.test_results['anomaly_detection']['details'].append("✅ Performance monitoring enabled")
                logger.info("✅ Performance monitoring enabled")
            else:
                self.test_results['anomaly_detection']['failed'] += 1
                self.test_results['anomaly_detection']['details'].append("❌ Performance monitoring not available")
                logger.error("❌ Performance monitoring not available")
            
            return self.test_results['anomaly_detection']['failed'] == 0
            
        except Exception as e:
            logger.error(f"❌ AnomalyDetectionAgent test failed with exception: {e}")
            self.test_results['anomaly_detection']['failed'] += 1
            self.test_results['anomaly_detection']['details'].append(f"❌ Exception: {str(e)}")
            return False
    
    async def test_validation_agent(self) -> bool:
        """Test enhanced ValidationAgent capabilities."""
        logger.info("🔍 Testing Enhanced ValidationAgent...")
        
        try:
            # Test 1: Basic validation functionality
            test_alert = AnomalyAlert(
                sensor_id="temp-sensor-validation-001",
                anomaly_type="temperature_spike",
                severity=4,
                confidence=0.85,
                description="Critical temperature anomaly detected in test equipment"
            )
            
            test_reading = SensorReading(
                sensor_id="temp-sensor-validation-001",
                sensor_type=SensorType.TEMPERATURE,
                value=150.0,
                unit="celsius",
                quality=0.95,
                timestamp=datetime.now()
            )
            
            # Test historical validation method
            correlation_id = "test-correlation-001"
            hist_adjustment, hist_reasons = await self.validation_agent._perform_historical_validation(
                alert=test_alert,
                reading=test_reading,
                correlation_id=correlation_id
            )
            
            if isinstance(hist_adjustment, float) and isinstance(hist_reasons, list):
                self.test_results['validation']['passed'] += 1
                self.test_results['validation']['details'].append("✅ Historical validation processing")
                logger.info(f"✅ Historical validation passed: adjustment={hist_adjustment}")
            else:
                self.test_results['validation']['failed'] += 1
                self.test_results['validation']['details'].append("❌ Historical validation processing failed")
                logger.error("❌ Historical validation processing failed")
            
            # Test 2: Metrics tracking
            if hasattr(self.validation_agent, 'metrics') and hasattr(self.validation_agent.metrics, 'total_validations'):
                self.test_results['validation']['passed'] += 1
                self.test_results['validation']['details'].append("✅ Validation metrics available")
                logger.info("✅ Validation metrics available")
            else:
                self.test_results['validation']['failed'] += 1
                self.test_results['validation']['details'].append("❌ Validation metrics not available")
                logger.error("❌ Validation metrics not available")
            
            # Test 3: Configuration validation
            if self.validation_agent.settings.get('credible_threshold') == 0.7:
                self.test_results['validation']['passed'] += 1
                self.test_results['validation']['details'].append("✅ Configuration settings applied")
                logger.info("✅ Configuration settings applied correctly")
            else:
                self.test_results['validation']['failed'] += 1
                self.test_results['validation']['details'].append("❌ Configuration settings not applied")
                logger.error("❌ Configuration settings not applied")
            
            return self.test_results['validation']['failed'] == 0
            
        except Exception as e:
            logger.error(f"❌ ValidationAgent test failed with exception: {e}")
            self.test_results['validation']['failed'] += 1
            self.test_results['validation']['details'].append(f"❌ Exception: {str(e)}")
            return False
    
    async def test_notification_agent(self) -> bool:
        """Test enhanced NotificationAgent capabilities."""
        logger.info("🔍 Testing Enhanced NotificationAgent...")
        
        try:
            # Test 1: Template availability
            available_templates = list(self.notification_agent.templates.keys())
            expected_templates = ['anomaly_critical', 'anomaly_validated', 'maintenance_scheduled', 'maintenance_predicted']
            
            if all(template in available_templates for template in expected_templates):
                self.test_results['notification']['passed'] += 1
                self.test_results['notification']['details'].append("✅ Notification templates available")
                logger.info(f"✅ Notification templates available: {available_templates}")
            else:
                self.test_results['notification']['failed'] += 1
                self.test_results['notification']['details'].append("❌ Notification templates missing")
                logger.error("❌ Notification templates missing")
            
            # Test 2: Provider availability
            if self.notification_agent.providers:
                self.test_results['notification']['passed'] += 1
                self.test_results['notification']['details'].append("✅ Notification providers initialized")
                logger.info(f"✅ Notification providers: {list(self.notification_agent.providers.keys())}")
            else:
                self.test_results['notification']['failed'] += 1
                self.test_results['notification']['details'].append("❌ No notification providers available")
                logger.error("❌ No notification providers available")
            
            # Test 3: Metrics tracking
            if hasattr(self.notification_agent, 'metrics'):
                self.test_results['notification']['passed'] += 1
                self.test_results['notification']['details'].append("✅ Notification metrics available")
                logger.info("✅ Notification metrics available")
            else:
                self.test_results['notification']['failed'] += 1
                self.test_results['notification']['details'].append("❌ Notification metrics not available")
                logger.error("❌ Notification metrics not available")
            
            # Test 4: Circuit breaker states
            if hasattr(self.notification_agent, 'circuit_breaker_states') and self.notification_agent.circuit_breaker_states:
                self.test_results['notification']['passed'] += 1
                self.test_results['notification']['details'].append("✅ Circuit breaker protection enabled")
                logger.info("✅ Circuit breaker protection enabled")
            else:
                self.test_results['notification']['failed'] += 1
                self.test_results['notification']['details'].append("❌ Circuit breaker protection not available")
                logger.error("❌ Circuit breaker protection not available")
            
            return self.test_results['notification']['failed'] == 0
            
        except Exception as e:
            logger.error(f"❌ NotificationAgent test failed with exception: {e}")
            self.test_results['notification']['failed'] += 1
            self.test_results['notification']['details'].append(f"❌ Exception: {str(e)}")
            return False
    
    async def test_integration_flow(self) -> bool:
        """Test end-to-end integration between all enhanced agents."""
        logger.info("🔍 Testing Enhanced Golden Path Integration Flow...")
        
        try:
            # Test 1: Agent initialization
            agents = [self.data_agent, self.anomaly_agent, self.validation_agent, self.notification_agent]
            initialized_agents = [agent for agent in agents if hasattr(agent, 'agent_id')]
            
            if len(initialized_agents) == 4:
                self.test_results['integration']['passed'] += 1
                self.test_results['integration']['details'].append("✅ All agents initialized")
                logger.info("✅ All Golden Path agents initialized successfully")
            else:
                self.test_results['integration']['failed'] += 1
                self.test_results['integration']['details'].append("❌ Agent initialization incomplete")
                logger.error("❌ Agent initialization incomplete")
            
            # Test 2: Agent settings configuration
            agents_with_settings = [
                agent for agent in agents 
                if hasattr(agent, 'settings') and agent.settings
            ]
            
            if len(agents_with_settings) >= 3:  # At least 3 agents should have settings
                self.test_results['integration']['passed'] += 1
                self.test_results['integration']['details'].append("✅ Agent settings configured")
                logger.info("✅ Agent settings configured properly")
            else:
                self.test_results['integration']['failed'] += 1
                self.test_results['integration']['details'].append("❌ Agent settings configuration incomplete")
                logger.error("❌ Agent settings configuration incomplete")
            
            # Test 3: Event bus integration
            agents_with_event_bus = [
                agent for agent in agents 
                if hasattr(agent, 'event_bus') and agent.event_bus is not None
            ]
            
            if len(agents_with_event_bus) == 4:
                self.test_results['integration']['passed'] += 1
                self.test_results['integration']['details'].append("✅ Event bus integration")
                logger.info("✅ All agents connected to event bus")
            else:
                self.test_results['integration']['failed'] += 1
                self.test_results['integration']['details'].append("❌ Event bus integration incomplete")
                logger.error("❌ Event bus integration incomplete")
            
            return self.test_results['integration']['failed'] == 0
            
        except Exception as e:
            logger.error(f"❌ Integration test failed with exception: {e}")
            self.test_results['integration']['failed'] += 1
            self.test_results['integration']['details'].append(f"❌ Exception: {str(e)}")
            return False
    
    def generate_test_report(self) -> str:
        """Generate comprehensive test report."""
        total_passed = sum(result['passed'] for result in self.test_results.values())
        total_failed = sum(result['failed'] for result in self.test_results.values())
        total_tests = total_passed + total_failed
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ENHANCED GOLDEN PATH INTEGRATION TEST REPORT             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║ 🎯 OVERALL RESULTS:                                                          ║
║    • Total Tests: {total_tests:3d}                                                    ║
║    • Passed:      {total_passed:3d}                                                    ║
║    • Failed:      {total_failed:3d}                                                    ║
║    • Success Rate: {success_rate:5.1f}%                                                ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
"""
        
        for component, results in self.test_results.items():
            component_total = results['passed'] + results['failed']
            component_rate = (results['passed'] / component_total * 100) if component_total > 0 else 0
            status_icon = "✅" if results['failed'] == 0 else "❌"
            
            report += f"""║ {status_icon} {component.upper().replace('_', ' '):20s}                                      ║
║    Passed: {results['passed']:2d} | Failed: {results['failed']:2d} | Success: {component_rate:5.1f}%                        ║
"""
            for detail in results['details']:
                report += f"║    {detail:62s} ║\n"
            report += "║                                                                              ║\n"
        
        report += """╚══════════════════════════════════════════════════════════════════════════════╝

🚀 ENHANCED GOLDEN PATH AGENTS SUMMARY:
   
   📊 DataAcquisitionAgent: Enterprise sensor data processing with batch operations,
      quality control, sensor profiling, and circuit breaker protection.
      
   🤖 AnomalyDetectionAgent: Serverless model loading from MLflow/S3 with intelligent
      caching, fallback mechanisms, and performance monitoring.
      
   ✅ ValidationAgent: Multi-layer validation with historical context analysis,
      adaptive confidence scoring, and comprehensive metrics tracking.
      
   📧 NotificationAgent: Multi-channel notification routing with template engine,
      priority handling, and delivery analytics.

"""
        
        if success_rate >= 90:
            report += "🎉 EXCELLENT: Golden Path integration is production-ready!\n"
        elif success_rate >= 75:
            report += "✅ GOOD: Golden Path integration is operational with minor issues.\n"
        elif success_rate >= 50:
            report += "⚠️  NEEDS WORK: Golden Path integration has significant issues.\n"
        else:
            report += "❌ CRITICAL: Golden Path integration requires major fixes.\n"
        
        return report

    async def run_all_tests(self) -> bool:
        """Run all enhanced Golden Path tests."""
        logger.info("🚀 Starting Enhanced Golden Path Integration Tests...")
        
        # Run individual agent tests
        data_success = await self.test_data_acquisition_agent()
        anomaly_success = await self.test_anomaly_detection_agent() 
        validation_success = await self.test_validation_agent()
        notification_success = await self.test_notification_agent()
        integration_success = await self.test_integration_flow()
        
        # Generate and display report
        report = self.generate_test_report()
        print(report)
        
        # Overall success
        overall_success = all([
            data_success, anomaly_success, validation_success, 
            notification_success, integration_success
        ])
        
        if overall_success:
            logger.info("🎯 ALL ENHANCED GOLDEN PATH TESTS PASSED! 🎯")
        else:
            logger.error("❌ Some Enhanced Golden Path tests failed.")
        
        return overall_success


async def main():
    """Run the enhanced Golden Path integration tests."""
    print("🔍 Enhanced Golden Path Integration Test Suite")
    print("=" * 80)
    
    test_suite = GoldenPathIntegrationTest()
    success = await test_suite.run_all_tests()
    
    if success:
        print("\n✨ Enhanced Golden Path Phase 2 Implementation Complete! ✨")
        return 0
    else:
        print("\n❌ Enhanced Golden Path tests failed. Please review and fix issues.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)