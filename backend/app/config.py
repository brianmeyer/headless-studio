"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Supabase (required)
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str

    # LLMs (required)
    groq_api_key: str
    google_ai_api_key: str

    # Reddit API (required)
    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str = "HeadlessStudio/0.1.0"

    # X/Twitter API (optional)
    xai_api_key: str | None = None

    # Reddit Ads (optional - Phase 1+)
    reddit_ads_client_id: str | None = None
    reddit_ads_client_secret: str | None = None

    # Gumroad (optional - Phase 1+)
    gumroad_access_token: str | None = None

    # MailerLite (optional - Phase 1+)
    mailerlite_api_key: str | None = None

    # DataForSEO (optional - has fallback)
    dataforseo_login: str | None = None
    dataforseo_password: str | None = None

    @property
    def has_dataforseo(self) -> bool:
        """Check if DataForSEO credentials are configured."""
        return bool(self.dataforseo_login and self.dataforseo_password)

    @property
    def has_xai(self) -> bool:
        """Check if X/Twitter API is configured."""
        return bool(self.xai_api_key)

    @property
    def has_reddit_ads(self) -> bool:
        """Check if Reddit Ads is configured."""
        return bool(self.reddit_ads_client_id and self.reddit_ads_client_secret)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
