"""Read-only scout. Fixtures if no keys and no local dump. No live HTTP."""

from __future__ import annotations

import json
import os
from pathlib import Path

from runner.fixtures import DEFAULT_TOPIC, fixture_signals
from runner.models import Signal


def environment_name() -> str:
    return os.environ.get("ENVIRONMENT", "development").strip().lower() or "development"


def live_keys_present() -> bool:
    """True if a scout key is set. This slice still does not call those APIs."""
    return bool(
        os.environ.get("XAI_API_KEY")
        or os.environ.get("REDDIT_CLIENT_ID")
        or os.environ.get("GROQ_API_KEY")
    )


def load_local_signals(path: str | Path) -> list[Signal]:
    """Load a local JSON list of signals. Read-only. No network."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("signals file must be a JSON list")
    signals: list[Signal] = []
    for index, row in enumerate(raw):
        if not isinstance(row, dict):
            raise ValueError(f"signals[{index}] must be an object")
        signals.append(
            Signal(
                id=str(row.get("id") or f"local-{index + 1}"),
                source=str(row.get("source") or "local"),
                text=str(row.get("text") or ""),
                url=str(row.get("url") or ""),
                created_at=str(row.get("created_at") or ""),
                fixture=bool(row.get("fixture", False)),
                pain_points=tuple(row.get("pain_points") or ()),
                buying_signals=tuple(row.get("buying_signals") or ()),
                questions=tuple(row.get("questions") or ()),
                engagement=int(row.get("engagement") or 0),
                relevance=float(row.get("relevance") or 0.0),
                author=str(row.get("author") or ""),
            )
        )
    return signals


def scout(
    topic: str = DEFAULT_TOPIC,
    signals_path: str | Path | None = None,
) -> tuple[list[Signal], str]:
    """
    One-shot read-only scout.

    - local JSON dump → those rows, scout_mode=local_file
    - otherwise fixtures (no keys / no HTTP), scout_mode=fixtures

    Fixture rows cannot pass the sourced-signal gate.
    """
    _ = live_keys_present()
    if signals_path:
        return load_local_signals(signals_path), "local_file"
    return fixture_signals(topic), "fixtures"
