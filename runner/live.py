"""
Public/unauth HTTP scouts plus optional Tavily. No required secrets.

Failures become empty lists and a note. Public Reddit answers 403 without auth;
that is recorded once and not retried, because Tavily is the Reddit path that
can work.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from runner.clues import (
    _buying_from_text,
    _pain_from_text,
    has_pain_intent,
    pain_window,
)
from runner.models import Signal
from runner.tavily import fetch_tavily_reddit

USER_AGENT = "HeadlessStudio/1.0 (read-only research)"
TIMEOUT_SEC = 12.0
REDDIT_SEARCH = "https://www.reddit.com/search.json?q={q}&limit=25&sort=new&raw_json=1"
GUMROAD_DISCOVER = "https://gumroad.com/discover?query={q}"
GUMROAD_PAGE_CAP = 8
PAGE_SNIPPET_CHARS = 400


def http_get(url: str, timeout: float = TIMEOUT_SEC) -> tuple[int, str]:
    """GET url. Returns (status, body). status 0 means transport failure."""
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
        },
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
            return int(getattr(resp, "status", 200) or 200), body
    except HTTPError as exc:
        try:
            err_body = exc.read().decode("utf-8", "replace") if exc.fp else ""
        except Exception:
            err_body = ""
        return int(exc.code), err_body or str(exc.reason or exc)
    except (URLError, TimeoutError, OSError) as exc:
        return 0, f"{type(exc).__name__}: {exc}"


def _reddit_url(data: dict) -> str:
    permalink = str(data.get("permalink") or "").strip()
    if permalink.startswith("/"):
        return "https://www.reddit.com" + permalink
    raw = str(data.get("url") or "").strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    return ""


def parse_reddit_listing(body: str) -> list[Signal]:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return []
    children = (payload.get("data") or {}).get("children") or []
    signals: list[Signal] = []
    seen: set[str] = set()
    for child in children:
        data = child.get("data") if isinstance(child, dict) else None
        if not isinstance(data, dict):
            continue
        url = _reddit_url(data)
        if not url or url in seen:
            continue
        title = str(data.get("title") or "").strip()
        selftext = str(data.get("selftext") or "").strip()
        text = title if not selftext else f"{title}\n{selftext}"
        text = text.strip()
        if len(text) < 8:
            continue
        seen.add(url)
        sid = str(data.get("id") or url)
        signals.append(
            Signal(
                id=f"rd-{sid}",
                source="reddit",
                text=text[:800],
                url=url,
                created_at=str(data.get("created_utc") or ""),
                fixture=False,
                pain_points=_pain_from_text(text),
                buying_signals=_buying_from_text(text),
                author=str(data.get("author") or ""),
                engagement=int(data.get("score") or 0),
                relevance=0.75 if has_pain_intent(text) else 0.5,
            )
        )
    return signals


def fetch_reddit(topic: str) -> tuple[list[Signal], list[str]]:
    """
    Optional extra hop: the public Reddit search JSON.

    Unauthenticated Reddit usually answers 403. That status is recorded and the
    scout moves on — no extra headers, no old.reddit, no oauth, no retries.
    """
    notes: list[str] = []
    signals: list[Signal] = []
    seen: set[str] = set()
    if not topic.strip():
        return signals, ["reddit: no topic to search → skipped"]
    url = REDDIT_SEARCH.format(q=quote(topic))
    status, body = http_get(url)
    notes.append(f"reddit GET {url} → {status}")
    if status in (403, 429):
        notes.append("reddit: blocked without auth, expected → not retried (Tavily is the path)")
        return signals, notes
    if status != 200:
        return signals, notes
    for signal in parse_reddit_listing(body):
        if signal.url in seen:
            continue
        seen.add(signal.url)
        signals.append(signal)
    return signals, notes


def _brace_object(text: str, start: int) -> str | None:
    i = text.find("{", start)
    if i < 0:
        return None
    depth = 0
    in_str = False
    escape = False
    for j, ch in enumerate(text[i:], i):
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[i : j + 1]
    return None


def parse_gumroad_discover(html: str) -> list[Signal]:
    unesc = unescape(html).replace("&quot;", '"')
    match = re.search(r'"search_results"\s*:\s*\{', unesc)
    if not match:
        return []
    blob = _brace_object(unesc, match.start())
    if not blob:
        return []
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return []
    products = data.get("products") or []
    if isinstance(products, dict):
        products = products.get("products") or products.get("results") or []
    signals: list[Signal] = []
    seen: set[str] = set()
    for item in products:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        permalink = str(item.get("permalink") or "").strip()
        if not url and permalink:
            url = f"https://gumroad.com/l/{permalink}"
        if not name or not (url.startswith("http://") or url.startswith("https://")):
            continue
        if url in seen:
            continue
        seen.add(url)
        seller = item.get("seller") if isinstance(item.get("seller"), dict) else {}
        seller_name = str((seller or {}).get("name") or item.get("seller_name") or "").strip()
        price = item.get("price_cents")
        extra = []
        if seller_name:
            extra.append(f"seller {seller_name}")
        if isinstance(price, int):
            extra.append(f"{price} cents")
        text = name if not extra else f"{name} ({', '.join(extra)})"
        sid = permalink or url
        signals.append(
            Signal(
                id=f"gr-{sid}",
                source="gumroad",
                text=text[:800],
                url=url,
                fixture=False,
                author=seller_name,
                engagement=int(item.get("review_count") or 0),
                relevance=0.5,
            )
        )
    return signals


_SCRIPT_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.S | re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_META_DESC_RE = re.compile(
    r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\'][^>]*'
    r"content=([\"'])(.{8,}?)\1",
    re.I | re.S,
)
_JSON_DESC_RE = re.compile(
    r'"(?:description|full_description|custom_summary)"\s*:\s*"((?:[^"\\]|\\.){8,}?)"'
)


def _json_string(raw: str) -> str:
    try:
        return json.loads(f'"{raw}"')
    except json.JSONDecodeError:
        return raw


def gumroad_page_text(html: str) -> str:
    """
    Readable text from a product page: meta/embedded description plus visible body.

    No JS is executed and nothing is logged in. Whatever the page actually shows
    is all this returns.
    """
    unesc = unescape(html)
    parts: list[str] = [match.group(2) for match in _META_DESC_RE.finditer(unesc)]
    json_ish = unesc.replace("&quot;", '"')
    parts.extend(_json_string(match.group(1)) for match in _JSON_DESC_RE.finditer(json_ish))
    body = _TAG_RE.sub(" ", _SCRIPT_RE.sub(" ", unesc))
    parts.append(body)
    flat = " ".join(" ".join(part.split()) for part in parts if part and part.strip())
    return flat[:4000]


def _with_page_text(signal: Signal, page_text: str) -> Signal:
    """Fold page text into the row. Pain is attached only if the page says it."""
    window = pain_window(page_text)
    snippet = window or " ".join(page_text.split())[:PAGE_SNIPPET_CHARS]
    if not snippet:
        return signal
    text = f"{signal.text}\n{snippet}"[:800]
    if not window:
        # Product titles and marketing furniture are not buyer pain.
        return replace(signal, text=text)
    return replace(
        signal,
        text=text,
        pain_points=_pain_from_text(window),
        buying_signals=_buying_from_text(page_text),
        relevance=max(signal.relevance, 0.7),
    )


def fetch_gumroad_pages(
    signals: list[Signal],
    cap: int = GUMROAD_PAGE_CAP,
) -> tuple[list[Signal], list[str]]:
    """
    GET each discovered product page (capped) and read pain/intent off the page.

    A failed page GET keeps the discover row as sourced competition with no
    invented pain, and records the status.
    """
    notes: list[str] = []
    out: list[Signal] = []
    for index, signal in enumerate(signals):
        if index >= cap:
            out.append(signal)
            continue
        status, body = http_get(signal.url)
        notes.append(f"gumroad page GET {signal.url} → {status}")
        if status != 200:
            notes.append("gumroad page unreadable → kept as competition, no invented pain")
            out.append(signal)
            continue
        out.append(_with_page_text(signal, gumroad_page_text(body)))
    if len(signals) > cap:
        notes.append(f"gumroad pages capped at {cap} of {len(signals)}")
    with_pain = sum(1 for s in out if s.pain_points)
    if out:
        notes.append(f"gumroad pages with pain language: {with_pain} of {min(len(out), cap)}")
    return out, notes


def fetch_gumroad(topic: str) -> tuple[list[Signal], list[str]]:
    if not topic.strip():
        return [], ["gumroad: no topic to search → skipped"]
    url = GUMROAD_DISCOVER.format(q=quote(topic))
    status, body = http_get(url)
    notes = [f"gumroad GET {url} → {status}"]
    if status != 200:
        return [], notes
    signals = parse_gumroad_discover(body)
    notes.append(f"gumroad parsed {len(signals)} products")
    if not signals:
        return signals, notes
    enriched, page_notes = fetch_gumroad_pages(signals)
    notes.extend(page_notes)
    return enriched, notes


def live_signals(topic: str) -> tuple[list[Signal], list[str]]:
    """
    Tavily Reddit (optional key) → public Reddit JSON → Gumroad discover + pages.

    No required secrets. Fixtures are never mixed in here.
    """
    notes: list[str] = ["scout: read-only try (Tavily optional, no required secrets)"]
    collected: list[Signal] = []
    seen: set[str] = set()
    for fetcher in (fetch_tavily_reddit, fetch_reddit, fetch_gumroad):
        try:
            rows, extra = fetcher(topic)
        except Exception as exc:
            notes.append(f"{fetcher.__name__} raised {type(exc).__name__}: {exc}")
            continue
        notes.extend(extra)
        for signal in rows:
            if signal.fixture or not signal.url or signal.url in seen:
                continue
            seen.add(signal.url)
            collected.append(signal)
    notes.append(f"live sourced candidates: {len(collected)}")
    return collected, notes
