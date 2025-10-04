# workflow_agents/config.py (UPDATED for Render)
"""
Configuration for workflow agents system - Render optimized.
"""

import os
from pydantic import BaseModel, Field
from typing import Optional


class WorkflowAgentConfig(BaseModel):
    """Configuration for workflow agents."""
    
    # Model configuration
    model_name: str = Field(
        default_factory=lambda: os.getenv("WORKFLOW_AGENT_MODEL_NAME", "anthropic:claude-sonnet-4-20250514"),
        description="LLM model to use for agents"
    )
    temperature: float = Field(
        default_factory=lambda: float(os.getenv("WORKFLOW_AGENT_TEMPERATURE", "0.3")),
        ge=0.0,
        le=2.0,
        description="Temperature for LLM responses"
    )
    max_tokens: int = Field(
        default_factory=lambda: int(os.getenv("WORKFLOW_AGENT_MAX_TOKENS", "4000")),
        description="Maximum tokens per response"
    )
    
    # Database configuration
    supabase_url: str = Field(
        default_factory=lambda: os.getenv("SUPABASE_URL", ""),
        description="Supabase project URL"
    )
    supabase_key: str = Field(
        default_factory=lambda: os.getenv("SUPABASE_KEY", ""),
        description="Supabase service role key"
    )
    
    # Redis configuration (Render provides this automatically)
    redis_url: str = Field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379"),
        description="Redis connection URL (provided by Render)"
    )
    
    # OAuth configuration
    oauth_redirect_base: str = Field(
        default_factory=lambda: os.getenv("OAUTH_REDIRECT_BASE", "http://localhost:3000"),
        description="Base URL for OAuth redirects"
    )
    
    # Feature flags
    enable_rate_limiting: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true",
        description="Enable rate limiting middleware"
    )
    enable_dry_run: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_DRY_RUN", "true").lower() == "true",
        description="Enable dry run validation"
    )
    enable_data_mapper: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_DATA_MAPPER", "true").lower() == "true",
        description="Enable Data Mapper agent"
    )
    
    # Logging
    log_level: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"),
        description="Logging level"
    )
    log_to_langsmith: bool = Field(
        default_factory=lambda: os.getenv("LANGSMITH_API_KEY", "") != "",
        description="Send traces to LangSmith"
    )
    
    # Environment
    environment: str = Field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development"),
        description="Environment (development, staging, production)"
    )
    
    class Config:
        env_prefix = "WORKFLOW_AGENT_"
        case_sensitive = False


# Global config instance
config = WorkflowAgentConfig()


# Validate critical config on import
def validate_config():
    """Validate that critical configuration is present."""
    errors = []
    
    if not config.supabase_url:
        errors.append("SUPABASE_URL is required")
    
    if not config.supabase_key:
        errors.append("SUPABASE_KEY is required")
    
    if not config.redis_url:
        errors.append("REDIS_URL is required")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")


# Run validation in production
if config.environment == "production":
    validate_config()