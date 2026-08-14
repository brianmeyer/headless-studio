"""Make `import runner` work when pytest is invoked as a script, with no secrets."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def no_tavily_secrets(monkeypatch, tmp_path_factory):
    """
    No test may read a real key or reach Tavily.

    TAVILY_API_KEY is cleared and the Hermes `.env` path is pointed at a file that
    does not exist. Tests that want Tavily rows mock the transport themselves.
    """
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    missing = tmp_path_factory.mktemp("hermes") / "absent" / ".env"
    monkeypatch.setattr("runner.tavily.HERMES_ENV_PATH", missing)
