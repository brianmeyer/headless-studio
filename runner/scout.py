"""Read-only scout. Development uses fixtures. No live xAI, Gumroad, or Supabase."""

from __future__ import annotations

import os

from runner.fixtures import DEFAULT_TOPIC, fixture_signals
from runner.models import Signal


def environment_name() -> str:
    return os.environ.get("ENVIRONMENT", "development").strip().lower() or "development"


def live_keys_present() -> bool:
    """True only if a live scout key is set. Runner still will not call those APIs."""
    return bool(
        os.environ.get("XAI_API_KEY")
        or os.environ.get("REDDIT_CLIENT_ID")
        or os.environ.get("GROQ_API_KEY")
    )


def scout(topic: str = DEFAULT_TOPIC) -> list[Signal]:
    """
    One-shot read-only scout.

    In development (default), or whenever live APIs are missing, return fixtures.
    This slice never performs HTTP. Fixture rows are marked fixture=True so the
    silence gates treat them as a miss.
    """
    _ = live_keys_present()
    return fixture_signals(topic)
