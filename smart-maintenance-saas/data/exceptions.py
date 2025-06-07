from typing import Optional, List, Any

class SmartMaintenanceBaseException(Exception):
    """Base class for custom exceptions in Smart Maintenance SaaS."""
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception

class DataValidationException(SmartMaintenanceBaseException):
    """Custom exception for data validation errors."""
    def __init__(self, message: str, errors: Optional[List[Any]] = None, original_exception: Optional[Exception] = None):
        super().__init__(message, original_exception)
        self.errors = errors if errors is not None else []

class DataEnrichmentException(SmartMaintenanceBaseException):
    """Custom exception for data enrichment errors."""
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message, original_exception)
        # Renaming underlying_exception to original_exception for consistency
        # self.underlying_exception = original_exception # This line is redundant

class AgentProcessingError(SmartMaintenanceBaseException):
    """For errors within an agent's main processing logic."""
    pass

class ServiceUnavailableError(SmartMaintenanceBaseException):
    """For when an external service (DB, Kafka, etc.) is unavailable."""
    pass

class ConfigurationError(SmartMaintenanceBaseException):
    """For issues with application configuration."""
    pass

class MLModelError(SmartMaintenanceBaseException):
    """For errors related to ML model loading or prediction."""
    pass

class WorkflowError(SmartMaintenanceBaseException):
    """For errors in business logic or workflow orchestration."""
    pass

class EventPublishError(SmartMaintenanceBaseException):
    """For errors encountered during event publishing by the event bus."""
    pass

class EventHandlerError(SmartMaintenanceBaseException):
    """For errors occurring within an event handler/subscriber."""
    pass
