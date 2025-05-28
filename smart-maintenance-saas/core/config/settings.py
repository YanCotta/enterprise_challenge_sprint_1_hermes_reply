"""
Configuration management for Smart Maintenance SaaS.

This module provides a central configuration system using Pydantic's BaseSettings
to manage environment-specific configuration values. Settings can be loaded from
environment variables or from a .env file.
"""

from typing import Any, Dict, Optional

from pydantic import Field, validator, AnyUrl
from pydantic_settings import BaseSettings


class PostgresDsn(AnyUrl):
    allowed_schemes = {"postgresql", "postgresql+psycopg2", "postgres"}
    host_required = True


class RedisDsn(AnyUrl):
    allowed_schemes = {"redis"}
    host_required = True


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
    
    # Database
    database_url: str = "postgresql://smart_user:strong_password@localhost:5432/smart_maintenance_db"
    
    # Redis (for future use)
    redis_url: str = "redis://localhost:6379"
    
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
    
    @validator("database_url")
    def validate_database_url(cls, v: str) -> str:
        """Validate that the database URL is properly formatted."""
        if not v.startswith(("postgresql://", "postgresql+psycopg2://", "postgres://")):
            raise ValueError("Database URL must start with postgresql:// or postgresql+psycopg2://")
        return v
        
    @validator("redis_url")
    def validate_redis_url(cls, v: str) -> str:
        """Validate that the Redis URL is properly formatted."""
        if not v.startswith("redis://"):
            raise ValueError("Redis URL must start with redis://")
        return v
    
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
