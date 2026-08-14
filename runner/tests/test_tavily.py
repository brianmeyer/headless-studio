"""Tavily is the optional Reddit transport. No key required, no key printed."""

from __future__ import annotations

import json
from pathlib import Path

from runner import run
from runner.live import live_signals
from runner.scout import scout
from runner.tavily import (
    NO_KEY_NOTE,
    fetch_tavily_reddit,
    key_from_hermes_env,
    parse_tavily_results,
    resolve_key,
    search_payload,
)

PAIN_RESULTS = {
    "results": [
        {
            "title": f"Looking for a bookkeeping spreadsheet for my Etsy shop {i}",
            "url": f"https://www.reddit.com/r/EtsySellers/comments/aa{i}/books/",
            "content": (
                "I can't tell what I actually made last month. Etsy fees and refunds are "
                "wasting hours every month and QuickBooks is too expensive for my shop. "
                "I would pay for a simple monthly profit and loss sheet."
            ),
        }
        for i in range(6)
    ]
}

NEUTRAL_RESULTS = {
    "results": [
        {
            "title": "Monthly shop update thread",
            "url": "https://www.reddit.com/r/EtsySellers/comments/neutral/update/",
            "content": "January numbers are posted. Shipping upgrades roll out on Tuesday.",
        }
    ]
}

GUMROAD_PAGE_PAIN = (
    "<html><head>"
    '<meta name="description" content="Sellers tell me they are tired of rewriting '
    'their books every month and can\'t see profit per order.">'
    "</head><body><h1>Shop Books Workbook</h1>"
    "<p>Built because spreadsheets from scratch are wasting hours.</p>"
    "</body></html>"
)


def _tavily_body(payload: dict) -> str:
    return json.dumps(payload)


def _gumroad_discover_html(n: int = 6) -> str:
    products = [
        {
            "name": f"Shop Books Workbook {i}",
            "permalink": f"books{i}",
            "url": f"https://example.gumroad.com/l/books{i}",
            "price_cents": 1900 + i,
            "seller": {"name": f"Seller {i}"},
            "review_count": 12 + i,
        }
        for i in range(n)
    ]
    page = json.dumps({"search_results": {"total": n, "products": products}})
    escaped = page.replace('"', "&quot;")
    return f"<html><body>{escaped}</body></html>"


def test_parse_tavily_results_are_sourced_reddit_rows_with_pain():
    signals = parse_tavily_results(_tavily_body(PAIN_RESULTS))
    assert len(signals) == 6
    assert all(not s.fixture for s in signals)
    assert all(s.source == "reddit" for s in signals)
    assert all(s.url.startswith("https://www.reddit.com/") for s in signals)
    assert all(s.pain_points for s in signals)
    assert all("would pay" in s.buying_signals for s in signals)


def test_parse_tavily_neutral_snippet_invents_no_pain():
    signals = parse_tavily_results(_tavily_body(NEUTRAL_RESULTS))
    assert len(signals) == 1
    assert signals[0].pain_points == ()
    assert signals[0].buying_signals == ()


def test_parse_tavily_result_without_real_url_is_dropped():
    payload = {
        "results": [
            {"title": "No URL at all", "content": "I can't find a simple books sheet."},
            {"title": "Relative", "url": "/r/EtsySellers/comments/x/", "content": "need help"},
            {"title": "Keep", "url": "https://www.reddit.com/r/EtsySellers/comments/y/",
             "content": "I can't keep up with fees, looking for a spreadsheet."},
        ]
    }
    signals = parse_tavily_results(_tavily_body(payload))
    assert [s.url for s in signals] == ["https://www.reddit.com/r/EtsySellers/comments/y/"]


def test_parse_tavily_garbage_body_is_empty():
    assert parse_tavily_results("not json") == []
    assert parse_tavily_results(json.dumps({"results": "nope"})) == []


def test_search_payload_targets_reddit_only():
    payload = search_payload("etsy shop bookkeeping")
    assert payload["include_domains"] == ["reddit.com"]
    assert "site:reddit.com" in payload["query"]
    assert "etsy shop bookkeeping" in payload["query"]
    for phrase in ("looking for", "need help", "how do I", "would pay"):
        assert phrase in payload["query"]
    assert payload["search_depth"] == "basic"
    assert payload["topic"] == "general"
    assert 8 <= payload["max_results"] <= 10
    assert "include_answer" not in payload
    assert "include_raw_content" not in payload


def test_request_sends_bearer_key_and_reddit_body(monkeypatch):
    seen: dict[str, object] = {}

    class FakeResponse:
        status = 200

        def read(self):
            return _tavily_body(PAIN_RESULTS).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(request, timeout=None):
        seen["url"] = request.full_url
        seen["method"] = request.get_method()
        seen["auth"] = request.get_header("Authorization")
        seen["body"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setenv("TAVILY_API_KEY", "test-key-not-real")
    monkeypatch.setattr("runner.tavily.urlopen", fake_urlopen)

    signals, notes = fetch_tavily_reddit("etsy shop bookkeeping")
    assert len(signals) == 6
    assert seen["url"] == "https://api.tavily.com/search"
    assert seen["method"] == "POST"
    assert seen["auth"] == "Bearer test-key-not-real"
    assert seen["body"]["include_domains"] == ["reddit.com"]
    assert "site:reddit.com" in seen["body"]["query"]
    assert any("via Tavily" in note for note in notes)
    # The key never lands in a note, and therefore never on a receipt.
    assert all("test-key-not-real" not in note for note in notes)


def test_no_key_anywhere_notes_fallback_without_calling_tavily(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("Tavily must not be called without a key")

    monkeypatch.setattr("runner.tavily.http_post_json", boom)
    key, note = resolve_key()
    assert key == ""
    assert note == NO_KEY_NOTE

    signals, notes = fetch_tavily_reddit("etsy shop bookkeeping")
    assert signals == []
    assert NO_KEY_NOTE in notes


def test_no_key_and_blocked_http_still_falls_back_to_fixtures_and_misses(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr("runner.live.http_get", lambda url, timeout=12.0: (403, "Blocked"))
    receipt = tmp_path / "RECEIPT.md"
    result = run(topic="etsy shop bookkeeping", out_path=receipt)
    assert result.verdict == "miss"
    assert all(s.fixture for s in result.signals)
    assert any("fallback" in note for note in result.notes)
    assert not (tmp_path / "mocks").exists()
    text = receipt.read_text(encoding="utf-8")
    assert "NOT APPROVED" in text
    assert "fixtures" in text.lower()


def test_hermes_env_loader_reads_only_the_tavily_key(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# hermes",
                "OTHER_SECRET=must-not-be-read",
                'TAVILY_API_KEY="hermes-value"',
                "GROQ_API_KEY=also-must-not-be-read",
            ]
        ),
        encoding="utf-8",
    )
    assert key_from_hermes_env(env_file) == "hermes-value"


def test_hermes_key_resolves_and_is_never_printed(tmp_path: Path, monkeypatch, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("TAVILY_API_KEY=hermes-value\n", encoding="utf-8")
    monkeypatch.setattr("runner.tavily.HERMES_ENV_PATH", env_file)
    monkeypatch.setattr(
        "runner.tavily.http_post_json",
        lambda url, key, payload, timeout=12.0: (200, _tavily_body(PAIN_RESULTS)),
    )
    signals, notes = fetch_tavily_reddit("etsy shop bookkeeping")
    assert len(signals) == 6
    assert any("Hermes" in note for note in notes)
    assert all("hermes-value" not in note for note in notes)
    assert "hermes-value" not in capsys.readouterr().out


def test_missing_hermes_file_is_not_an_error(tmp_path: Path):
    assert key_from_hermes_env(tmp_path / "nope" / ".env") == ""


def test_tavily_401_is_noted_and_scout_continues(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key-not-real")
    monkeypatch.setattr(
        "runner.tavily.http_post_json",
        lambda url, key, payload, timeout=12.0: (401, ""),
    )
    monkeypatch.setattr("runner.live.http_get", lambda url, timeout=12.0: (403, "Blocked"))
    signals, notes = live_signals("etsy shop bookkeeping")
    assert signals == []
    assert any("→ 401" in note for note in notes)
    assert any("continuing without Tavily rows" in note for note in notes)
    assert all("test-key-not-real" not in note for note in notes)


def test_tavily_empty_results_are_noted(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key-not-real")
    monkeypatch.setattr(
        "runner.tavily.http_post_json",
        lambda url, key, payload, timeout=12.0: (200, json.dumps({"results": []})),
    )
    signals, notes = fetch_tavily_reddit("etsy shop bookkeeping")
    assert signals == []
    assert any("0 results with a real URL" in note for note in notes)


def test_tavily_transport_failure_does_not_crash(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key-not-real")
    monkeypatch.setattr(
        "runner.tavily.http_post_json",
        lambda url, key, payload, timeout=12.0: (0, "URLError"),
    )
    signals, notes = fetch_tavily_reddit("etsy shop bookkeeping")
    assert signals == []
    assert any("→ 0" in note for note in notes)


def test_fixtures_flag_skips_tavily_and_http(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("--fixtures must not touch the network")

    monkeypatch.setenv("TAVILY_API_KEY", "test-key-not-real")
    monkeypatch.setattr("runner.tavily.http_post_json", boom)
    monkeypatch.setattr("runner.live.http_get", boom)
    outcome = scout("etsy shop bookkeeping", use_fixtures=True)
    assert outcome.used_fixtures is True
    assert all(s.fixture for s in outcome.signals)


def test_mocked_tavily_plus_gumroad_pages_can_hit(tmp_path: Path, monkeypatch):
    """Tavily reddit rows plus real page text on Gumroad rows can clear the gates."""
    discover = _gumroad_discover_html(6)

    monkeypatch.setenv("TAVILY_API_KEY", "test-key-not-real")
    monkeypatch.setattr(
        "runner.tavily.http_post_json",
        lambda url, key, payload, timeout=12.0: (200, _tavily_body(PAIN_RESULTS)),
    )

    def fake_get(url, timeout=12.0):
        if "reddit.com" in url:
            return 403, "Blocked"
        if "gumroad.com/discover" in url:
            return 200, discover
        if "gumroad.com/l/" in url:
            return 200, GUMROAD_PAGE_PAIN
        return 0, "skip"

    monkeypatch.setattr("runner.live.http_get", fake_get)
    receipt = tmp_path / "RECEIPT.md"
    result = run(topic="etsy shop bookkeeping", out_path=receipt)

    assert result.signals
    assert all(not s.fixture for s in result.signals)
    assert {s.source for s in result.signals} == {"reddit", "gumroad"}
    assert result.verdict == "hit"
    assert not (tmp_path / "mocks").exists()
    text = receipt.read_text(encoding="utf-8")
    assert "NOT APPROVED" in text
    assert any("via Tavily" in note for note in result.notes)
    assert any("not retried" in note for note in result.notes)
    assert "test-key-not-real" not in text
