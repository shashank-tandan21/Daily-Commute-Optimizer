"""Configuration management for the Daily Commute Optimizer."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # API Configuration
    google_maps_api_key: Optional[str] = None
    weather_api_key: Optional[str] = None
    transit_api_key: Optional[str] = None
    
    # Application Configuration
    max_routes_per_request: int = 3
    cache_ttl_minutes: int = 5
    default_max_walking_distance: float = 2.0
    
    # Testing Configuration
    use_mock_apis: bool = True
    property_test_iterations: int = 100
    
    # Logging Configuration
    log_level: str = "INFO"


# Global settings instance
settings = Settings()