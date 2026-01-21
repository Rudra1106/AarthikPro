"""
Configuration management for AarthikAI Financial Intelligence System.
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # OpenRouter API
    openrouter_api_key: str
    
    # Pinecone Vector DB
    pinecone_api_key: str
    pinecone_index_name: str = "financial-reports"
    pinecone_environment: str = "us-east-1"
    
    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "aarthik_ai"  # For financial data (financial_statements, corporate_actions, etc.)
    mongodb_conversations_database: str = "aarthik_aii"  # For conversation history
    
    # Redis Cache
    redis_url: str = "redis://localhost:6379/0"
    
    # Perplexity API
    perplexity_api_key: Optional[str] = None
    
    # Zerodha API
    zerodha_api_key: Optional[str] = None
    zerodha_api_secret: Optional[str] = None
    zerodha_access_token: Optional[str] = None
    zerodha_refresh_token: Optional[str] = None
    
    # Zerodha OAuth (for portfolio integration)
    zerodha_encryption_key: Optional[str] = None
    zerodha_redirect_url: str = "http://localhost:8000/api/zerodha/callback"
    
    # Indian API
    indian_api_key: Optional[str] = None
    indian_api_base_url: str = "https://stock.indianapi.in"
    
    # Dhan API (for market data - replaces Zerodha for non-portfolio queries)
    dhan_client_id: Optional[str] = None
    dhan_access_token: Optional[str] = None
    
    # LangSmith (Optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: Optional[str] = None
    langchain_project: str = "aarthik-ai"
    
    # Application Settings
    environment: str = "development"
    log_level: str = "INFO"
    cache_ttl_seconds: int = 86400  # 24 hours
    max_context_tokens: int = 8000
    
    # Model Configuration
    default_model: str = "openai/gpt-4o-mini"
    complex_model: str = "anthropic/claude-3.5-sonnet"
    simple_model: str = "openai/gpt-3.5-turbo"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Cost & Latency Optimization
    enable_semantic_cache: bool = True
    enable_response_streaming: bool = True
    max_parallel_fetches: int = 3
    
    # Query Classification
    intent_classification_threshold: float = 0.7
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance
settings = get_settings()
