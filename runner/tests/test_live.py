"""Public HTTP scout: live rows are sourced; fixtures never are."""

from __future__ import annotations

import json
from pathlib import Path

from runner import run
from runner.live import parse_gumroad_discover, parse_gumroad_product, parse_reddit_listing
from runner.fixtures import fixture_signals
from runner.scorer import sourced_signals
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
    """Tiny inline Gumroad discover HTML in the current Inertia data-page format."""
    products = []
    for i in range(n):
        products.append(
            {
                "name": f"Prompt Pack {i} for Agents",
                "permalink": f"pack{i}",
                "url": f"https://example.gumroad.com/l/pack{i}",
                "price_cents": 1500 + i,
                "seller": {"name": f"Seller {i}"},
                "ratings": {"count": 10 + i, "average": 4.5},
            }
        )
    page = json.dumps({"props": {"search_results": {"total": n, "products": products}}})
    escaped = page.replace('"', "&quot;")
    return f'<div id="app" data-page="{escaped}"></div>'


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


def test_public_gumroad_html_yields_sourced_signals(monkeypatch):
    """Public Gumroad HTML with >=5 products -> >=5 non-fixture sourced http signals; fixtures not counted."""
    html = _gumroad_html(6)

    def fake_get(url, timeout=12.0):
        if "gumroad.com" in url:
            return 200, html
        return 403, "Blocked"  # reddit blocked from this Mac

    monkeypatch.setattr("runner.live.http_get", fake_get)
    monkeypatch.delenv("GREEN_FORCE_FIXTURES", raising=False)
    outcome = scout("chatgpt prompts for property managers")
    assert not outcome.used_fixtures
    sourced = sourced_signals(outcome.signals)
    assert len(sourced) >= 5
    assert all(not s.fixture for s in sourced)
    assert all(s.url.startswith("http") for s in sourced)
    assert all(s.source == "gumroad" for s in sourced)
    # live succeeded -> fixtures are not mixed in to inflate counts
    assert not any(s.fixture for s in outcome.signals)


def test_reddit_403_and_gumroad_fail_uses_fixtures(monkeypatch):
    """Reddit 403 + Gumroad transport fail -> fixtures fallback, still miss, no crash."""
    monkeypatch.delenv("GREEN_FORCE_FIXTURES", raising=False)

    def fake_get(url, timeout=12.0):
        if "reddit.com" in url:
            return 403, "Blocked"
        if "gumroad.com" in url:
            return 0, "URLError: blocked"
        return 0, "skip"

    monkeypatch.setattr("runner.live.http_get", fake_get)
    outcome = scout("chatgpt prompts for property managers")
    assert outcome.used_fixtures is True
    assert all(s.fixture for s in outcome.signals)
    notes = " ".join(outcome.notes)
    assert "403" in notes
    assert "fixtures" in notes.lower()


def test_fixtures_never_opens_url(monkeypatch):
    """--fixtures and GREEN_FORCE_FIXTURES=1 must never open a URL."""

    def boom(*args, **kwargs):
        raise AssertionError(f"urlopen must not be called: {args!r}")

    monkeypatch.setattr("runner.live.urlopen", boom)

    # explicit --fixtures / force_fixtures
    outcome = scout("chatgpt prompts for property managers", use_fixtures=True)
    assert outcome.used_fixtures is True
    assert all(s.fixture for s in outcome.signals)

    # env var path
    monkeypatch.setenv("GREEN_FORCE_FIXTURES", "1")
    outcome2 = scout("chatgpt prompts for property managers")
    assert outcome2.used_fixtures is True
    assert all(s.fixture for s in outcome2.signals)


def test_fixture_rows_mixed_with_live_still_not_sourced(tmp_path: Path, monkeypatch):
    """Fixture rows mixed into a live run must not count as sourced or inflate gate 1."""
    monkeypatch.delenv("GREEN_FORCE_FIXTURES", raising=False)
    live = parse_gumroad_discover(_gumroad_html(6))
    assert len(live) >= 5
    mixed = live + fixture_signals("chatgpt prompts for property managers")
    receipt = tmp_path / "RECEIPT.md"
    result = run(
        topic="chatgpt prompts for property managers",
        out_path=receipt,
        signals=mixed,
    )
    sourced = sourced_signals(result.signals)
    assert all(not s.fixture for s in sourced)
    assert len(sourced) == len(live)
    # fixtures are present in the receipt rows but excluded from the gate count
    assert any(s.fixture for s in result.signals)
    gate1 = result.gates.by_name("sourced_signals")
    assert gate1 is not None
    assert int(gate1.detail.split()[0]) == len(live)


def test_react_on_rails_discover_fallback_parses():
    """Older React-on-Rails data-component-name='Discover' JSON still parses."""
    products = [
        {
            "name": f"Prompt Pack {i}",
            "permalink": f"pack{i}",
            "url": f"https://gumroad.com/l/pack{i}",
            "price_cents": 1900 + i,
            "seller": {"name": f"Seller {i}"},
            "ratings": {"count": 3 + i, "average": 4.0},
        }
        for i in range(5)
    ]
    blob = json.dumps({"search_results": {"products": products}})
    html = f'<script data-component-name="Discover">{blob}</script>'
    signals = parse_gumroad_discover(html)
    assert len(signals) == 5
    assert all(not s.fixture for s in signals)
    assert all(s.url.startswith("https://") for s in signals)
    assert all(0.4 <= s.relevance <= 0.7 for s in signals)
    assert signals[0].engagement == 3  # ratings.count


def _product_html_inertia(pain: str, summary: str = "Prompt pack for property managers") -> str:
    """Current Gumroad product page: Inertia data-page with description_html."""
    page = {
        "props": {
            "product": {
                "name": "Prompt Pack",
                "summary": summary,
                "description_html": f"<p>{pain}</p><ul><li>50 prompts</li></ul>",
            }
        }
    }
    escaped = json.dumps(page).replace("&", "&amp;").replace('"', "&quot;")
    return f'<div id="app" data-page="{escaped}"></div>'


def _product_html_meta(pain: str) -> str:
    return (
        "<html><head>"
        f'<meta name="description" content="{pain}">'
        '<meta property="og:description" content="Prompt pack.">'
        "</head><body></body></html>"
    )


def _product_html_ldjson(pain: str) -> str:
    blob = json.dumps({"@type": "Product", "name": "Pack", "description": pain})
    return f'<html><head><script type="application/ld+json">{blob}</script></head></html>'


PRODUCT_PAIN = (
    "For property managers tired of rewriting listing copy from scratch. "
    "Stop the manual copy-paste that wastes hours every week."
)


def test_parse_gumroad_product_extracts_pain_from_inertia():
    parsed = parse_gumroad_product(_product_html_inertia(PRODUCT_PAIN))
    assert parsed["source"] == "inertia"
    assert "tired of rewriting listing copy from scratch" in parsed["text"].lower()
    assert "<p>" not in parsed["text"]
    assert "50 prompts" in parsed["text"]
    from runner.live import _pain_from_text

    assert _pain_from_text(parsed["text"])


def test_parse_gumroad_product_extracts_pain_from_meta_description():
    parsed = parse_gumroad_product(_product_html_meta(PRODUCT_PAIN))
    assert parsed["source"] == "meta-description"
    assert "from scratch" in parsed["text"].lower()


def test_parse_gumroad_product_extracts_pain_from_ld_json():
    parsed = parse_gumroad_product(_product_html_ldjson(PRODUCT_PAIN))
    assert parsed["source"] == "ld-json"
    assert "manual" in parsed["text"].lower()


def test_parse_gumroad_product_hype_only_yields_no_pain():
    from runner.clues import is_hype_only
    from runner.live import _buying_from_text, _pain_from_text

    hype = "This game changer is revolutionary. 10x viral must-have passive income."
    parsed = parse_gumroad_product(_product_html_inertia(hype, summary="Insane pack"))
    assert parsed["text"]
    assert is_hype_only(parsed["text"])
    assert _pain_from_text(parsed["text"]) == ()
    assert _buying_from_text(parsed["text"]) == ()


def test_parse_gumroad_product_empty_on_unreadable_page():
    parsed = parse_gumroad_product("<html><body>no description here</body></html>")
    assert parsed["text"] == ""
    assert parsed["source"] == ""


def _distinct_pain_products() -> dict[str, str]:
    """Distinct real pain/intent copy per product URL — three+ separate clues."""
    pains = [
        "Property managers tired of rewriting listing copy from scratch every week.",
        "Stop the manual copy-paste workflow that wastes hours on tenant notices.",
        "Looking for a template pack because the old renewal letters are broken.",
        "For teams overwhelmed by inbound maintenance email with no time to reply.",
        "If you would pay to stop starting over on every vacancy ad, this is it.",
        "Owners frustrated that generic templates doesn't work for their portfolio.",
    ]
    return {
        f"https://example.gumroad.com/l/pack{i}": _product_html_inertia(
            pain, summary=f"Prompt pack {i} for property managers"
        )
        for i, pain in enumerate(pains)
    }


def test_mocked_product_pages_pass_gate_two(tmp_path: Path, monkeypatch):
    """Discover + product pages with >=3 distinct pain/intent phrases -> gate 2 passes."""
    monkeypatch.delenv("GREEN_FORCE_FIXTURES", raising=False)
    discover = _gumroad_html(6)
    products = _distinct_pain_products()

    def fake_get(url, timeout=12.0):
        if url in products:
            return 200, products[url]
        if "gumroad.com/discover" in url:
            return 200, discover
        return 403, "Blocked"

    monkeypatch.setattr("runner.live.http_get", fake_get)
    receipt = tmp_path / "RECEIPT.md"
    result = run(topic="chatgpt prompts for property managers", out_path=receipt)

    assert all(not s.fixture for s in result.signals)
    assert all(s.source == "gumroad" for s in result.signals)
    gate2 = result.gates.by_name("pain_intent_clues")
    assert gate2 is not None
    assert gate2.passed, gate2.detail
    assert len(result.clues) >= 3
    assert any(s.pain_points for s in result.signals)
    assert any(s.relevance == 0.75 for s in result.signals)
    # verdict may still be miss if score / gate 3 fails — that is OK
    assert result.verdict in {"hit", "miss"}
    assert not (tmp_path / "mocks").exists()


def test_product_page_cap_is_eight(monkeypatch):
    """At most 8 product pages are fetched per run."""
    monkeypatch.delenv("GREEN_FORCE_FIXTURES", raising=False)
    discover = _gumroad_html(12)
    calls: list[str] = []

    def fake_get(url, timeout=12.0):
        calls.append(url)
        if "gumroad.com/discover" in url:
            return 200, discover
        if "/l/pack" in url:
            return 200, _product_html_meta(PRODUCT_PAIN)
        return 403, "Blocked"

    monkeypatch.setattr("runner.live.http_get", fake_get)
    from runner.live import fetch_gumroad

    signals, notes = fetch_gumroad("chatgpt prompts for property managers")
    product_calls = [u for u in calls if "/l/pack" in u]
    assert len(product_calls) == 8
    assert len(signals) == 12  # rows are enriched, never dropped
    assert sum(1 for s in signals if s.pain_points) == 8
    assert any("cap 8" in note for note in notes)


def test_product_get_failure_keeps_sourced_rows_without_invented_pain(
    tmp_path: Path, monkeypatch
):
    """Product GET 403/0 -> discover rows stay sourced, no invented pain, miss, no mock."""
    monkeypatch.delenv("GREEN_FORCE_FIXTURES", raising=False)
    discover = _gumroad_html(6)

    def fake_get(url, timeout=12.0):
        if "gumroad.com/discover" in url:
            return 200, discover
        if "/l/pack0" in url or "/l/pack1" in url:
            return 0, "URLError: connection reset"
        if "/l/pack" in url:
            return 403, "Blocked"
        return 403, "Blocked"

    monkeypatch.setattr("runner.live.http_get", fake_get)
    receipt = tmp_path / "RECEIPT.md"
    result = run(topic="chatgpt prompts for property managers", out_path=receipt)

    assert len(sourced_signals(result.signals)) == 6
    assert all(not s.fixture for s in result.signals)
    assert all(s.pain_points == () for s in result.signals)
    assert all(s.buying_signals == () for s in result.signals)
    assert result.verdict == "miss"
    assert not (tmp_path / "mocks").exists()
    notes = " ".join(result.notes)
    assert "product GET" in notes
    assert "0 with pain/intent" in notes


def test_scout_notes_record_product_statuses(monkeypatch):
    """Scout notes must record product GET statuses and pain/intent page counts."""
    monkeypatch.delenv("GREEN_FORCE_FIXTURES", raising=False)
    discover = _gumroad_html(6)
    products = _distinct_pain_products()

    def fake_get(url, timeout=12.0):
        if url in products:
            return 200, products[url]
        if "gumroad.com/discover" in url:
            return 200, discover
        return 403, "Blocked"

    monkeypatch.setattr("runner.live.http_get", fake_get)
    outcome = scout("chatgpt prompts for property managers")
    notes = " ".join(outcome.notes)
    assert "gumroad product GET" in notes
    assert "→ 200" in notes
    assert "with pain/intent" in notes
    assert not outcome.used_fixtures


def test_pain_sentences_quote_source_and_drop_hype():
    """Pain is quoted verbatim from pain-bearing sentences; hype sentences drop out."""
    from runner.live import _pain_sentences

    text = (
        "This pack is a revolutionary game changer. "
        "Property managers are tired of rewriting listing copy from scratch. "
        "It is a 10x viral must-have. "
        "The manual copy-paste workflow wastes hours every week."
    )
    found = _pain_sentences(text)
    assert len(found) == 2
    joined = " ".join(found).lower()
    assert "tired of rewriting listing copy from scratch" in joined
    assert "manual copy-paste" in joined
    assert "game changer" not in joined
    assert "viral" not in joined
    for sentence in found:
        assert sentence in text  # verbatim, never invented


def test_pain_sentences_reach_pain_past_the_first_160_chars():
    """Long marketing lead-in must not hide the real pain sentence behind it."""
    from runner.live import _pain_sentences

    lead = "Welcome to the complete professional toolkit for modern real estate teams. " * 3
    text = lead + "Agents are tired of rewriting listing copy from scratch."
    assert len(lead) > 160
    found = _pain_sentences(text)
    assert found
    assert "tired of rewriting listing copy from scratch" in found[0].lower()



def test_enrichment_skips_non_gumroad_urls(monkeypatch):
    """Product enrichment must not GET arbitrary hosts from discover JSON."""
    from runner.live import enrich_gumroad_products, is_public_gumroad_url
    from runner.models import Signal

    assert is_public_gumroad_url("https://seller.gumroad.com/l/pack")
    assert is_public_gumroad_url("https://gumroad.com/l/pack")
    assert not is_public_gumroad_url("http://gumroad.com/l/pack")
    assert not is_public_gumroad_url("https://evil.example/l/pack")
    assert not is_public_gumroad_url("file:///etc/passwd")

    def boom(url, timeout=12.0):
        raise AssertionError(f"http_get must not run for {url}")

    monkeypatch.setattr("runner.live.http_get", boom)
    signals = [
        Signal(
            id="gr-evil",
            source="gumroad",
            text="Prompt pack",
            url="https://evil.example/l/pack",
            fixture=False,
        )
    ]
    out, notes = enrich_gumroad_products(signals)
    assert len(out) == 1
    assert out[0].url == "https://evil.example/l/pack"
    assert out[0].pain_points == ()
    assert any("skipped" in n for n in notes)
