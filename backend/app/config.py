"""
Configuration settings for the Dashboard API
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App settings
    app_name: str = "Raspberry Pi Dashboard"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/metrics.db"
    
    # Metrics collection
    collection_interval: int = 2  # seconds
    history_retention_hours: int = 24
    
    # WebSocket
    ws_heartbeat_interval: int = 30
    
    # Alerts thresholds
    cpu_alert_threshold: float = 80.0
    ram_alert_threshold: float = 80.0
    disk_alert_threshold: float = 90.0
    temp_alert_threshold: float = 70.0
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
