"""
Configuration management for Smart Maintenance SaaS.

This module provides a central configuration system using Pydantic's BaseSettings
to manage environment-specific configuration values. Settings can be loaded from
environment variables or from a .env file.
"""

from typing import Any, Dict, Optional

# Import Pydantic DSN types
from pydantic import AnyUrl, Field, PostgresDsn, RedisDsn, validator
from pydantic_settings import BaseSettings


class KafkaDsn(AnyUrl):
    allowed_schemes = {"kafka"}
    host_required = False


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.

    This class defines all configuration settings for the Smart Maintenance SaaS
    application. Default values are provided but can be overridden via environment
    variables or a .env file.
    """

    PROJECT_NAME: str = "Smart Maintenance SaaS"
    API_VERSION: str = "0.1.0"

    # Database
    database_url: PostgresDsn = "postgresql://smart_user:strong_password@localhost:5432/smart_maintenance_db"  # type: ignore
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "smart_user"
    db_password: str = "strong_password"
    db_name: str = "smart_maintenance_db"

    # Test Database
    test_database_url: PostgresDsn = "postgresql://smart_user:strong_password@localhost:5432/smart_maintenance_db_test"  # type: ignore

    # Redis (for future use)
    redis_url: RedisDsn = "redis://localhost:6379"  # type: ignore

    # Kafka (for future use)
    kafka_bootstrap_servers: str = "localhost:9092"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # Security
    secret_key: str = "change_this_to_a_secure_random_key_in_production"
    access_token_expire_minutes: int = 60
    API_KEY: str = "your_default_api_key"  # Static API Key for basic auth

    # Agents
    agent_communication_timeout: int = 30

    # Scheduling
    USE_OR_TOOLS_SCHEDULER: bool = Field(default=False, description="Enable advanced OR-Tools constraint programming scheduler")

    # ML
    model_registry_path: str = "./models"
    # Toggle to disable MLflow model registry/network calls (fast startup / offline mode)
    DISABLE_MLFLOW_MODEL_LOADING: bool = Field(default=False, description="Disable MLflow model registry calls to avoid blocking on network/DNS")

    # Notification Services
    whatsapp_api_key: str = "your_whatsapp_api_key"
    email_smtp_host: str = "smtp.example.com"
    email_smtp_port: int = 587
    email_smtp_user: str = "your_smtp_username"
    email_smtp_password: str = "your_smtp_password"

    # Logging
    log_level: str = "INFO"

    # Event Bus DLQ and Retries
    EVENT_HANDLER_MAX_RETRIES: int = Field(default=3, description="Maximum retry attempts for event handlers.")
    EVENT_HANDLER_RETRY_DELAY_SECONDS: float = Field(default=1.0, description="Delay in seconds between event handler retries.")
    DLQ_ENABLED: bool = Field(default=True, description="Enable Dead Letter Queue for failed event processing.")
    DLQ_LOG_FILE: str = Field(default="logs/dlq_events.log", description="Path to the DLQ log file.")

    # Orchestrator Settings
    ORCHESTRATOR_URGENT_MAINTENANCE_DAYS: int = Field(
        default=30,
        description="Threshold in days for considering maintenance urgent."
    )
    ORCHESTRATOR_HIGH_CONFIDENCE_THRESHOLD: float = Field(
        default=0.90,
        description="Prediction confidence level considered high."
    )
    ORCHESTRATOR_MODERATE_CONFIDENCE_THRESHOLD: float = Field(
        default=0.75,
        description="Prediction confidence level considered moderate."
    )
    ORCHESTRATOR_AUTO_APPROVAL_MAX_DAYS_MODERATE_CONFIDENCE: int = Field(
        default=15,
        description="Max days to failure for auto-approval if confidence is only moderate (but not low)."
    )
    ORCHESTRATOR_VERY_URGENT_MAINTENANCE_DAYS_FACTOR: float = Field(
        default=0.5,
        description="Factor of URGENT_MAINTENANCE_DAYS to determine 'very urgent' threshold (e.g., 0.5 for half)."
    )

    class Config:
        """Pydantic config for settings."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create a global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings.

    This function is useful for dependency injection in FastAPI.

    Returns:
        Settings: Application settings
    """
    return settings
