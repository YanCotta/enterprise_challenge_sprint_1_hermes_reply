class DataValidationException(ValueError):
    """Custom exception for data validation errors."""

    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors if errors is not None else []


class DataEnrichmentException(Exception):
    """Custom exception for data enrichment errors."""

    def __init__(self, message, underlying_exception=None):
        super().__init__(message)
        self.underlying_exception = underlying_exception
