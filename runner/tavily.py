"""
Optional Tavily search for Reddit buyer language. Read-only, stdlib only.

The key is optional. It is never printed, never logged, and never written to a
receipt. Tavily is only the transport: rows it returns are Reddit rows, so the
signal source stays "reddit".
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from runner.clues import _buying_from_text, _pain_from_text, has_pain_intent
from runner.models import Signal

TAVILY_URL = "https://api.tavily.com/search"
KEY_NAME = "TAVILY_API_KEY"
HERMES_ENV_PATH = Path.home() / ".hermes" / ".env"
USER_AGENT = "HeadlessStudio/1.0 (read-only research)"
TIMEOUT_SEC = 12.0
MAX_RESULTS = 10
REDDIT_DOMAIN = "reddit.com"

# Buyer language, not hype. Pain still has to come out of the returned text.
BUYER_LANGUAGE = ("looking for", "need help", "how do I", "would pay")

NO_KEY_NOTE = "tavily: no key in process env or Hermes .env → fallback"


def key_from_hermes_env(path: str | Path | None = None) -> str:
    """
    Read only TAVILY_API_KEY out of a Hermes-style KEY=VALUE file.

    Every other line is ignored, nothing is echoed, and a missing file is not
    an error. Returns "" when the key is absent.
    """
    target = Path(path) if path is not None else HERMES_ENV_PATH
    try:
        raw = target.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, _, value = stripped.partition("=")
        if name.strip() != KEY_NAME:
            continue
        return value.strip().strip('"').strip("'")
    return ""


def resolve_key() -> tuple[str, str]:
    """(key, note). The note describes where the key came from, never its value."""
    env_key = (os.environ.get(KEY_NAME) or "").strip()
    if env_key:
        return env_key, "tavily: key from process env (value not logged)"
    hermes_key = key_from_hermes_env()
    if hermes_key:
        return hermes_key, "tavily: key from Hermes .env (value not logged)"
    return "", NO_KEY_NOTE


def reddit_query(topic: str) -> str:
    """site:reddit.com plus the topic's buyer language."""
    clean = " ".join(topic.split())
    wants = " OR ".join(f'"{phrase}"' for phrase in BUYER_LANGUAGE)
    return f"site:{REDDIT_DOMAIN} {clean} ({wants})"


def search_payload(topic: str) -> dict:
    """Search body. No include_answer, no include_raw_content."""
    return {
        "query": reddit_query(topic),
        "include_domains": [REDDIT_DOMAIN],
        "search_depth": "basic",
        "max_results": MAX_RESULTS,
        "topic": "general",
    }


def http_post_json(
    url: str,
    key: str,
    payload: dict,
    timeout: float = TIMEOUT_SEC,
) -> tuple[int, str]:
    """POST json with urllib. Returns (status, body). status 0 is a transport failure."""
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", "replace")
            return int(getattr(resp, "status", 200) or 200), text
    except HTTPError as exc:
        return int(exc.code), ""
    except (URLError, TimeoutError, OSError) as exc:
        return 0, type(exc).__name__


def _signal_id(url: str) -> str:
    tail = url.rstrip("/").rsplit("/", 1)[-1].lower()
    slug = re.sub(r"[^a-z0-9]+", "-", tail).strip("-")
    return f"tv-{slug[:32]}" if slug else f"tv-{abs(hash(url)) % 10**8}"


def parse_tavily_results(body: str) -> list[Signal]:
    """
    Tavily results → sourced reddit signals.

    A row needs a real http(s) URL to count; anything else is dropped. Pain and
    buying language come only from the returned title/content snippets.
    """
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, dict):
        return []
    results = payload.get("results")
    if not isinstance(results, list):
        return []

    signals: list[Signal] = []
    seen: set[str] = set()
    for item in results:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            continue
        if url in seen:
            continue
        title = str(item.get("title") or "").strip()
        content = str(item.get("content") or "").strip()
        text = "\n".join(part for part in (title, content) if part).strip()
        if len(text) < 8:
            continue
        seen.add(url)
        signals.append(
            Signal(
                id=_signal_id(url),
                source="reddit",
                text=text[:800],
                url=url,
                created_at=str(item.get("published_date") or ""),
                fixture=False,
                pain_points=_pain_from_text(text),
                buying_signals=_buying_from_text(text),
                relevance=0.75 if has_pain_intent(text) else 0.5,
            )
        )
    return signals


def fetch_tavily_reddit(topic: str) -> tuple[list[Signal], list[str]]:
    """
    Reddit rows via Tavily when a key resolves. No key means no rows and a note.

    HTTP failures, 401s and empty result sets are noted and skipped. Nothing
    here raises, and no fixtures are substituted.
    """
    notes: list[str] = []
    if not topic.strip():
        notes.append("tavily: no topic to search → skipped")
        return [], notes

    key, key_note = resolve_key()
    notes.append(key_note)
    if not key:
        return [], notes

    status, body = http_post_json(TAVILY_URL, key, search_payload(topic))
    notes.append(f"tavily POST {TAVILY_URL} → {status}")
    if status != 200:
        notes.append("tavily: no usable response → continuing without Tavily rows")
        return [], notes

    rows = parse_tavily_results(body)
    if not rows:
        notes.append("tavily: 0 results with a real URL → continuing without Tavily rows")
        return [], notes

    notes.append(f"tavily: {len(rows)} reddit rows via Tavily (source=reddit)")
    return rows, notes
