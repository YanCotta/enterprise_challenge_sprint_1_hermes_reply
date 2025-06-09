"""
PredictionAgent: An AI agent responsible for generating time-to-failure predictions.

This agent subscribes to AnomalyValidatedEvent, analyzes historical sensor data,
and uses the Prophet library to make maintenance predictions. It publishes
MaintenancePredictedEvent containing predictions and recommendations.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Tuple

try:
    import pandas as pd
    from prophet import Prophet
except ImportError as e:
    raise ImportError(f"Required dependencies not available: {e}. Please install Prophet and pandas.")

# Core application imports
from core.base_agent_abc import BaseAgent, AgentCapability
from core.events.event_bus import EventBus
from core.database.crud.crud_sensor_reading import CRUDSensorReading
from core.events.event_models import AnomalyValidatedEvent, MaintenancePredictedEvent
from data.schemas import SensorReading

# Import AsyncSession for type hinting
from sqlalchemy.ext.asyncio import AsyncSession


class PredictionAgent(BaseAgent):
    """
    Agent responsible for time-to-failure predictions using Prophet ML library.
    
    Event Flow: 
    AnomalyValidatedEvent -> PredictionAgent -> MaintenancePredictedEvent
    
    The agent fetches historical sensor data, prepares it for Prophet modeling,
    trains the model, generates predictions, and publishes maintenance recommendations.
    """

    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        crud_sensor_reading: CRUDSensorReading,
        db_session_factory: Optional[Callable[[], AsyncSession]] = None,
        specific_settings: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the PredictionAgent.
        
        Args:
            agent_id: Unique identifier for this agent instance
            event_bus: EventBus instance for event communication
            crud_sensor_reading: CRUD interface for sensor data access
            db_session_factory: Factory function to create database sessions
            specific_settings: Configuration settings specific to this agent
        """
        super().__init__(agent_id=agent_id, event_bus=event_bus)
        self.logger = logging.getLogger(f"{__name__}.{self.agent_id}")
        self.crud_sensor_reading = crud_sensor_reading
        self.db_session_factory = db_session_factory
        self.settings = specific_settings or {}

        # Event type configuration
        self.input_event_type = AnomalyValidatedEvent.__name__
        self.output_event_type = MaintenancePredictedEvent.__name__
        
        # Configuration parameters with defaults
        self.min_historical_points = self.settings.get("min_historical_points", 30)
        self.prediction_horizon_days = self.settings.get("prediction_horizon_days", 90)
        self.historical_data_limit = self.settings.get("historical_data_limit", 1000)
        self.confidence_threshold = self.settings.get("prediction_confidence_threshold", 0.6)
        
        self.logger.info(
            f"PredictionAgent '{self.agent_id}' initialized. "
            f"Input: {self.input_event_type}, Output: {self.output_event_type}. "
            f"Min historical points: {self.min_historical_points}, "
            f"Prediction horizon: {self.prediction_horizon_days} days, "
            f"Historical data limit: {self.historical_data_limit}, "
            f"Confidence threshold: {self.confidence_threshold}"
        )

    async def register_capabilities(self) -> None:
        """Register agent capabilities."""
        self.capabilities.append(
            AgentCapability(
                name="time_to_failure_prediction",
                description="Generates time-to-failure predictions using Prophet ML library",
                input_types=[self.input_event_type],
                output_types=[self.output_event_type]
            )
        )
        self.logger.info(
            f"Agent {self.agent_id}: Registered capability - "
            f"Consumes: {self.input_event_type}, Produces: {self.output_event_type}"
        )

    async def start(self) -> None:
        """Start the agent and subscribe to AnomalyValidatedEvent."""
        await super().start()  # Call BaseAgent.start() which registers capabilities
        if self.event_bus:
            await self.event_bus.subscribe(
                event_type_name=self.input_event_type, 
                handler=self.process
            )
            self.logger.info(
                f"Agent {self.agent_id} started and subscribed to '{self.input_event_type}'."
            )
        else:
            self.logger.error(f"Agent {self.agent_id} cannot start: EventBus not provided.")

    async def stop(self) -> None:
        """Stop the agent and unsubscribe from events."""
        if self.event_bus:
            await self.event_bus.unsubscribe(
                event_type_name=self.input_event_type, 
                handler=self.process
            )
            self.logger.info(
                f"Agent {self.agent_id} stopped and unsubscribed from '{self.input_event_type}'."
            )
        else:
            self.logger.warning(
                f"Agent {self.agent_id} cannot stop gracefully: EventBus not provided during init."
            )
        await super().stop()

    async def process(self, event: AnomalyValidatedEvent) -> None:
        """
        Main processing method for AnomalyValidatedEvent.
        
        Args:
            event: The AnomalyValidatedEvent to process
        """
        log_correlation_id = getattr(event, 'correlation_id', 'N/A')
        self.logger.info(
            f"Processing AnomalyValidatedEvent {getattr(event, 'event_id', 'N/A')} "
            f"(Correlation ID: {log_correlation_id})"
        )

        try:
            # 1. Extract sensor information from the event
            sensor_id = self._extract_sensor_id(event)
            equipment_id = self._extract_equipment_id(event)
            
            if not sensor_id:
                self.logger.error(f"Cannot extract sensor_id from event {getattr(event, 'event_id', 'N/A')}")
                return

            # 2. Only process confirmed anomalies or high confidence cases
            if not self._should_generate_prediction(event):
                self.logger.info(
                    f"Skipping prediction for event {getattr(event, 'event_id', 'N/A')}: "
                    f"validation status '{event.validation_status}' or confidence "
                    f"{event.final_confidence} below threshold"
                )
                return

            # 3. Fetch historical data for prediction
            self.logger.debug(f"Fetching historical data for sensor {sensor_id}")
            historical_data, error_msg = await self._fetch_historical_data_for_prediction(
                sensor_id=sensor_id,
                limit=self.historical_data_limit
            )

            if error_msg:
                self.logger.error(f"Failed to fetch historical data: {error_msg}")
                return

            if len(historical_data) < self.min_historical_points:
                self.logger.warning(
                    f"Insufficient historical data for prediction: "
                    f"{len(historical_data)} points (minimum required: {self.min_historical_points})"
                )
                return

            # 4. Prepare data for Prophet
            prophet_data = self._prepare_prophet_data(historical_data)
            if prophet_data is None or len(prophet_data) < self.min_historical_points:
                self.logger.error("Failed to prepare data for Prophet modeling")
                return

            # 5. Generate prediction using Prophet
            prediction_result = await self._generate_prediction(prophet_data, sensor_id)
            if not prediction_result:
                self.logger.error("Failed to generate prediction")
                return

            # 6. Create and publish MaintenancePredictedEvent
            await self._publish_maintenance_prediction(
                event=event,
                equipment_id=equipment_id,
                sensor_id=sensor_id,
                prediction_result=prediction_result
            )

        except Exception as e:
            self.logger.error(
                f"Unhandled error processing AnomalyValidatedEvent "
                f"{getattr(event, 'event_id', 'N/A')} (Correlation ID: {log_correlation_id}): {e}",
                exc_info=True,
            )

    def _extract_sensor_id(self, event: AnomalyValidatedEvent) -> Optional[str]:
        """Extract sensor_id from the event payload."""
        try:
            # Try to get sensor_id from original anomaly alert payload
            if isinstance(event.original_anomaly_alert_payload, dict):
                sensor_id = event.original_anomaly_alert_payload.get('sensor_id')
                if sensor_id:
                    return sensor_id
            
            # Try to get sensor_id from triggering reading payload
            if isinstance(event.triggering_reading_payload, dict):
                sensor_id = event.triggering_reading_payload.get('sensor_id')
                if sensor_id:
                    return sensor_id
                    
            self.logger.warning("Could not extract sensor_id from event payloads")
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting sensor_id: {e}")
            return None

    def _extract_equipment_id(self, event: AnomalyValidatedEvent) -> str:
        """Extract or derive equipment_id from the event."""
        try:
            # First try to get equipment_id from anomaly alert payload
            if isinstance(event.original_anomaly_alert_payload, dict):
                equipment_id = event.original_anomaly_alert_payload.get('equipment_id')
                if equipment_id:
                    return equipment_id
            
            # Second, try to get equipment_id from triggering reading payload metadata
            if isinstance(event.triggering_reading_payload, dict):
                metadata = event.triggering_reading_payload.get('metadata', {})
                if isinstance(metadata, dict):
                    equipment_id = metadata.get('equipment_id')
                    if equipment_id:
                        return equipment_id
            
            # If not found, use sensor_id as equipment_id (common pattern)
            sensor_id = self._extract_sensor_id(event)
            if sensor_id:
                # Convert sensor_id to equipment_id format
                return f"equipment_{sensor_id}"
            
            # Fallback to a generic identifier
            return f"equipment_unknown_{getattr(event, 'event_id', 'N/A')}"
            
        except Exception as e:
            self.logger.error(f"Error extracting equipment_id: {e}")
            return f"equipment_error_{getattr(event, 'event_id', 'N/A')}"

    def _should_generate_prediction(self, event: AnomalyValidatedEvent) -> bool:
        """Determine if a prediction should be generated based on validation results."""
        # Only generate predictions for confirmed anomalies or high confidence cases
        confirmed_statuses = ["CONFIRMED", "credible_anomaly"]
        
        return (
            event.validation_status in confirmed_statuses or
            event.final_confidence >= self.confidence_threshold
        )

    async def _fetch_historical_data_for_prediction(
        self, sensor_id: str, limit: int = 1000
    ) -> Tuple[List[SensorReading], Optional[str]]:
        """
        Fetch historical sensor readings for prediction modeling.
        
        Returns:
            Tuple of (readings_list, error_message)
        """
        if not self.db_session_factory:
            error_msg = "Cannot fetch historical data: Database session factory not provided."
            self.logger.error(error_msg)
            return [], error_msg

        session: Optional[AsyncSession] = None
        try:
            session = self.db_session_factory()
            
            # Fetch data from the last reasonable time period (e.g., 1 year)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=365)
            
            historical_readings_orm = await self.crud_sensor_reading.get_sensor_readings_by_sensor_id(
                db=session,
                sensor_id=sensor_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            
            # Convert ORM objects to Pydantic SensorReading schemas
            historical_readings = [
                SensorReading.model_validate(orm_obj) 
                for orm_obj in historical_readings_orm 
                if orm_obj
            ]
            
            self.logger.info(
                f"Fetched {len(historical_readings)} historical readings for sensor {sensor_id} "
                f"from {start_time} to {end_time}"
            )
            return historical_readings, None
            
        except Exception as e:
            error_msg = f"Error fetching historical data for sensor {sensor_id}: {e}"
            self.logger.error(error_msg, exc_info=True)
            return [], error_msg
            
        finally:
            if session and hasattr(session, 'close'):
                if asyncio.iscoroutinefunction(session.close):
                    await session.close()
                else:
                    session.close()
                self.logger.debug("Database session closed after fetching historical data.")

    def _prepare_prophet_data(self, historical_readings: List[SensorReading]) -> Optional[pd.DataFrame]:
        """
        Prepare historical sensor data for Prophet modeling.
        
        Prophet expects a DataFrame with 'ds' (datestamp) and 'y' (value) columns.
        
        Args:
            historical_readings: List of SensorReading objects
            
        Returns:
            DataFrame formatted for Prophet, or None if preparation fails
        """
        try:
            if not historical_readings:
                self.logger.warning("No historical readings provided for Prophet data preparation")
                return None

            # Convert to pandas DataFrame
            data = []
            for reading in historical_readings:
                # Remove timezone info for Prophet compatibility
                timestamp = reading.timestamp
                if timestamp.tzinfo is not None:
                    timestamp = timestamp.replace(tzinfo=None)
                
                data.append({
                    'ds': timestamp,  # datestamp (timezone-naive)
                    'y': reading.value       # value to predict
                })
            
            df = pd.DataFrame(data)
            
            # Sort by timestamp to ensure chronological order
            df = df.sort_values('ds').reset_index(drop=True)
            
            # Remove any duplicate timestamps (keep last)
            df = df.drop_duplicates(subset=['ds'], keep='last')
            
            # Remove any rows with null values
            df = df.dropna()
            
            self.logger.debug(
                f"Prepared Prophet data: {len(df)} points from "
                f"{df['ds'].min()} to {df['ds'].max()}"
            )
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error preparing Prophet data: {e}", exc_info=True)
            return None

    async def _generate_prediction(
        self, prophet_data: pd.DataFrame, sensor_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Generate time-to-failure prediction using Prophet.
        
        Args:
            prophet_data: DataFrame formatted for Prophet
            sensor_id: Sensor identifier for logging
            
        Returns:
            Dictionary containing prediction results, or None if prediction fails
        """
        try:
            self.logger.debug(f"Starting Prophet prediction for sensor {sensor_id}")
            
            # Initialize Prophet model
            # Configure based on data characteristics
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.05,  # Less sensitive to trend changes
                seasonality_prior_scale=10.0,  # More flexible seasonalities
                interval_width=0.8  # 80% confidence intervals
            )
            
            # Train the model
            model.fit(prophet_data)
            
            # Create future dataframe for prediction
            future = model.make_future_dataframe(
                periods=self.prediction_horizon_days, 
                freq='D'
            )
            
            # Generate predictions
            forecast = model.predict(future)
            
            # Analyze trend and determine failure prediction
            prediction_result = self._analyze_forecast_for_failure(
                forecast=forecast, 
                historical_data=prophet_data,
                sensor_id=sensor_id
            )
            
            # Calculate model performance metrics
            metrics = self._calculate_model_metrics(
                model=model, 
                historical_data=prophet_data, 
                forecast=forecast
            )
            
            prediction_result['model_metrics'] = metrics
            prediction_result['historical_data_points'] = len(prophet_data)
            
            self.logger.info(
                f"Generated prediction for sensor {sensor_id}: "
                f"failure in {prediction_result.get('time_to_failure_days', 'N/A')} days"
            )
            
            return prediction_result
            
        except Exception as e:
            self.logger.error(f"Error generating Prophet prediction for sensor {sensor_id}: {e}", exc_info=True)
            return None

    def _analyze_forecast_for_failure(
        self, forecast: pd.DataFrame, historical_data: pd.DataFrame, sensor_id: str
    ) -> Dict[str, Any]:
        """
        Analyze Prophet forecast to determine failure prediction.
        
        This is a simplified failure prediction logic. In practice, you would
        implement domain-specific rules based on sensor type, threshold values,
        trend analysis, etc.
        """
        try:
            # Get the last historical value and trend
            last_historical_date = historical_data['ds'].max()
            last_historical_value = historical_data[historical_data['ds'] == last_historical_date]['y'].iloc[0]
            
            # Get future predictions only
            future_forecast = forecast[forecast['ds'] > last_historical_date].copy()
            
            if len(future_forecast) == 0:
                raise ValueError("No future predictions available")
            
            # Analyze trend - this is simplified logic
            # You would customize this based on your specific use case
            
            # Calculate trend slope over next 30 days
            if len(future_forecast) >= 30:
                trend_period = future_forecast.head(30)
                trend_slope = (trend_period['yhat'].iloc[-1] - trend_period['yhat'].iloc[0]) / 30
            else:
                trend_slope = (future_forecast['yhat'].iloc[-1] - future_forecast['yhat'].iloc[0]) / len(future_forecast)
            
            # Determine failure based on trend and thresholds
            # This is domain-specific logic that you would customize
            failure_threshold_multiplier = 2.0  # Configurable based on sensor type
            failure_threshold = last_historical_value * failure_threshold_multiplier
            
            # Find when the prediction crosses the failure threshold
            failure_predictions = future_forecast[future_forecast['yhat'] >= failure_threshold]
            
            if len(failure_predictions) > 0:
                # Failure predicted
                failure_date = failure_predictions.iloc[0]['ds']
                confidence_lower = failure_predictions.iloc[0]['yhat_lower']
                confidence_upper = failure_predictions.iloc[0]['yhat_upper']
                time_to_failure = (failure_date - datetime.utcnow()).days
                
                # Ensure time_to_failure is non-negative (Pydantic validation requirement)
                if time_to_failure < 0:
                    # If failure is predicted in the past, treat as immediate failure
                    time_to_failure = 1  # 1 day minimum for immediate maintenance
                    failure_date = datetime.utcnow() + timedelta(days=1)
                
                # Calculate prediction confidence based on confidence interval width
                confidence_width = confidence_upper - confidence_lower
                relative_confidence = max(0.0, min(1.0, 1.0 - (confidence_width / failure_threshold)))
                
            else:
                # No failure predicted within horizon
                failure_date = datetime.utcnow() + timedelta(days=self.prediction_horizon_days * 2)
                confidence_lower = failure_date - timedelta(days=30)
                confidence_upper = failure_date + timedelta(days=30)
                time_to_failure = (failure_date - datetime.utcnow()).days
                relative_confidence = 0.3  # Lower confidence for long-term predictions
            
            # Determine maintenance type based on time to failure
            if time_to_failure <= 7:
                maintenance_type = "urgent_corrective"
            elif time_to_failure <= 30:
                maintenance_type = "preventive"
            else:
                maintenance_type = "inspection"
            
            # Generate recommendations
            recommendations = self._generate_maintenance_recommendations(
                time_to_failure=time_to_failure,
                maintenance_type=maintenance_type,
                trend_slope=trend_slope
            )
            
            return {
                'predicted_failure_date': failure_date,
                'confidence_interval_lower': confidence_lower,
                'confidence_interval_upper': confidence_upper,
                'prediction_confidence': relative_confidence,
                'time_to_failure_days': float(time_to_failure),
                'maintenance_type': maintenance_type,
                'recommended_actions': recommendations,
                'trend_slope': trend_slope,
                'failure_threshold': failure_threshold
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing forecast for sensor {sensor_id}: {e}", exc_info=True)
            # Return a conservative default prediction
            return {
                'predicted_failure_date': datetime.utcnow() + timedelta(days=90),
                'confidence_interval_lower': datetime.utcnow() + timedelta(days=60),
                'confidence_interval_upper': datetime.utcnow() + timedelta(days=120),
                'prediction_confidence': 0.3,
                'time_to_failure_days': 90.0,
                'maintenance_type': 'inspection',
                'recommended_actions': ['Schedule routine inspection', 'Monitor sensor readings'],
                'trend_slope': 0.0,
                'failure_threshold': 0.0
            }

    def _generate_maintenance_recommendations(
        self, time_to_failure: float, maintenance_type: str, trend_slope: float
    ) -> List[str]:
        """Generate maintenance recommendations based on prediction results."""
        recommendations = []
        
        if maintenance_type == "urgent_corrective":
            recommendations.extend([
                "Schedule immediate maintenance intervention",
                "Prepare replacement parts and tools",
                "Assign experienced technician",
                "Consider temporary shutdown if critical"
            ])
        elif maintenance_type == "preventive":
            recommendations.extend([
                "Schedule preventive maintenance within recommended timeframe",
                "Order replacement parts in advance",
                "Plan maintenance during next scheduled downtime",
                "Increase monitoring frequency"
            ])
        else:  # inspection
            recommendations.extend([
                "Schedule routine inspection",
                "Monitor sensor readings for trend changes",
                "Review maintenance history",
                "Consider preventive maintenance planning"
            ])
        
        # Add trend-specific recommendations
        if abs(trend_slope) > 0.1:  # Significant trend
            if trend_slope > 0:
                recommendations.append("Monitor upward trend in sensor readings")
            else:
                recommendations.append("Monitor downward trend in sensor readings")
        
        return recommendations

    def _calculate_model_metrics(
        self, model: Prophet, historical_data: pd.DataFrame, forecast: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate model performance metrics."""
        try:
            # Calculate metrics on historical data
            historical_forecast = forecast[forecast['ds'].isin(historical_data['ds'])]
            
            if len(historical_forecast) == 0:
                return {'mae': 0.0, 'rmse': 0.0, 'mape': 0.0}
            
            # Merge historical data with forecast
            merged = historical_data.merge(historical_forecast[['ds', 'yhat']], on='ds')
            
            if len(merged) == 0:
                return {'mae': 0.0, 'rmse': 0.0, 'mape': 0.0}
            
            # Calculate metrics
            errors = merged['y'] - merged['yhat']
            mae = float(abs(errors).mean())
            rmse = float((errors ** 2).mean() ** 0.5)
            
            # Calculate MAPE (Mean Absolute Percentage Error)
            mape = float((abs(errors / merged['y']).mean() * 100))
            
            return {
                'mae': mae,
                'rmse': rmse,
                'mape': mape
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating model metrics: {e}")
            return {'mae': 0.0, 'rmse': 0.0, 'mape': 0.0}

    async def _publish_maintenance_prediction(
        self,
        event: AnomalyValidatedEvent,
        equipment_id: str,
        sensor_id: str,
        prediction_result: Dict[str, Any]
    ) -> None:
        """Publish MaintenancePredictedEvent with prediction results."""
        try:
            # Create MaintenancePredictedEvent payload
            prediction_payload = {
                'original_anomaly_event_id': event.event_id,
                'equipment_id': equipment_id,
                'predicted_failure_date': prediction_result['predicted_failure_date'],
                'confidence_interval_lower': prediction_result['confidence_interval_lower'],
                'confidence_interval_upper': prediction_result['confidence_interval_upper'],
                'prediction_confidence': prediction_result['prediction_confidence'],
                'time_to_failure_days': prediction_result['time_to_failure_days'],
                'maintenance_type': prediction_result['maintenance_type'],
                'prediction_method': 'prophet',
                'historical_data_points': prediction_result['historical_data_points'],
                'model_metrics': prediction_result['model_metrics'],
                'recommended_actions': prediction_result['recommended_actions'],
                'agent_id': self.agent_id,
                'correlation_id': getattr(event, 'correlation_id', None)
            }
            
            # Create the event
            maintenance_event = MaintenancePredictedEvent(**prediction_payload)
            
            # Publish the event
            if self.event_bus:
                await self.event_bus.publish(maintenance_event)
                self.logger.info(
                    f"Published MaintenancePredictedEvent {maintenance_event.event_id} "
                    f"for equipment {equipment_id} (sensor {sensor_id}). "
                    f"Predicted failure in {prediction_result['time_to_failure_days']:.1f} days."
                )
            else:
                self.logger.error("Cannot publish MaintenancePredictedEvent: EventBus not available.")
                
        except Exception as e:
            self.logger.error(f"Error publishing MaintenancePredictedEvent: {e}", exc_info=True)
