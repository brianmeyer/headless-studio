"""Public HTTP scout: live rows are sourced; fixtures never are."""

from __future__ import annotations

import json
from pathlib import Path

from runner import run
from runner.live import parse_gumroad_discover, parse_reddit_listing
from runner.scout import scout


def _reddit_body(n: int = 6) -> str:
    children = []
    for i in range(n):
        children.append(
            {
                "kind": "t3",
                "data": {
                    "id": f"abc{i}",
                    "title": (
                        f"Looking for ChatGPT prompts for property managers {i}. "
                        "Tired of rewriting listing copy from scratch."
                    ),
                    "selftext": "Manual copy-paste is wasting hours and notices don't work.",
                    "permalink": f"/r/PropertyManagement/comments/abc{i}/prompts/",
                    "author": f"pm{i}",
                    "score": 40 + i,
                },
            }
        )
    return json.dumps({"data": {"children": children}})


def _gumroad_html(n: int = 6) -> str:
    products = []
    for i in range(n):
        products.append(
            {
                "name": f"Prompt Pack {i} for Agents",
                "permalink": f"pack{i}",
                "url": f"https://example.gumroad.com/l/pack{i}",
                "price_cents": 1500 + i,
                "seller": {"name": f"Seller {i}"},
            }
        )
    page = json.dumps({"search_results": {"total": n, "products": products}})
    escaped = page.replace('"', "&quot;")
    return f"<html><head></head><body>{escaped}</body></html>"


def test_parse_reddit_listing_marks_sourced():
    signals = parse_reddit_listing(_reddit_body(5))
    assert len(signals) == 5
    assert all(not s.fixture for s in signals)
    assert all(s.source == "reddit" for s in signals)
    assert all(s.url.startswith("https://www.reddit.com/") for s in signals)
    assert any(s.pain_points for s in signals)


def test_parse_gumroad_discover_marks_sourced_without_invented_pain():
    signals = parse_gumroad_discover(_gumroad_html(5))
    assert len(signals) == 5
    assert all(not s.fixture for s in signals)
    assert all(s.source == "gumroad" for s in signals)
    assert all(s.url.startswith("https://") for s in signals)
    assert all(s.pain_points == () for s in signals)


def test_fixtures_flag_skips_http(monkeypatch):
    def boom(url, timeout=12.0):
        raise AssertionError(f"http_get should not run: {url}")

    monkeypatch.setattr("runner.live.http_get", boom)
    outcome = scout("chatgpt prompts for property managers", use_fixtures=True)
    assert outcome.used_fixtures is True
    assert outcome.signals
    assert all(s.fixture for s in outcome.signals)


def test_http_failure_uses_fixtures(monkeypatch):
    monkeypatch.setattr("runner.live.http_get", lambda url, timeout=12.0: (403, "Blocked"))
    outcome = scout("chatgpt prompts for property managers")
    assert outcome.used_fixtures is True
    assert all(s.fixture for s in outcome.signals)
    assert any("403" in note or "fixtures" in note.lower() for note in outcome.notes)


def test_mocked_reddit_live_can_hit(tmp_path: Path, monkeypatch):
    body = _reddit_body(6)
    html = _gumroad_html(6)

    def fake_get(url, timeout=12.0):
        if "reddit.com" in url:
            return 200, body
        if "gumroad.com" in url:
            return 200, html
        return 0, "skip"

    monkeypatch.setattr("runner.live.http_get", fake_get)
    receipt = tmp_path / "RECEIPT.md"
    result = run(topic="chatgpt prompts for property managers", out_path=receipt)
    assert all(not s.fixture for s in result.signals)
    assert {s.source for s in result.signals} == {"reddit", "gumroad"}
    assert result.verdict == "hit"
    assert not (tmp_path / "mocks").exists()


def test_mocked_gumroad_live_is_sourced_but_misses_without_pain(tmp_path: Path, monkeypatch):
    html = _gumroad_html(6)

    def fake_get(url, timeout=12.0):
        if "gumroad.com" in url:
            return 200, html
        return 403, "Blocked"

    monkeypatch.setattr("runner.live.http_get", fake_get)
    receipt = tmp_path / "RECEIPT.md"
    result = run(topic="chatgpt prompts for property managers", out_path=receipt)
    assert result.signals
    assert all(not s.fixture for s in result.signals)
    assert all(s.source == "gumroad" for s in result.signals)
    assert result.verdict == "miss"
    assert not (tmp_path / "mocks").exists()
    text = receipt.read_text(encoding="utf-8")
    assert "miss" in text
    assert "gumroad" in text.lower()
