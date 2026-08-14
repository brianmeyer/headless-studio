"""Public/unauth HTTP scouts. No secrets. Failures become empty lists."""

from __future__ import annotations

import json
import re
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from runner.clues import has_pain_intent
from runner.models import Signal

USER_AGENT = "HeadlessStudio/1.0 (read-only research)"
TIMEOUT_SEC = 12.0
REDDIT_SEARCH = "https://www.reddit.com/search.json?q={q}&limit=25&sort=new&raw_json=1"
REDDIT_PROPERTY = (
    "https://www.reddit.com/r/PropertyManagement/search.json"
    "?q={q}&restrict_sr=1&limit=25&sort=new&raw_json=1"
)
GUMROAD_DISCOVER = "https://gumroad.com/discover?query={q}"


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


def _pain_from_text(text: str) -> tuple[str, ...]:
    if not has_pain_intent(text):
        return ()
    snippet = " ".join(text.split())
    return (snippet[:160],) if len(snippet) >= 8 else ()


def _buying_from_text(text: str) -> tuple[str, ...]:
    lowered = text.lower()
    found: list[str] = []
    for phrase in ("looking for", "would pay", "willing to pay", "need help", "need a prompt"):
        if phrase in lowered:
            found.append(phrase)
    return tuple(found)


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
    notes: list[str] = []
    signals: list[Signal] = []
    seen: set[str] = set()
    urls = [REDDIT_SEARCH.format(q=quote(topic))]
    lowered = topic.lower()
    if any(word in lowered for word in ("property", "tenant", "listing", "landlord")):
        urls.append(REDDIT_PROPERTY.format(q=quote(topic)))
    for url in urls:
        status, body = http_get(url)
        notes.append(f"reddit GET {url} → {status}")
        if status != 200:
            continue
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


def fetch_gumroad(topic: str) -> tuple[list[Signal], list[str]]:
    url = GUMROAD_DISCOVER.format(q=quote(topic))
    status, body = http_get(url)
    notes = [f"gumroad GET {url} → {status}"]
    if status != 200:
        return [], notes
    signals = parse_gumroad_discover(body)
    notes.append(f"gumroad parsed {len(signals)} products")
    return signals, notes


def live_signals(topic: str) -> tuple[list[Signal], list[str]]:
    """Try public Reddit, then public Gumroad. No secrets."""
    notes: list[str] = ["scout: public-try (no required secrets)"]
    collected: list[Signal] = []
    seen: set[str] = set()
    for fetcher in (fetch_reddit, fetch_gumroad):
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
