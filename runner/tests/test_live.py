"""Public HTTP scout: live rows are sourced; fixtures never are."""

from __future__ import annotations

import json
from pathlib import Path

from runner import run
from runner.live import (
    fetch_gumroad,
    fetch_gumroad_pages,
    gumroad_page_text,
    parse_gumroad_discover,
    parse_reddit_listing,
)
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


PAGE_WITH_PAIN = (
    "<html><head>"
    '<meta name="description" content="For sellers who can\'t tell what they earned.">'
    "<script>var junk = {ignored: true};</script>"
    "</head><body><h1>Shop Books Workbook</h1>"
    "<p>I built this because tracking fees by hand is wasting hours every month "
    "and starting over in a new sheet each January is too much.</p>"
    "</body></html>"
)

PAGE_WITHOUT_PAIN = (
    "<html><head>"
    '<meta name="description" content="A tidy workbook for shop numbers.">'
    "</head><body><h1>Prompt Pack 0 for Agents</h1>"
    "<p>Instant download. Four tabs. Works in Google Sheets and Excel.</p>"
    "</body></html>"
)


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


def test_gumroad_page_text_reads_meta_and_body_without_scripts():
    text = gumroad_page_text(PAGE_WITH_PAIN)
    assert "can't tell what they earned" in text
    assert "wasting hours" in text
    assert "Shop Books Workbook" in text
    assert "var junk" not in text


def test_gumroad_product_page_with_pain_sets_pain_points(monkeypatch):
    monkeypatch.setattr("runner.live.http_get", lambda url, timeout=12.0: (200, PAGE_WITH_PAIN))
    discovered = parse_gumroad_discover(_gumroad_html(2))
    enriched, notes = fetch_gumroad_pages(discovered)
    assert len(enriched) == 2
    for signal in enriched:
        assert signal.pain_points
        # The quote is a sentence the page actually wrote.
        assert "can't tell what they earned" in " ".join(signal.pain_points)
        # Gate 4 reads signal.text, so the page words have to land there too.
        assert "can't tell what they earned" in signal.text
        assert signal.fixture is False
    assert any("→ 200" in note for note in notes)


def test_gumroad_product_page_without_pain_has_no_pain_points(monkeypatch):
    monkeypatch.setattr(
        "runner.live.http_get",
        lambda url, timeout=12.0: (200, PAGE_WITHOUT_PAIN),
    )
    discovered = parse_gumroad_discover(_gumroad_html(3))
    enriched, _ = fetch_gumroad_pages(discovered)
    assert len(enriched) == 3
    for signal in enriched:
        assert signal.pain_points == ()
        assert signal.buying_signals == ()
        assert signal.url.startswith("https://")


def test_gumroad_page_faq_is_not_buyer_pain(monkeypatch):
    """A seller answering their own FAQ says "how do I" without being in pain."""
    faq_page = (
        "<html><body><h1>Bookkeeping Tracker</h1>"
        "<p>Instant download. Google Sheets and Excel.</p>"
        "<p>FAQs: Q: How do I access the Google Sheets version? "
        "A: You will receive a PDF in the ZIP file.</p>"
        "</body></html>"
    )
    monkeypatch.setattr("runner.live.http_get", lambda url, timeout=12.0: (200, faq_page))
    discovered = parse_gumroad_discover(_gumroad_html(1))
    enriched, _ = fetch_gumroad_pages(discovered)
    assert enriched[0].pain_points == ()
    assert "Bookkeeping Tracker" in enriched[0].text


def test_gumroad_page_pain_is_quoted_as_a_sentence(monkeypatch):
    page = (
        "<html><body><h1>Shop Books</h1>"
        "<p>Instant download. Sellers tell me they can't see profit per order "
        "and give up halfway through the month. Works in Excel.</p>"
        "</body></html>"
    )
    monkeypatch.setattr("runner.live.http_get", lambda url, timeout=12.0: (200, page))
    enriched, _ = fetch_gumroad_pages(parse_gumroad_discover(_gumroad_html(1)))
    pain = enriched[0].pain_points[0]
    assert pain.startswith("Sellers tell me")
    assert pain.endswith("month.")


def test_gumroad_page_failure_keeps_sourced_row_without_pain(monkeypatch):
    monkeypatch.setattr("runner.live.http_get", lambda url, timeout=12.0: (500, "nope"))
    discovered = parse_gumroad_discover(_gumroad_html(2))
    enriched, notes = fetch_gumroad_pages(discovered)
    assert [s.url for s in enriched] == [s.url for s in discovered]
    assert all(s.pain_points == () for s in enriched)
    assert all(not s.fixture for s in enriched)
    assert any("→ 500" in note for note in notes)
    assert any("no invented pain" in note for note in notes)


def test_gumroad_pages_are_capped(monkeypatch):
    calls: list[str] = []

    def fake_get(url, timeout=12.0):
        calls.append(url)
        return 200, PAGE_WITH_PAIN

    monkeypatch.setattr("runner.live.http_get", fake_get)
    discovered = parse_gumroad_discover(_gumroad_html(11))
    enriched, notes = fetch_gumroad_pages(discovered)
    assert len(enriched) == 11
    assert len(calls) == 8
    assert any("capped at 8" in note for note in notes)


def test_gumroad_discover_then_pages(monkeypatch):
    html = _gumroad_html(3)

    def fake_get(url, timeout=12.0):
        if "discover" in url:
            return 200, html
        return 200, PAGE_WITH_PAIN

    monkeypatch.setattr("runner.live.http_get", fake_get)
    signals, notes = fetch_gumroad("etsy shop bookkeeping")
    assert len(signals) == 3
    assert all(s.pain_points for s in signals)
    assert any("gumroad parsed 3 products" in note for note in notes)
    assert any("pages with pain language: 3" in note for note in notes)


def test_reddit_403_is_recorded_once_and_not_retried(monkeypatch):
    calls: list[str] = []

    def fake_get(url, timeout=12.0):
        calls.append(url)
        return 403, "Blocked"

    monkeypatch.setattr("runner.live.http_get", fake_get)
    from runner.live import fetch_reddit

    signals, notes = fetch_reddit("etsy shop bookkeeping")
    assert signals == []
    assert len(calls) == 1
    assert any("→ 403" in note for note in notes)
    assert any("not retried" in note for note in notes)


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
