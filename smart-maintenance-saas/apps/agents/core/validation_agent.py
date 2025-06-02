import logging
import asyncio # For potential async operations if needed, though not strictly in this snippet
from datetime import datetime, timedelta # For historical data fetching
from typing import Tuple, List, Any, Optional, Callable # Standard typing imports, added Callable

# Core application imports - CRITICAL: Ensure these paths are correct for absolute imports
from smart_maintenance_saas.apps.agents.base_agent import BaseAgent
from smart_maintenance_saas.core.events.event_bus import EventBus
from smart_maintenance_saas.core.database.crud.crud_sensor_reading import CRUDSensorReading # Instance expected
from smart_maintenance_saas.apps.rules.validation_rules import RuleEngine # Instance expected
from smart_maintenance_saas.core.events.event_models import AnomalyDetectedEvent, AnomalyValidatedEvent
from smart_maintenance_saas.data.schemas import AnomalyAlert, SensorReading # Pydantic models for parsing

# Import AsyncSession for type hinting if a session factory is used
from sqlalchemy.ext.asyncio import AsyncSession 

class ValidationAgent(BaseAgent):
    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        crud_sensor_reading: CRUDSensorReading, # Pass an instance
        rule_engine: RuleEngine, # Pass an instance
        db_session_factory: Optional[Callable[[], AsyncSession]] = None # Session factory for DB access
    ):
        super().__init__(agent_id=agent_id, event_bus=event_bus)
        self.logger = logging.getLogger(f"{__name__}.{self.agent_id}")
        self.crud_sensor_reading = crud_sensor_reading
        self.rule_engine = rule_engine
        self.db_session_factory = db_session_factory # Store session factory

        self.input_event_type = AnomalyDetectedEvent.__name__
        self.output_event_type = AnomalyValidatedEvent.__name__
        self.logger.info(
            f"ValidationAgent '{self.agent_id}' initialized. "
            f"Input: {self.input_event_type}, Output: {self.output_event_type}. "
            f"DB Session Factory provided: {self.db_session_factory is not None}"
        )

    async def register_capabilities(self):
        '''Declares the agent's capabilities.'''
        self.logger.info(
            f"Agent {self.agent_id}: Declaring capability - Consumes: {self.input_event_type}, Produces: {self.output_event_type}"
        )
        # Actual registration logic might be in BaseAgent or handled by an external registry.

    async def start(self):
        '''Subscribes the agent to relevant events.'''
        if self.event_bus: # Ensure event_bus is provided
            await self.event_bus.subscribe(
                event_type=self.input_event_type, handler=self.process
            )
            self.logger.info(
                f"Agent {self.agent_id} started and subscribed to '{self.input_event_type}'."
            )
        else:
            self.logger.error(f"Agent {self.agent_id} cannot start: EventBus not provided.")


    async def stop(self):
        '''Unsubscribes the agent from events.'''
        if self.event_bus: # Ensure event_bus is provided
            await self.event_bus.unsubscribe(
                event_type=self.input_event_type, handler=self.process
            )
            self.logger.info(
                f"Agent {self.agent_id} stopped and unsubscribed from '{self.input_event_type}'."
            )
        else:
            self.logger.warning(f"Agent {self.agent_id} cannot stop gracefully: EventBus not provided during init.")


    async def _fetch_historical_data(
        self, sensor_id: str, before_timestamp: datetime, limit: int = 20
    ) -> List[SensorReading]:
        '''Helper to fetch historical sensor readings using a DB session from the factory.'''
        self.logger.debug(f"Fetching historical data for sensor {sensor_id} before {before_timestamp}")

        if not self.db_session_factory:
            self.logger.error(
                "Cannot fetch historical data: Database session factory not provided to ValidationAgent."
            )
            return []

        session: Optional[AsyncSession] = None
        try:
            session = self.db_session_factory() # Obtain a new session
            historical_readings_orm = await self.crud_sensor_reading.get_sensor_readings_by_sensor_id(
                db=session, # Pass the active session
                sensor_id=sensor_id,
                end_time=before_timestamp, # Match CRUD param name
                limit=limit
            )
            # Convert ORM objects to Pydantic SensorReading schemas
            historical_readings = [SensorReading.model_validate(orm_obj) for orm_obj in historical_readings_orm if orm_obj]
            self.logger.info(f"Fetched {len(historical_readings)} historical readings for sensor {sensor_id}.")
            return historical_readings
        except Exception as e:
            self.logger.error(f"Error fetching historical data for sensor {sensor_id}: {e}", exc_info=True)
            return []
        finally:
            if session:
                await session.close() # Ensure session is closed
                self.logger.debug("Database session closed after fetching historical data.")


    async def _perform_historical_validation(
        self, alert: AnomalyAlert, reading: SensorReading, historical_readings: List[SensorReading]
    ) -> Tuple[float, List[str]]:
        '''Performs validation based on historical context.'''
        historical_confidence_adjustment = 0.0
        historical_reasons = []

        if not historical_readings:
            historical_reasons.append("No historical readings available for comparison.")
            self.logger.debug("Historical validation: No historical data.")
            return historical_confidence_adjustment, historical_reasons

        # Rule 1: Recent Value Stability (Example)
        if len(historical_readings) >= 5:
            recent_values = [r.value for r in historical_readings[:5]] # Assuming value is float/int
            avg_recent_value = sum(recent_values) / len(recent_values)
            # Calculate variance, then standard deviation
            variance = sum([(x - avg_recent_value) ** 2 for x in recent_values]) / len(recent_values)
            std_dev_recent = variance ** 0.5

            # Check for stability: std dev is small relative to average or a small absolute value
            is_stable = std_dev_recent < (0.1 * abs(avg_recent_value) + 1e-6) or std_dev_recent < 0.05 # e.g. for very small values
            
            # Check for significant jump: current reading's value vs (avg +/- 3*std_dev)
            # Ensure reading.value is float/int for comparison
            current_value = reading.value
            if isinstance(current_value, (int, float)):
                if is_stable:
                    if abs(current_value - avg_recent_value) > 3 * (std_dev_recent + 1e-3): # Add small epsilon to avoid division by zero if std_dev is tiny
                        historical_confidence_adjustment += 0.10
                        reason = f"Anomaly (value: {current_value}) deviates significantly from a recently stable baseline (avg: {avg_recent_value:.2f}, std_dev: {std_dev_recent:.2f})."
                        historical_reasons.append(reason)
                        self.logger.debug(f"Historical Rule (Jump from Stable) triggered: {reason}")
                    else:
                        historical_confidence_adjustment -= 0.05
                        reason = f"Anomaly (value: {current_value}) is a minor deviation from a recently stable baseline (avg: {avg_recent_value:.2f}, std_dev: {std_dev_recent:.2f})."
                        historical_reasons.append(reason)
                        self.logger.debug(f"Historical Rule (Minor Deviation from Stable) triggered: {reason}")
                else: # Not stable
                    historical_confidence_adjustment += 0.05 # Less change if baseline is already volatile
                    reason = f"Anomaly (value: {current_value}) occurred during a period of volatile readings (avg: {avg_recent_value:.2f}, std_dev: {std_dev_recent:.2f}). Less adjustment made."
                    historical_reasons.append(reason)
                    self.logger.debug(f"Historical Rule (Volatile Baseline) triggered: {reason}")
            else:
                self.logger.warning(f"Cannot apply historical stability rule: reading value '{current_value}' is not numeric.")

        if not historical_reasons:
            historical_reasons.append("No significant historical patterns affected confidence based on implemented rules.")
        
        self.logger.debug(f"Historical validation complete. Adjustment: {historical_confidence_adjustment}, Reasons: {historical_reasons}")
        return historical_confidence_adjustment, historical_reasons

    async def process(self, event: AnomalyDetectedEvent):
        '''Processes an AnomalyDetectedEvent to validate the anomaly.'''
        # Ensure correlation_id is available for logging and downstream events
        # AnomalyDetectedEvent should have event_id (from BaseEventModel) and may have its own correlation_id
        # BaseEventModel in the issue description does not show correlation_id, but AnomalyValidatedEvent is asked to have one.
        # Let's assume AnomalyDetectedEvent (as a BaseEventModel) might have a correlation_id or we use its event_id.
        # The AnomalyValidatedEvent is also asked to have correlation_id from incoming AnomalyDetectedEvent
        
        # Safely access correlation_id from event, fallback to event.event_id
        event_correlation_id = getattr(event, 'correlation_id', None)
        if event_correlation_id is None and hasattr(event, 'event_id'):
             event_correlation_id = str(event.event_id) # Use event_id if correlation_id is not present

        log_correlation_id = event_correlation_id or "N/A" # For logging if neither exists

        self.logger.info(
            f"Processing AnomalyDetectedEvent (ID: {getattr(event, 'event_id', 'N/A')}) "
            f"for sensor {getattr(event.anomaly_details, 'sensor_id', 'N/A') if isinstance(event.anomaly_details, dict) else getattr(event, 'sensor_id', 'N/A')} " # Check anomaly_details first
            f"(Correlation ID: {log_correlation_id})."
        )

        try:
            # 1. Parse event data into Pydantic models
            # AnomalyDetectedEvent has .anomaly_details and .triggering_data (both Dict[str, Any])
            if not isinstance(event.anomaly_details, dict) or not isinstance(event.triggering_data, dict):
                self.logger.error(f"Event {getattr(event, 'event_id', 'N/A')} has invalid payload structure. "
                                  f"anomaly_details or triggering_data is not a dict. Skipping. (Corr ID: {log_correlation_id})")
                return

            parsed_alert = AnomalyAlert(**event.anomaly_details)
            parsed_reading = SensorReading(**event.triggering_data)

            self.logger.debug(f"Parsed AnomalyAlert (Corr ID: {log_correlation_id}): {parsed_alert.model_dump_json(indent=2, exclude_none=True)}")
            self.logger.debug(f"Parsed SensorReading (Corr ID: {log_correlation_id}): {parsed_reading.model_dump_json(indent=2, exclude_none=True)}")

            # 2. Call RuleEngine
            rule_adj, rule_reasons = await self.rule_engine.evaluate_rules(
                alert=parsed_alert, reading=parsed_reading
            )
            self.logger.debug(f"Rule engine (Corr ID: {log_correlation_id}): Adjustment={rule_adj}, Reasons='{'; '.join(rule_reasons)}'")

            # 3. Historical Context Validation
            historical_readings = await self._fetch_historical_data(
                sensor_id=parsed_alert.sensor_id,
                before_timestamp=parsed_reading.timestamp,
                limit=20
            )
            
            hist_adj, hist_reasons = await self._perform_historical_validation(
                alert=parsed_alert, reading=parsed_reading, historical_readings=historical_readings
            )
            self.logger.debug(f"Historical validation (Corr ID: {log_correlation_id}): Adjustment={hist_adj}, Reasons='{'; '.join(hist_reasons)}'")

            # 4. Final Confidence & Status
            final_confidence = parsed_alert.confidence + rule_adj + hist_adj
            final_confidence = max(0.0, min(1.0, final_confidence))

            validation_status = "further_investigation_needed"
            if final_confidence >= 0.75:
                validation_status = "credible_anomaly"
            elif final_confidence < 0.4:
                validation_status = "false_positive_suspected"
            
            all_reasons = [r for r in rule_reasons + hist_reasons if r not in [
                "No rule-based adjustments applied.", 
                "No significant historical patterns affected confidence based on implemented rules.", 
                "No historical readings available for comparison."
                ]
            ]
            if not all_reasons: # If all reasons were generic, provide a default summary
                all_reasons = ["Standard validation checks completed; no specific rules or historical patterns significantly altered confidence."]

            self.logger.info(
                f"Validation result for sensor {parsed_alert.sensor_id} (Corr ID: {log_correlation_id}): "
                f"Final Confidence={final_confidence:.2f}, Status='{validation_status}'"
            )

            # 5. Publish AnomalyValidatedEvent
            validated_event_payload = {
                "original_anomaly_alert_payload": event.anomaly_details,
                "triggering_reading_payload": event.triggering_data,
                "validation_status": validation_status,
                "final_confidence": final_confidence,
                "validation_reasons": all_reasons,
                "agent_id": self.agent_id,
                "correlation_id": event_correlation_id # Pass through the determined correlation_id
                # validated_at is handled by default_factory in Pydantic model
                # event_id and timestamp for AnomalyValidatedEvent itself are handled by BaseEventModel's defaults
            }
            # Ensure event_type is set if BaseEventModel expects it (current one does not)
            # validated_event_payload["event_type"] = AnomalyValidatedEvent.__name__ # Add if needed

            validated_event = AnomalyValidatedEvent(**validated_event_payload)
            
            if self.event_bus:
                await self.event_bus.publish(event=validated_event)
                self.logger.info(
                    f"Published AnomalyValidatedEvent {getattr(validated_event, 'event_id', 'N/A')} "
                    f"for sensor {parsed_alert.sensor_id} (Corr ID: {log_correlation_id})."
                )
            else:
                self.logger.error(f"Cannot publish AnomalyValidatedEvent: EventBus not available. (Corr ID: {log_correlation_id})")


        except Exception as e:
            self.logger.error(
                f"Unhandled error processing AnomalyDetectedEvent {getattr(event, 'event_id', 'N/A')} "
                f"(Sensor: {getattr(parsed_alert, 'sensor_id', 'N/A') if 'parsed_alert' in locals() else getattr(event.anomaly_details, 'sensor_id', 'N/A') if isinstance(event.anomaly_details, dict) else 'N/A'}, Correlation ID: {log_correlation_id}): {e}",
                exc_info=True,
            )
            # Consider publishing a specific error event or using a dead-letter mechanism.
