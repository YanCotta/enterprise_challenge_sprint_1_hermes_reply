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

    # Agents
    agent_communication_timeout: int = 30

    # ML
    model_registry_path: str = "./models"

    # Notification Services
    whatsapp_api_key: str = "your_whatsapp_api_key"
    email_smtp_host: str = "smtp.example.com"
    email_smtp_port: int = 587
    email_smtp_user: str = "your_smtp_username"
    email_smtp_password: str = "your_smtp_password"

    # Logging
    log_level: str = "INFO"

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
