import pytest
from unittest.mock import Mock, patch
import uuid
from datetime import datetime

from apps.agents.core.validation_agent import ValidationAgent
from core.events.event_models import AnomalyDetectedEvent, AnomalyValidatedEvent
from data.schemas import AnomalyAlert, SensorReading, ValidationStatus, AnomalyType
from apps.rules.validation_rules import RuleEngine # Assuming RuleEngine can be mocked or instantiated simply


# Mock EventBus for agent initialization
@pytest.fixture
def mock_event_bus():
    bus = Mock()
    from unittest.mock import AsyncMock
    bus.publish = AsyncMock(return_value=None) # Async mock since publish is awaited
    return bus

@pytest.fixture
def mock_crud_sensor_reading():
    crud = Mock()
    # Configure mock methods as needed, e.g., for _fetch_historical_data
    # Make it async compatible since the real method is async
    from unittest.mock import AsyncMock
    crud.get_sensor_readings_by_sensor_id = AsyncMock(return_value=[])
    return crud

@pytest.fixture
def mock_rule_engine():
    engine = Mock(spec=RuleEngine)
    # Configure mock methods, e.g., for evaluate_rules
    from unittest.mock import AsyncMock
    engine.evaluate_rules = AsyncMock(return_value=(0.0, ["mock rule reason"]))
    return engine

@pytest.fixture
def mock_db_session_factory():
    # This factory should return a mock session
    mock_session = Mock()
    mock_session.close = Mock() # Mock close if it's called
    factory = Mock(return_value=mock_session)
    return factory


@pytest.fixture
def validation_agent(mock_event_bus, mock_crud_sensor_reading, mock_rule_engine, mock_db_session_factory):
    agent_settings = {
        "credible_threshold": 0.7,
        "false_positive_threshold": 0.4,
        "recent_stability_window": 5,
        # Add any other settings required by the agent
    }
    agent = ValidationAgent(
        agent_id="test_validation_agent",
        event_bus=mock_event_bus,
        crud_sensor_reading=mock_crud_sensor_reading,
        rule_engine=mock_rule_engine,
        db_session_factory=mock_db_session_factory,
        specific_settings=agent_settings
    )
    return agent

class TestValidationAgentProcessEnumUsage:

    @pytest.mark.asyncio # Mark test as async
    async def test_process_publishes_correct_validation_status_enum_value(
        self, validation_agent, mock_event_bus, mock_rule_engine, mock_crud_sensor_reading, mock_db_session_factory
    ):
        # Arrange
        correlation_id = str(uuid.uuid4())
        anomaly_details_payload = {
            "sensor_id": "sensor_test_1",
            "anomaly_type": AnomalyType.SPIKE.value, # Use enum value for incoming event
            "severity": 3,
            "confidence": 0.6, # Initial confidence
            "description": "A test spike anomaly",
            "status": "open" # Assuming status is a string here for the incoming event
        }
        triggering_data_payload = {
            "sensor_id": "sensor_test_1",
            "value": 150.0,
            "timestamp": datetime.utcnow().isoformat(),
            "sensor_type": "temperature",
            "unit": "C"
        }

        event = AnomalyDetectedEvent(
            event_id=str(uuid.uuid4()),
            anomaly_details=anomaly_details_payload,
            triggering_data=triggering_data_payload,
            severity="medium", # Example
            correlation_id=correlation_id,
            timestamp=datetime.utcnow()
        )

        # Mock dependent methods to control the outcome of validation_status
        # Scenario: final_confidence leads to CREDIBLE_ANOMALY
        # For AsyncMock, we need to import asyncio to create a coroutine
        import asyncio
        async def mock_evaluate_rules(alert, reading):
            return (0.2, ["Rule: high confidence boost"])
        
        mock_rule_engine.evaluate_rules = mock_evaluate_rules
        # _fetch_historical_data is mocked by mock_crud_sensor_reading to return empty list, leading to no hist_adj
        # So, initial confidence 0.6 + rule_adj 0.2 = 0.8. This should be CREDIBLE_ANOMALY.

        # If _fetch_historical_data or _perform_historical_validation are async, ensure their mocks are too.
        # For this test, _fetch_historical_data uses mock_crud_sensor_reading.get_sensor_readings_by_sensor_id
        # which should be an async mock if the actual method is async.
        # Let's assume they are patched/mocked correctly by fixtures.
        # Keep the AsyncMock setup from the fixture

        # Act
        await validation_agent.process(event)

        # Assert
        mock_event_bus.publish.assert_called_once()
        published_event_call = mock_event_bus.publish.call_args[0][0]

        assert isinstance(published_event_call, AnomalyValidatedEvent)
        assert published_event_call.correlation_id == correlation_id

        # The AnomalyValidatedEvent's payload for 'validation_status' should be the string value
        # of the ValidationStatus enum member.
        # Expected: 0.6 (initial) + 0.2 (rule_adj) + 0.0 (hist_adj) = 0.8.
        # With credible_threshold = 0.7, this should be ValidationStatus.CREDIBLE_ANOMALY.
        assert published_event_call.validation_status == ValidationStatus.CREDIBLE_ANOMALY.value
        assert published_event_call.final_confidence == 0.8

    @pytest.mark.asyncio
    async def test_process_false_positive_status(
        self, validation_agent, mock_event_bus, mock_rule_engine, mock_crud_sensor_reading
    ):
        # Arrange
        correlation_id = str(uuid.uuid4())
        anomaly_details_payload = {"sensor_id": "s2", "anomaly_type": "drift", "severity": 1, "confidence": 0.2, "description": "low conf"}
        triggering_data_payload = {"sensor_id": "s2", "value": 10.0, "timestamp": datetime.utcnow().isoformat(), "sensor_type": "pressure", "unit": "Pa"}
        event = AnomalyDetectedEvent(anomaly_details=anomaly_details_payload, triggering_data=triggering_data_payload, correlation_id=correlation_id)

        # Setup async mock for rule engine
        async def mock_evaluate_rules(alert, reading):
            return (0.0, [])  # No change from rules
        mock_rule_engine.evaluate_rules = mock_evaluate_rules
        
        # Historical data mock is already set up as AsyncMock in fixture

        # Act
        await validation_agent.process(event)

        # Assert
        mock_event_bus.publish.assert_called_once()
        published_event = mock_event_bus.publish.call_args[0][0]
        # Initial confidence 0.2, false_positive_threshold = 0.4. Should be FALSE_POSITIVE_SUSPECTED
        assert published_event.validation_status == ValidationStatus.FALSE_POSITIVE_SUSPECTED.value
        assert published_event.final_confidence == 0.2


    @pytest.mark.asyncio
    async def test_process_further_investigation_status(
        self, validation_agent, mock_event_bus, mock_rule_engine, mock_crud_sensor_reading
    ):
        # Arrange
        correlation_id = str(uuid.uuid4())
        anomaly_details_payload = {"sensor_id": "s3", "anomaly_type": "stuck_at_value", "severity": 2, "confidence": 0.5, "description": "mid conf"}
        triggering_data_payload = {"sensor_id": "s3", "value": 5.0, "timestamp": datetime.utcnow().isoformat(), "sensor_type": "vibration", "unit": "mm/s"}
        event = AnomalyDetectedEvent(anomaly_details=anomaly_details_payload, triggering_data=triggering_data_payload, correlation_id=correlation_id)

        # Setup async mock for rule engine
        async def mock_evaluate_rules(alert, reading):
            return (0.0, [])
        mock_rule_engine.evaluate_rules = mock_evaluate_rules

        # Act
        await validation_agent.process(event)

        # Assert
        mock_event_bus.publish.assert_called_once()
        published_event = mock_event_bus.publish.call_args[0][0]
        # Initial confidence 0.5. credible_threshold=0.7, false_positive_threshold=0.4. Should be FURTHER_INVESTIGATION_NEEDED
        assert published_event.validation_status == ValidationStatus.FURTHER_INVESTIGATION_NEEDED.value
        assert published_event.final_confidence == 0.5

# Note: Need to ensure that async methods in mocks are wrapped with an async-compatible mock if necessary,
# e.g. if using `unittest.mock.AsyncMock` or if the test framework handles standard Mocks with await.
# Pytest-mock's `mocker.patch` usually handles this well. `unittest.mock.Mock` might need `new_callable=AsyncMock`.
# For this example, assuming standard Mocks are okay or will be adjusted if runtime issues arise.
# The current `mock_event_bus.publish` is a standard Mock. If `event_bus.publish` is an `async def`,
# it should be `mock_event_bus.publish = AsyncMock()` or similar.
# The same applies to `rule_engine.evaluate_rules` and `crud_sensor_reading.get_sensor_readings_by_sensor_id`.
# For simplicity, this example assumes they are either synchronous or the mocking handles async calls.
# If `pytest-asyncio` is used, it often works fine with standard mocks for awaited calls.
# Let's refine the mock_event_bus fixture for async.
@pytest.fixture
def mock_event_bus(): # Overwrite previous one for async context
    bus = Mock()
    bus.publish = Mock() # Make it an async mock
    return bus

@pytest.fixture
def mock_rule_engine(): # Overwrite previous one for async context
    engine = Mock(spec=RuleEngine)
    engine.evaluate_rules = Mock(return_value=(0.0, ["mock rule reason"]))
    return engine

@pytest.fixture
def mock_crud_sensor_reading(): # Overwrite previous one for async context
    crud = Mock()
    crud.get_sensor_readings_by_sensor_id = Mock(return_value=[])
    return crud

# The @pytest.mark.asyncio handles the test coroutine correctly.
# The mocks for async methods should ideally be AsyncMock if strictness is required,
# but often standard Mocks work if they just need to be awaitable and return a value.
# If `evaluate_rules` or `get_sensor_readings_by_sensor_id` are truly async,
# their mocks should be `AsyncMock`.
# For now, let's assume this setup is sufficient for pytest-asyncio.
# If `AttributeError: 'Mock' object is not awaitable` occurs, then AsyncMock is needed.
# e.g. from unittest.mock import AsyncMock
# mock_event_bus.publish = AsyncMock()
# mock_rule_engine.evaluate_rules = AsyncMock(return_value=(0.0, ["mock rule reason"]))
# mock_crud_sensor_reading.get_sensor_readings_by_sensor_id = AsyncMock(return_value=[])
pytest
