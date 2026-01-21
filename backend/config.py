"""
Backend-specific configuration settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class BackendSettings(BaseSettings):
    """Backend API configuration."""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 2
    api_timeout: int = 60
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Memory Limits
    max_memory_mb: int = 800
    gc_threshold: tuple[int, int, int] = (700, 10, 10)
    
    # Model Configuration
    default_model: str = "openai/gpt-4o-mini"
    complex_model: str = "anthropic/claude-3.5-sonnet"
    llm_timeout: int = 30  # Renamed from model_timeout to avoid namespace conflict
    max_tokens: int = 2000
    max_context_length: int = 6000
    
    # Streaming
    stream_chunk_size: int = 50
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    rate_limit_per_hour: int = 1000
    
    # Session
    session_ttl_seconds: int = 3600  # 1 hour
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields from .env
        protected_namespaces = ('settings_',)  # Avoid model_ namespace conflict


# Singleton instance
settings = BackendSettings()
