"""Read-only scout: public HTTP, then fixtures. Fixtures never count as sourced."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from runner.fixtures import DEFAULT_TOPIC, fixture_signals
from runner.live import live_signals
from runner.models import Signal


@dataclass
class ScoutOutcome:
    signals: list[Signal]
    notes: list[str] = field(default_factory=list)
    used_fixtures: bool = False


def environment_name() -> str:
    return os.environ.get("ENVIRONMENT", "development").strip().lower() or "development"


def live_keys_present() -> bool:
    """True if a live-auth key is set. Public HTTP does not require these."""
    return bool(
        os.environ.get("XAI_API_KEY")
        or os.environ.get("REDDIT_CLIENT_ID")
        or os.environ.get("GROQ_API_KEY")
    )


def _force_fixtures(use_fixtures: bool) -> bool:
    """--fixtures, GREEN_FORCE_FIXTURES=1, or explicit force_fixtures all skip HTTP."""
    if use_fixtures:
        return True
    return os.environ.get("GREEN_FORCE_FIXTURES", "").strip() == "1"


def scout(topic: str = DEFAULT_TOPIC, use_fixtures: bool = False) -> ScoutOutcome:
    """
    One-shot read-only scout.

    Keys missing: try public/unauth HTTP, then fixtures, still miss.
    Fixture rows are marked fixture=True and never count as sourced.
    Live rows (if any) are returned alone — fixtures are not mixed in.

    Force fixtures via --fixtures, GREEN_FORCE_FIXTURES=1, or force_fixtures.
    """
    _ = live_keys_present()
    if _force_fixtures(use_fixtures):
        return ScoutOutcome(
            signals=fixture_signals(topic),
            notes=[
                "scout: --fixtures / GREEN_FORCE_FIXTURES=1 (skipped public HTTP)",
                "fixtures never count as sourced",
            ],
            used_fixtures=True,
        )

    live, notes = live_signals(topic)
    if live:
        notes.append("scout: live public HTTP (fixtures not mixed in)")
        notes.append("fixtures never count as sourced")
        return ScoutOutcome(signals=live, notes=notes, used_fixtures=False)

    notes.append("scout: public HTTP empty/failed → fixtures")
    notes.append("fixtures never count as sourced")
    return ScoutOutcome(
        signals=fixture_signals(topic),
        notes=notes,
        used_fixtures=True,
    )
