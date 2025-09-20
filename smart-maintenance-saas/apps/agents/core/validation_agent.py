import asyncio
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Tuple, List, Any, Optional, Callable, Dict, Union, Set
from dataclasses import dataclass
from enum import Enum

# Core application imports - CRITICAL: Ensure these paths are correct for absolute imports
from core.base_agent_abc import BaseAgent, AgentCapability
from core.events.event_bus import EventBus
from core.database.crud.crud_sensor_reading import CRUDSensorReading # Instance expected
from apps.rules.validation_rules import RuleEngine # Instance expected
from core.events.event_models import AnomalyDetectedEvent, AnomalyValidatedEvent
from data.schemas import AnomalyAlert, SensorReading, ValidationStatus # Pydantic models for parsing, Added ValidationStatus
from data.exceptions import (
    DataValidationException,
    AgentProcessingError,
    WorkflowError,
    SmartMaintenanceBaseException
)

# Import AsyncSession for type hinting if a session factory is used
from sqlalchemy.ext.asyncio import AsyncSession


class ValidationDecision(Enum):
    """Enhanced validation decision types."""
    CREDIBLE_ANOMALY = "credible_anomaly"
    FALSE_POSITIVE_SUSPECTED = "false_positive_suspected"
    FURTHER_INVESTIGATION_NEEDED = "further_investigation_needed"
    INSUFFICIENT_DATA = "insufficient_data"
    VALIDATION_ERROR = "validation_error"


@dataclass
class ValidationMetrics:
    """Metrics for validation performance tracking."""
    total_validations: int = 0
    credible_anomalies: int = 0
    false_positives: int = 0
    investigation_needed: int = 0
    validation_errors: int = 0
    avg_processing_time: float = 0.0
    rule_engine_success_rate: float = 0.0
    historical_data_success_rate: float = 0.0


@dataclass
class SensorValidationProfile:
    """Profile for sensor-specific validation patterns."""
    sensor_id: str
    total_validations: int = 0
    credible_count: int = 0
    false_positive_count: int = 0
    avg_confidence_adjustment: float = 0.0
    last_validation: Optional[datetime] = None
    historical_fetch_success_rate: float = 1.0
    common_anomaly_types: Dict[str, int] = None
    
    def __post_init__(self):
        if self.common_anomaly_types is None:
            self.common_anomaly_types = defaultdict(int)

class ValidationAgent(BaseAgent):
    """
    Enhanced ValidationAgent for production-ready anomaly validation.

    The ValidationAgent is responsible for validating detected anomalies with enterprise-grade
    features including intelligent validation strategies, performance monitoring, and adaptive
    learning capabilities.

    Key Responsibilities:
    1. **Multi-Layer Validation**: Rule-based validation, historical contextualization, and pattern analysis
    2. **Adaptive Confidence Scoring**: Dynamic confidence adjustments based on multiple factors
    3. **Performance Monitoring**: Real-time metrics and validation performance tracking
    4. **Sensor Profiling**: Learn sensor-specific validation patterns over time
    5. **Quality Assurance**: Comprehensive error handling and validation quality control
    6. **Batch Processing**: Efficient handling of multiple anomalies with optimization
    7. **Circuit Breaker**: Protection against database and external service failures

    Enhanced Features:
    - **Intelligent Fallbacks**: Graceful degradation when external dependencies fail
    - **Validation Caching**: Cache historical data and rule results for performance
    - **Pattern Learning**: Adapt validation thresholds based on historical accuracy
    - **Performance Optimization**: Batch queries and concurrent processing
    - **Comprehensive Monitoring**: Detailed metrics and validation quality tracking
    """

    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        crud_sensor_reading: Optional[CRUDSensorReading] = None,
        rule_engine: Optional[RuleEngine] = None,
        db_session_factory: Optional[Callable[[], AsyncSession]] = None,
        specific_settings: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the enhanced ValidationAgent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            event_bus: Event bus for publishing/subscribing to events
            crud_sensor_reading: CRUD instance for sensor data (optional, creates fallback if not provided)
            rule_engine: Rule engine instance (optional, creates fallback if not provided)
            db_session_factory: Database session factory (optional)
            specific_settings: Agent-specific configuration settings
        """
        super().__init__(agent_id=agent_id, event_bus=event_bus)
        self.logger = logging.getLogger(f"{__name__}.{self.agent_id}")
        
        # Core components with fallback initialization
        self.crud_sensor_reading = crud_sensor_reading or self._create_fallback_crud()
        self.rule_engine = rule_engine or self._create_fallback_rule_engine()
        self.db_session_factory = db_session_factory
        
        # Create proper settings object for test compatibility
        from types import SimpleNamespace
        settings_dict = specific_settings or {}

        # Enhanced configuration - extract values and remove from dict to avoid duplicates
        self.batch_processing_enabled = settings_dict.pop('batch_processing_enabled', False)
        self.batch_size = settings_dict.pop('batch_size', 5)
        self.batch_timeout_seconds = settings_dict.pop('batch_timeout_seconds', 3.0)
        self.enable_caching = settings_dict.pop('enable_caching', True)
        self.cache_ttl_seconds = settings_dict.pop('cache_ttl_seconds', 300)  # 5 minutes
        self.enable_learning = settings_dict.pop('enable_learning', True)
        self.enable_circuit_breaker = settings_dict.pop('enable_circuit_breaker', True)
        
        # Performance monitoring
        self.metrics = ValidationMetrics()
        self.sensor_profiles: Dict[str, SensorValidationProfile] = {}
        self.processing_times: deque = deque(maxlen=100)  # Keep last 100 processing times
        
        # Caching system
        self.historical_data_cache: Dict[str, Tuple[List[SensorReading], datetime]] = {}
        self.rule_results_cache: Dict[str, Tuple[float, List[str], datetime]] = {}
        
        # Circuit breaker for database operations
        self.db_circuit_breaker_failures = 0
        self.db_circuit_breaker_threshold = settings_dict.pop('db_circuit_breaker_threshold', 5)
        self.db_circuit_breaker_timeout = settings_dict.pop('db_circuit_breaker_timeout_seconds', 60)
        self.db_circuit_breaker_last_failure = None
        self.db_circuit_breaker_open = False
        
        # Batch processing
        self.batch_queue: List[AnomalyDetectedEvent] = []
        self.batch_timer_task: Optional[asyncio.Task] = None
        
        # Validation thresholds (can be adapted over time)
        self.credible_threshold = settings_dict.pop("credible_threshold", 0.7)
        self.false_positive_threshold = settings_dict.pop("false_positive_threshold", 0.4)
        
        # Create settings object with attributes for test compatibility
        self.settings = SimpleNamespace(
            credible_threshold=self.credible_threshold,
            batch_processing_enabled=self.batch_processing_enabled,
            batch_size=self.batch_size
        )
        
        # Add any additional settings from settings_dict that aren't already set
        for key, value in settings_dict.items():
            if not hasattr(self.settings, key):
                setattr(self.settings, key, value)
        
        # Event types
        self.input_event_type = AnomalyDetectedEvent.__name__
        self.output_event_type = AnomalyValidatedEvent.__name__
        
        self.logger.info(
            f"Enhanced ValidationAgent '{self.agent_id}' initialized. "
            f"Batch processing: {self.batch_processing_enabled}, "
            f"Caching: {self.enable_caching}, "
            f"Learning: {self.enable_learning}, "
            f"Circuit breaker: {self.enable_circuit_breaker}",
            extra={"correlation_id": "N/A"}
        )

    def _create_fallback_crud(self) -> Any:
        """Create a fallback CRUD implementation."""
        class FallbackCRUD:
            def orm_to_pydantic(self, orm_obj):
                return orm_obj
            
            async def get_sensor_readings_by_sensor_id(self, db, sensor_id, end_time, limit):
                # Return empty list as fallback
                return []
        
        self.logger.warning("Using fallback CRUD implementation - historical data features disabled")
        return FallbackCRUD()
    
    def _create_fallback_rule_engine(self) -> Any:
        """Create a fallback rule engine implementation."""
        class FallbackRuleEngine:
            async def evaluate_rules(self, alert, reading):
                # Return neutral adjustment as fallback
                return 0.0, ["Rule engine not available - using neutral adjustment"]
        
        self.logger.warning("Using fallback rule engine - rule-based validation disabled")
        return FallbackRuleEngine()

    @property
    def historical_check_limit(self) -> int:
        """Return the historical check limit from settings, used by tests."""
        return getattr(self.settings, "historical_check_limit", 20)

    async def register_capabilities(self) -> None:
        """Register agent capabilities."""
        capability = AgentCapability(
            name="validate_anomalies",
            description="Validates detected anomalies using multi-layer analysis with rule-based and historical validation",
            input_types=[AnomalyDetectedEvent.__name__],
            output_types=[AnomalyValidatedEvent.__name__]
        )
        self.capabilities.append(capability)
        self.logger.debug(f"Agent {self.agent_id} registered capability: {capability.name}")

    async def start(self) -> None:
        """Start the agent and subscribe to events."""
        await super().start()
        if self.event_bus:
            await self.event_bus.subscribe(
                event_type_name=self.input_event_type, handler=self.process
            )
            
            # Start batch processing timer if enabled
            if self.batch_processing_enabled:
                self.batch_timer_task = asyncio.create_task(self._batch_timer())
            
            self.logger.info(
                f"Enhanced ValidationAgent {self.agent_id} started and subscribed to '{self.input_event_type}'",
                extra={"correlation_id": "N/A"}
            )
        else:
            self.logger.error(
                f"Agent {self.agent_id} cannot start: EventBus not provided",
                extra={"correlation_id": "N/A"}
            )

    async def stop(self) -> None:
        """Stop the agent and cleanup resources."""
        await super().stop()
        
        # Cancel batch timer if running
        if self.batch_timer_task and not self.batch_timer_task.done():
            self.batch_timer_task.cancel()
            try:
                await self.batch_timer_task
            except asyncio.CancelledError:
                pass
        
        # Process any remaining batched events
        if self.batch_queue:
            await self._process_batch(self.batch_queue.copy())
            self.batch_queue.clear()
        
        if self.event_bus:
            await self.event_bus.unsubscribe(
                event_type_name=self.input_event_type, handler=self.process
            )
            self.logger.info(f"Enhanced ValidationAgent {self.agent_id} stopped")
        else:
            self.logger.warning(f"Agent {self.agent_id} cannot stop gracefully: EventBus not provided")

    async def process(self, event: AnomalyDetectedEvent) -> None:
        """
        Main processing entry point for anomaly validation.
        
        Handles both individual and batch processing based on configuration.
        """
        if self.batch_processing_enabled:
            await self._add_to_batch(event)
        else:
            await self._process_single_event(event)

    async def _add_to_batch(self, event: AnomalyDetectedEvent) -> None:
        """Add event to batch processing queue."""
        self.batch_queue.append(event)
        
        # Process batch if it reaches the configured size
        if len(self.batch_queue) >= self.batch_size:
            batch_to_process = self.batch_queue.copy()
            self.batch_queue.clear()
            await self._process_batch(batch_to_process)

    async def _batch_timer(self) -> None:
        """Timer task for batch processing timeout."""
        try:
            while True:
                await asyncio.sleep(self.batch_timeout_seconds)
                if self.batch_queue:
                    batch_to_process = self.batch_queue.copy()
                    self.batch_queue.clear()
                    await self._process_batch(batch_to_process)
        except asyncio.CancelledError:
            pass

    async def _process_batch(self, events: List[AnomalyDetectedEvent]) -> None:
        """Process a batch of events efficiently."""
        if not events:
            return
        
        start_time = time.time()
        self.logger.info(f"Processing validation batch of {len(events)} events")
        
        # Process events concurrently
        tasks = [self._process_single_event(event) for event in events]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update batch metrics
        processing_time = time.time() - start_time
        self.logger.info(
            f"Completed batch validation of {len(events)} events in {processing_time:.3f}s"
        )

    async def _process_single_event(self, event: AnomalyDetectedEvent) -> None:
        """Process a single anomaly validation event."""
        start_time = time.time()
        
        # Extract correlation ID
        event_correlation_id = getattr(event, 'correlation_id', None)
        if event_correlation_id is None and hasattr(event, 'event_id'):
            event_correlation_id = str(event.event_id)
        log_correlation_id = event_correlation_id or "N/A"

        self.logger.info(
            f"Processing AnomalyDetectedEvent (ID: {getattr(event, 'event_id', 'N/A')}) "
            f"(Correlation ID: {log_correlation_id})",
            extra={"correlation_id": log_correlation_id}
        )

        try:
            # Parse and validate event data
            parsed_alert, parsed_reading = await self._parse_and_validate_event(event, log_correlation_id)
            
            # Update sensor profile
            if self.enable_learning:
                await self._update_sensor_profile(parsed_alert.sensor_id, log_correlation_id)
            
            # Perform validation steps
            rule_adj, rule_reasons = await self._perform_rule_validation(
                parsed_alert, parsed_reading, log_correlation_id
            )
            
            hist_adj, hist_reasons = await self._perform_historical_validation(
                parsed_alert, parsed_reading, log_correlation_id
            )
            
            # Calculate final confidence and status
            final_confidence = max(0.0, min(1.0, parsed_alert.confidence + rule_adj + hist_adj))
            validation_status = self._determine_validation_status(final_confidence)
            
            # Compile validation reasons
            all_reasons = self._compile_validation_reasons(rule_reasons, hist_reasons)
            
            # Publish validation result
            await self._publish_validation_result(
                event, parsed_alert, parsed_reading, final_confidence,
                validation_status, all_reasons, event_correlation_id, log_correlation_id
            )
            
            # Update metrics and profiles
            await self._update_metrics_and_profiles(
                parsed_alert.sensor_id, validation_status, final_confidence - parsed_alert.confidence,
                start_time, log_correlation_id
            )
            
            self.logger.info(
                f"Validation completed for sensor {parsed_alert.sensor_id}: "
                f"confidence {parsed_alert.confidence:.3f} -> {final_confidence:.3f}, "
                f"status: {validation_status.value}",
                extra={"correlation_id": log_correlation_id}
            )
            
        except Exception as e:
            self.metrics.validation_errors += 1
            self.logger.error(
                f"Validation failed for event {getattr(event, 'event_id', 'N/A')}: {e}",
                exc_info=True,
                extra={"correlation_id": log_correlation_id}
            )
            # Could publish a validation error event here


            # Could publish a validation error event here

    async def _parse_and_validate_event(self, event: AnomalyDetectedEvent, correlation_id: str) -> Tuple[AnomalyAlert, SensorReading]:
        """Parse and validate event data into Pydantic models."""
        if not isinstance(event.anomaly_details, dict) or not isinstance(event.triggering_data, dict):
            raise DataValidationException(
                f"Event {getattr(event, 'event_id', 'N/A')} has invalid payload structure"
            )

        try:
            parsed_alert = AnomalyAlert(**event.anomaly_details)
            parsed_reading = SensorReading(**event.triggering_data)
            return parsed_alert, parsed_reading
        except Exception as e:
            raise DataValidationException(f"Failed to parse event data: {e}") from e

    async def _update_sensor_profile(self, sensor_id: str, correlation_id: str) -> None:
        """Update sensor validation profile for learning."""
        if sensor_id not in self.sensor_profiles:
            self.sensor_profiles[sensor_id] = SensorValidationProfile(sensor_id=sensor_id)
        
        profile = self.sensor_profiles[sensor_id]
        profile.total_validations += 1
        profile.last_validation = datetime.utcnow()

    async def _perform_rule_validation(self, alert: AnomalyAlert, reading: SensorReading, correlation_id: str) -> Tuple[float, List[str]]:
        """Perform rule-based validation with caching."""
        # Create cache key for rule validation
        cache_key = f"rule_{alert.sensor_id}_{alert.anomaly_type}_{reading.value}_{alert.confidence}"
        
        # Check cache if enabled
        if self.enable_caching and cache_key in self.rule_results_cache:
            cached_result, cached_time = self.rule_results_cache[cache_key]
            if (datetime.utcnow() - cached_time).total_seconds() < self.cache_ttl_seconds:
                adj, reasons = cached_result
                self.logger.debug(f"Rule validation cache hit for {alert.sensor_id}", 
                                extra={"correlation_id": correlation_id})
                return adj, reasons

        try:
            # Perform rule validation
            rule_adj, rule_reasons = await self.rule_engine.evaluate_rules(
                alert=alert, reading=reading
            )
            
            # Cache the result
            if self.enable_caching:
                self.rule_results_cache[cache_key] = ((rule_adj, rule_reasons), datetime.utcnow())
            
            self.logger.debug(
                f"Rule validation for {alert.sensor_id}: adjustment={rule_adj}, reasons='{'; '.join(rule_reasons)}'",
                extra={"correlation_id": correlation_id}
            )
            
            return rule_adj, rule_reasons
            
        except Exception as e:
            self.logger.warning(f"Rule validation failed for {alert.sensor_id}: {e}", 
                              extra={"correlation_id": correlation_id})
            return 0.0, [f"Rule validation failed: {str(e)}"]

    async def _perform_historical_validation(self, alert: AnomalyAlert, reading: SensorReading, correlation_id: str) -> Tuple[float, List[str]]:
        """Perform historical validation with circuit breaker and caching."""
        # Check circuit breaker
        if self._is_db_circuit_breaker_open():
            return 0.0, ["Historical validation unavailable: database circuit breaker open"]
        
        # Check cache
        cache_key = f"hist_{alert.sensor_id}_{reading.timestamp.isoformat()}"
        if self.enable_caching and cache_key in self.historical_data_cache:
            cached_data, cached_time = self.historical_data_cache[cache_key]
            if (datetime.utcnow() - cached_time).total_seconds() < self.cache_ttl_seconds:
                self.logger.debug(f"Historical data cache hit for {alert.sensor_id}",
                                extra={"correlation_id": correlation_id})
                return self._analyze_historical_patterns(alert, reading, cached_data, correlation_id)

        try:
            # Fetch historical data
            historical_readings, fetch_error = await self._fetch_historical_data(
                sensor_id=alert.sensor_id,
                before_timestamp=reading.timestamp,
                limit=self.historical_check_limit,
                correlation_id=correlation_id
            )
            
            # Cache the historical data
            if self.enable_caching and not fetch_error:
                self.historical_data_cache[cache_key] = (historical_readings, datetime.utcnow())
            
            # Analyze patterns
            if fetch_error:
                self._increment_db_circuit_breaker()
                return 0.0, [fetch_error]
            
            self._reset_db_circuit_breaker()
            return self._analyze_historical_patterns(alert, reading, historical_readings, correlation_id)
            
        except Exception as e:
            self._increment_db_circuit_breaker()
            self.logger.error(f"Historical validation error for {alert.sensor_id}: {e}",
                            exc_info=True, extra={"correlation_id": correlation_id})
            return 0.0, [f"Historical validation error: {str(e)}"]

    def _analyze_historical_patterns(self, alert: AnomalyAlert, reading: SensorReading, 
                                   historical_readings: List[SensorReading], correlation_id: str) -> Tuple[float, List[str]]:
        """Analyze historical patterns for validation (enhanced version of original logic)."""
        if not historical_readings:
            return 0.0, ["No historical readings available for context"]
        
        historical_confidence_adjustment = 0.0
        historical_reasons = []
        
        # Enhanced stability analysis
        window = getattr(self.settings, "recent_stability_window", 5)
        if len(historical_readings) >= window:
            recent_values = [r.value for r in historical_readings[:window]]
            avg_recent_value = sum(recent_values) / len(recent_values)
            variance = sum([(x - avg_recent_value) ** 2 for x in recent_values]) / len(recent_values)
            std_dev_recent = variance ** 0.5
            
            # Stability assessment
            stability_factor = getattr(self.settings, "recent_stability_factor", 0.1)
            min_std_dev = getattr(self.settings, "recent_stability_min_std_dev", 0.05)
            is_stable = std_dev_recent < (stability_factor * abs(avg_recent_value) + 1e-6) or std_dev_recent < min_std_dev
            
            current_value = reading.value
            if isinstance(current_value, (int, float)):
                deviation = abs(current_value - avg_recent_value)
                threshold = 3 * (std_dev_recent + 1e-3)
                
                if is_stable:
                    if deviation > threshold:
                        adjustment = getattr(self.settings, "recent_stability_jump_adjustment", 0.15)
                        historical_confidence_adjustment += adjustment
                        historical_reasons.append(
                            f"Significant deviation from stable baseline (dev: {deviation:.2f}, threshold: {threshold:.2f})"
                        )
                    else:
                        adjustment = getattr(self.settings, "recent_stability_minor_deviation_adjustment", -0.05)
                        historical_confidence_adjustment += adjustment
                        historical_reasons.append(f"Minor deviation from stable baseline")
                else:
                    adjustment = getattr(self.settings, "volatile_baseline_adjustment", 0.05)
                    historical_confidence_adjustment += adjustment
                    historical_reasons.append(f"Anomaly during volatile period (std_dev: {std_dev_recent:.3f})")
        
        # Pattern frequency analysis
        if len(historical_readings) >= 3:
            similar_patterns = 0
            anomaly_threshold = getattr(self.settings, "pattern_anomaly_threshold", 0.2)
            
            for i in range(len(historical_readings) - 1):
                current_val = historical_readings[i].value
                previous_val = historical_readings[i + 1].value
                
                if isinstance(current_val, (int, float)) and isinstance(previous_val, (int, float)):
                    denominator = abs(previous_val) + 1e-6
                    percentage_diff = abs(current_val - previous_val) / denominator
                    if percentage_diff > anomaly_threshold:
                        similar_patterns += 1
            
            pattern_frequency = similar_patterns / (len(historical_readings) - 1)
            if pattern_frequency > 0.3:  # More than 30% of patterns are anomalous
                penalty = getattr(self.settings, "recurring_anomaly_penalty", -0.08)
                historical_confidence_adjustment += penalty
                historical_reasons.append(f"Recurring anomaly pattern detected ({pattern_frequency:.1%} frequency)")
        
        # Quality trend analysis
        quality_scores = [r.quality_score for r in historical_readings if hasattr(r, 'quality_score') and r.quality_score is not None]
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            if avg_quality < 0.7:
                quality_penalty = getattr(self.settings, "low_quality_penalty", -0.03)
                historical_confidence_adjustment += quality_penalty
                historical_reasons.append(f"Low historical data quality (avg: {avg_quality:.2f})")
        
        return historical_confidence_adjustment, historical_reasons

    def _determine_validation_status(self, final_confidence: float) -> ValidationDecision:
        """Determine validation status based on confidence and thresholds."""
        if final_confidence >= self.credible_threshold:
            return ValidationDecision.CREDIBLE_ANOMALY
        elif final_confidence < self.false_positive_threshold:
            return ValidationDecision.FALSE_POSITIVE_SUSPECTED
        else:
            return ValidationDecision.FURTHER_INVESTIGATION_NEEDED

    def _compile_validation_reasons(self, rule_reasons: List[str], hist_reasons: List[str]) -> List[str]:
        """Compile and clean validation reasons."""
        all_reasons = rule_reasons + hist_reasons
        
        # Filter out generic messages
        filtered_reasons = [
            r for r in all_reasons 
            if r not in [
                "No rule-based adjustments applied.",
                "No significant historical patterns affected confidence based on implemented rules.",
                "No historical readings available for comparison."
            ]
        ]
        
        if not filtered_reasons:
            filtered_reasons = ["Standard validation completed with no significant adjustments"]
        
        return filtered_reasons

    async def _publish_validation_result(self, original_event: AnomalyDetectedEvent, alert: AnomalyAlert, 
                                       reading: SensorReading, final_confidence: float, 
                                       validation_status: ValidationDecision, reasons: List[str],
                                       event_correlation_id: str, log_correlation_id: str) -> None:
        """Publish the validation result event."""
        try:
            validated_event_payload = {
                "original_anomaly_alert_payload": original_event.anomaly_details,
                "triggering_reading_payload": original_event.triggering_data,
                "validation_status": validation_status.value,
                "final_confidence": final_confidence,
                "validation_reasons": reasons,
                "agent_id": self.agent_id,
                "correlation_id": event_correlation_id
            }

            validated_event = AnomalyValidatedEvent(**validated_event_payload)
            
            if self.event_bus:
                await self.event_bus.publish(validated_event)
                self.logger.info(
                    f"Published AnomalyValidatedEvent for sensor {alert.sensor_id}",
                    extra={"correlation_id": log_correlation_id}
                )
            else:
                self.logger.error(
                    f"Cannot publish validation result: EventBus not available",
                    extra={"correlation_id": log_correlation_id}
                )
                
        except Exception as e:
            self.logger.error(
                f"Failed to publish validation result for {alert.sensor_id}: {e}",
                exc_info=True, extra={"correlation_id": log_correlation_id}
            )

    async def _update_metrics_and_profiles(self, sensor_id: str, validation_status: ValidationDecision,
                                         confidence_adjustment: float, start_time: float, correlation_id: str) -> None:
        """Update metrics and sensor profiles."""
        # Update global metrics
        processing_time = time.time() - start_time
        self.processing_times.append(processing_time)
        
        self.metrics.total_validations += 1
        if validation_status == ValidationDecision.CREDIBLE_ANOMALY:
            self.metrics.credible_anomalies += 1
        elif validation_status == ValidationDecision.FALSE_POSITIVE_SUSPECTED:
            self.metrics.false_positives += 1
        elif validation_status == ValidationDecision.FURTHER_INVESTIGATION_NEEDED:
            self.metrics.investigation_needed += 1
        
        # Update average processing time
        if self.processing_times:
            self.metrics.avg_processing_time = sum(self.processing_times) / len(self.processing_times)
        
        # Update sensor profile
        if sensor_id in self.sensor_profiles:
            profile = self.sensor_profiles[sensor_id]
            if validation_status == ValidationDecision.CREDIBLE_ANOMALY:
                profile.credible_count += 1
            elif validation_status == ValidationDecision.FALSE_POSITIVE_SUSPECTED:
                profile.false_positive_count += 1
            
            # Update average confidence adjustment
            total_adjustments = profile.total_validations * profile.avg_confidence_adjustment + confidence_adjustment
            profile.avg_confidence_adjustment = total_adjustments / (profile.total_validations + 1)

    def _is_db_circuit_breaker_open(self) -> bool:
        """Check if database circuit breaker is open."""
        if not self.enable_circuit_breaker:
            return False
        
        if self.db_circuit_breaker_open:
            if (self.db_circuit_breaker_last_failure and 
                datetime.utcnow() - self.db_circuit_breaker_last_failure > 
                timedelta(seconds=self.db_circuit_breaker_timeout)):
                self.db_circuit_breaker_open = False
                self.db_circuit_breaker_failures = 0
                self.logger.info("Database circuit breaker reset")
                return False
            return True
        
        return False

    def _increment_db_circuit_breaker(self) -> None:
        """Increment database circuit breaker failure count."""
        if not self.enable_circuit_breaker:
            return
        
        self.db_circuit_breaker_failures += 1
        self.db_circuit_breaker_last_failure = datetime.utcnow()
        
        if self.db_circuit_breaker_failures >= self.db_circuit_breaker_threshold:
            self.db_circuit_breaker_open = True
            self.logger.warning(
                f"Database circuit breaker opened due to {self.db_circuit_breaker_failures} failures"
            )

    def _reset_db_circuit_breaker(self) -> None:
        """Reset database circuit breaker on successful operation."""
        if self.enable_circuit_breaker and self.db_circuit_breaker_failures > 0:
            self.db_circuit_breaker_failures = 0
            self.db_circuit_breaker_open = False

    async def get_validation_metrics(self) -> Dict[str, Any]:
        """Get current validation metrics."""
        success_rate = 0.0
        if self.metrics.total_validations > 0:
            successful_validations = self.metrics.credible_anomalies + self.metrics.false_positives
            success_rate = successful_validations / self.metrics.total_validations
        
        return {
            'total_validations': self.metrics.total_validations,
            'credible_anomalies': self.metrics.credible_anomalies,
            'false_positives': self.metrics.false_positives,
            'investigation_needed': self.metrics.investigation_needed,
            'validation_errors': self.metrics.validation_errors,
            'success_rate': success_rate,
            'avg_processing_time': self.metrics.avg_processing_time,
            'sensor_count': len(self.sensor_profiles),
            'db_circuit_breaker_open': self.db_circuit_breaker_open,
            'db_circuit_breaker_failures': self.db_circuit_breaker_failures,
            'cache_size': len(self.historical_data_cache) + len(self.rule_results_cache),
            'batch_queue_size': len(self.batch_queue)
        }

    async def get_sensor_validation_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get sensor validation profiles."""
        return {
            sensor_id: {
                'total_validations': profile.total_validations,
                'credible_count': profile.credible_count,
                'false_positive_count': profile.false_positive_count,
                'credible_rate': profile.credible_count / max(1, profile.total_validations),
                'avg_confidence_adjustment': profile.avg_confidence_adjustment,
                'last_validation': profile.last_validation.isoformat() if profile.last_validation else None
            }
            for sensor_id, profile in self.sensor_profiles.items()
        }

    async def reset_metrics(self) -> None:
        """Reset validation metrics."""
        self.metrics = ValidationMetrics()
        self.processing_times.clear()
        self.logger.info("Validation metrics reset")

    async def clear_cache(self) -> None:
        """Clear validation caches."""
        self.historical_data_cache.clear()
        self.rule_results_cache.clear()
        self.logger.info("Validation caches cleared")

    async def _fetch_historical_data(self, sensor_id: str, before_timestamp: datetime, 
                                   limit: int = 20, correlation_id: Optional[str] = None) -> Tuple[List[SensorReading], Optional[str]]:
        """Fetch historical sensor readings with enhanced error handling."""
        self.logger.debug(
            f"Fetching historical data for sensor {sensor_id} before {before_timestamp}",
            extra={"correlation_id": correlation_id}
        )

        if not self.db_session_factory:
            error_msg = "Cannot fetch historical data: Database session factory not provided"
            self.logger.warning(error_msg, extra={"correlation_id": correlation_id})
            return [], error_msg

        session: Optional[AsyncSession] = None
        try:
            session = self.db_session_factory()
            historical_readings_orm = await self.crud_sensor_reading.get_sensor_readings_by_sensor_id(
                db=session,
                sensor_id=sensor_id,
                end_time=before_timestamp,
                limit=limit
            )
            
            # Convert ORM objects to Pydantic schemas
            historical_readings = [
                self.crud_sensor_reading.orm_to_pydantic(orm_obj) 
                for orm_obj in historical_readings_orm if orm_obj
            ]
            
            self.logger.debug(
                f"Fetched {len(historical_readings)} historical readings for sensor {sensor_id}",
                extra={"correlation_id": correlation_id}
            )
            return historical_readings, None
            
        except Exception as e:
            error_msg = f"Historical data fetch failed: {str(e)}"
            self.logger.error(
                f"Error fetching historical data for sensor {sensor_id}: {e}",
                exc_info=True,
                extra={"correlation_id": correlation_id}
            )
            return [], error_msg
            
        finally:
            if session and hasattr(session, 'close'):
                if asyncio.iscoroutinefunction(session.close):
                    await session.close()
                else:
                    session.close()
                self.logger.debug(
                    "Database session closed after fetching historical data",
                    extra={"correlation_id": correlation_id}
                )
