"""
Headless Studio - Configuration Settings
Loads and validates environment variables using Pydantic Settings
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # =========================================================================
    # Supabase (Required - Phase 0)
    # =========================================================================
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_anon_key: str = Field(..., description="Supabase anonymous key")
    supabase_service_key: str = Field(..., description="Supabase service role key")

    # =========================================================================
    # LLM APIs (Required - Phase 0)
    # =========================================================================
    groq_api_key: str = Field(..., description="Groq API key for LLM calls")
    google_ai_api_key: str = Field(..., description="Google AI Studio API key")

    # =========================================================================
    # Reddit (Required - Phase 0)
    # =========================================================================
    reddit_client_id: str = Field(..., description="Reddit app client ID")
    reddit_client_secret: str = Field(..., description="Reddit app client secret")
    reddit_user_agent: str = Field(
        default="headless-studio-discovery/1.0",
        description="Reddit API user agent",
    )

    # =========================================================================
    # Gumroad (Required - Phase 1)
    # =========================================================================
    gumroad_access_token: str | None = Field(
        default=None, description="Gumroad API access token"
    )

    # =========================================================================
    # Pinterest (Optional - Phase 0+)
    # =========================================================================
    pinterest_app_id: str | None = Field(default=None, description="Pinterest app ID")
    pinterest_app_secret: str | None = Field(
        default=None, description="Pinterest app secret"
    )
    pinterest_access_token: str | None = Field(
        default=None, description="Pinterest access token"
    )

    # =========================================================================
    # X/Twitter via XAI Grok (Optional - Phase 1+)
    # =========================================================================
    xai_api_key: str | None = Field(default=None, description="XAI/Grok API key")

    # =========================================================================
    # Reddit Ads (Phase 1+)
    # =========================================================================
    reddit_ads_client_id: str | None = Field(
        default=None, description="Reddit Ads client ID"
    )
    reddit_ads_client_secret: str | None = Field(
        default=None, description="Reddit Ads client secret"
    )
    reddit_ads_refresh_token: str | None = Field(
        default=None, description="Reddit Ads refresh token"
    )

    # =========================================================================
    # Google Ads (Phase 2)
    # =========================================================================
    google_ads_client_id: str | None = Field(
        default=None, description="Google Ads client ID"
    )
    google_ads_client_secret: str | None = Field(
        default=None, description="Google Ads client secret"
    )
    google_ads_refresh_token: str | None = Field(
        default=None, description="Google Ads refresh token"
    )
    google_ads_developer_token: str | None = Field(
        default=None, description="Google Ads developer token"
    )
    google_ads_customer_id: str | None = Field(
        default=None, description="Google Ads customer ID"
    )

    # =========================================================================
    # Meta Ads (Phase 2)
    # =========================================================================
    meta_app_id: str | None = Field(default=None, description="Meta app ID")
    meta_app_secret: str | None = Field(default=None, description="Meta app secret")
    meta_access_token: str | None = Field(
        default=None, description="Meta access token"
    )
    meta_ad_account_id: str | None = Field(
        default=None, description="Meta ad account ID"
    )

    # =========================================================================
    # MailerLite (Phase 1+)
    # =========================================================================
    mailerlite_api_key: str | None = Field(
        default=None, description="MailerLite API key"
    )

    # =========================================================================
    # SEO / Keywords (Optional)
    # =========================================================================
    dataforseo_login: str | None = Field(
        default=None, description="DataForSEO login"
    )
    dataforseo_password: str | None = Field(
        default=None, description="DataForSEO password"
    )

    # =========================================================================
    # N8N Webhooks
    # =========================================================================
    n8n_webhook_gate1: str | None = Field(
        default=None, description="N8N Gate 1 webhook URL"
    )
    n8n_webhook_manufacturing: str | None = Field(
        default=None, description="N8N Manufacturing webhook URL"
    )
    n8n_webhook_gate2: str | None = Field(
        default=None, description="N8N Gate 2 webhook URL"
    )

    # =========================================================================
    # Notifications (Optional)
    # =========================================================================
    slack_webhook_url: str | None = Field(
        default=None, description="Slack webhook for notifications"
    )
    discord_webhook_url: str | None = Field(
        default=None, description="Discord webhook for notifications"
    )

    # =========================================================================
    # Application Settings
    # =========================================================================
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Runtime environment"
    )
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="Comma-separated CORS origins",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )

    # =========================================================================
    # Phase Configuration
    # =========================================================================
    current_phase: int = Field(
        default=0, ge=0, le=3, description="Current implementation phase (0-3)"
    )

    # =========================================================================
    # Feature Flags
    # =========================================================================
    enable_organic_validation: bool = Field(
        default=True, description="Enable organic validation"
    )
    enable_paid_validation: bool = Field(
        default=False, description="Enable paid validation"
    )
    enable_pinterest_auto: bool = Field(
        default=False, description="Enable automatic Pinterest posting"
    )
    enable_seo_clustering: bool = Field(
        default=False, description="Enable SEO clustering (Phase 3)"
    )

    # =========================================================================
    # Rate Limiting & Safety
    # =========================================================================
    max_concurrent_llm_requests: int = Field(
        default=5, ge=1, le=20, description="Max concurrent LLM requests"
    )
    max_opportunities_per_run: int = Field(
        default=10, ge=1, le=50, description="Max opportunities per discovery run"
    )
    duplicate_lookback_days: int = Field(
        default=90, ge=30, le=365, description="Days to look back for duplicates"
    )

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        """Validate CORS origins format."""
        if not v:
            return "http://localhost:3000"
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
