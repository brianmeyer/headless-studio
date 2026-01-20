"""Tests for configuration loading."""

import os

import pytest

from app.config import Settings


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables for testing."""
    env_vars = {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_ANON_KEY": "test-anon-key",
        "SUPABASE_SERVICE_KEY": "test-service-key",
        "GROQ_API_KEY": "test-groq-key",
        "GOOGLE_AI_API_KEY": "test-google-key",
        "REDDIT_CLIENT_ID": "test-reddit-id",
        "REDDIT_CLIENT_SECRET": "test-reddit-secret",
        "REDDIT_USER_AGENT": "TestAgent/1.0",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


def test_settings_loads_required_vars(mock_env):
    """Test that settings loads all required environment variables."""
    settings = Settings()

    assert settings.supabase_url == "https://test.supabase.co"
    assert settings.supabase_anon_key == "test-anon-key"
    assert settings.supabase_service_key == "test-service-key"
    assert settings.groq_api_key == "test-groq-key"
    assert settings.google_ai_api_key == "test-google-key"
    assert settings.reddit_client_id == "test-reddit-id"
    assert settings.reddit_client_secret == "test-reddit-secret"


def test_optional_vars_default_to_none(mock_env):
    """Test that optional variables default to None."""
    settings = Settings()

    assert settings.xai_api_key is None
    assert settings.dataforseo_login is None
    assert settings.dataforseo_password is None
    assert settings.reddit_ads_client_id is None
    assert settings.gumroad_access_token is None
    assert settings.mailerlite_api_key is None


def test_has_dataforseo_property(mock_env, monkeypatch):
    """Test has_dataforseo property returns correct values."""
    settings = Settings()
    assert settings.has_dataforseo is False

    monkeypatch.setenv("DATAFORSEO_LOGIN", "test-login")
    monkeypatch.setenv("DATAFORSEO_PASSWORD", "test-password")
    settings = Settings()
    assert settings.has_dataforseo is True


def test_has_xai_property(mock_env, monkeypatch):
    """Test has_xai property returns correct values."""
    settings = Settings()
    assert settings.has_xai is False

    monkeypatch.setenv("XAI_API_KEY", "test-xai-key")
    settings = Settings()
    assert settings.has_xai is True


def test_has_reddit_ads_property(mock_env, monkeypatch):
    """Test has_reddit_ads property returns correct values."""
    settings = Settings()
    assert settings.has_reddit_ads is False

    monkeypatch.setenv("REDDIT_ADS_CLIENT_ID", "test-ads-id")
    monkeypatch.setenv("REDDIT_ADS_CLIENT_SECRET", "test-ads-secret")
    settings = Settings()
    assert settings.has_reddit_ads is True
