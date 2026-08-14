"""Public/unauth HTTP scouts. No secrets. Failures become empty lists."""

from __future__ import annotations

import json
import re
from dataclasses import replace
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from runner.clues import has_pain_intent, is_hype_only
from runner.models import Signal

USER_AGENT = "HeadlessStudio/1.0 (read-only research)"
TIMEOUT_SEC = 12.0
GUMROAD_PRODUCT_PAGE_CAP = 8
SIGNAL_TEXT_CAP = 1200
REDDIT_SEARCH = "https://www.reddit.com/search.json?q={q}&limit=25&sort=new&raw_json=1"
REDDIT_PROPERTY = (
    "https://www.reddit.com/r/PropertyManagement/search.json"
    "?q={q}&restrict_sr=1&limit=25&sort=new&raw_json=1"
)
GUMROAD_DISCOVER = "https://gumroad.com/discover?query={q}"



def is_public_gumroad_url(url: str) -> bool:
    """True only for https Gumroad hosts. Enrichment must not follow arbitrary URLs."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme != "https":
        return False
    host = (parsed.hostname or "").lower()
    return host == "gumroad.com" or host.endswith(".gumroad.com")


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


def _gumroad_relevance(count: int, average) -> float:
    """Map a product's rating signal to a 0.4-0.7 relevance band."""
    rel = 0.45
    if count and count > 0:
        rel = 0.55
    try:
        if average is not None and float(average) >= 4.0 and (count or 0) >= 5:
            rel = 0.65
    except (TypeError, ValueError):
        pass
    return max(0.4, min(0.7, rel))


def _products_from_search_results(data: dict) -> list[dict]:
    """Pull the product list out of an Inertia props.search_results or legacy blob."""
    if not isinstance(data, dict):
        return []
    props = data.get("props") if isinstance(data.get("props"), dict) else {}
    search = props.get("search_results") if isinstance(props, dict) else None
    if search is None:
        search = data.get("search_results")
    if search is None:
        return []
    if isinstance(search, dict):
        rows = search.get("products") or search.get("results") or []
    elif isinstance(search, list):
        rows = search
    else:
        rows = []
    return [r for r in rows if isinstance(r, dict)]


def _extract_inertia_page(html: str) -> dict | None:
    """Inertia: <div id="app" data-page="{...}">. Unescape entities then json.loads."""
    match = re.search(r'data-page="([^"]*)"', html)
    if not match:
        return None
    raw = unescape(match.group(1)).replace("&quot;", '"')
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _extract_discover_component(html: str) -> dict | None:
    """Older React-on-Rails: <script data-component-name="Discover">{...}</script>."""
    match = re.search(
        r'data-component-name="Discover"[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not match:
        return None
    try:
        data = json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _extract_search_results_blob(html: str) -> dict | None:
    """Last-resort tolerant parser: brace-match a "search_results": {...} blob."""
    unesc = unescape(html).replace("&quot;", '"')
    match = re.search(r'"search_results"\s*:\s*\{', unesc)
    if not match:
        return None
    blob = _brace_object(unesc, match.start())
    if not blob:
        return None
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def parse_gumroad_discover(html: str) -> list[Signal]:
    """Parse Gumroad discover HTML into sourced (non-fixture) gumroad Signals.

    Supports the current Inertia data-page format, the older React-on-Rails
    Discover component, and a tolerant search_results blob as a final fallback.
    Pain points are never invented — only product name/seller/price/rating text.
    """
    products: list[dict] = []
    for extractor in (_extract_inertia_page, _extract_discover_component):
        data = extractor(html)
        if data:
            products = _products_from_search_results(data)
            if products:
                break
    if not products:
        data = _extract_search_results_blob(html)
        if data:
            if isinstance(data.get("search_results"), dict) or isinstance(
                data.get("props"), dict
            ):
                products = _products_from_search_results(data)
            else:
                rows = data.get("products") or data.get("results") or []
                products = [r for r in rows if isinstance(r, dict)]

    signals: list[Signal] = []
    seen: set[str] = set()
    for item in products:
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
        ratings = item.get("ratings") if isinstance(item.get("ratings"), dict) else {}
        rating_count = int(
            (ratings or {}).get("count")
            or item.get("review_count")
            or item.get("num_reviews")
            or 0
        )
        rating_avg = (ratings or {}).get("average")
        extra = []
        if seller_name:
            extra.append(f"seller {seller_name}")
        if isinstance(price, int):
            extra.append(f"{price} cents")
        if rating_count:
            extra.append(f"{rating_count} ratings")
        text = name if not extra else f"{name} ({', '.join(extra)})"
        sid = permalink or str(item.get("id") or "") or url
        signals.append(
            Signal(
                id=f"gr-{sid}",
                source="gumroad",
                text=text[:800],
                url=url,
                fixture=False,
                author=seller_name,
                engagement=rating_count,
                relevance=_gumroad_relevance(rating_count, rating_avg),
            )
        )
    return signals


_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_RE = re.compile(r"<(script|style)\b.*?</\1>", re.I | re.S)
_BLOCK_RE = re.compile(r"</(p|div|li|h[1-6])>|<br\s*/?>", re.I)


def strip_html(raw: str) -> str:
    """Buyer-facing text out of an HTML fragment. No tags, collapsed whitespace."""
    if not raw:
        return ""
    text = _SCRIPT_RE.sub(" ", raw)
    text = _BLOCK_RE.sub(" ", text)
    text = _TAG_RE.sub(" ", text)
    return " ".join(unescape(text).split())


def _data_page_props(html: str) -> dict:
    """Inertia mounts its payload in a data-page attribute."""
    match = re.search(r"data-page\s*=\s*(\"|')(.*?)\1", html, re.S)
    if not match:
        return {}
    try:
        payload = json.loads(unescape(match.group(2)))
    except (json.JSONDecodeError, TypeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    props = payload.get("props")
    return props if isinstance(props, dict) else {}


def _meta_content(html: str, attr: str, value: str) -> str:
    pattern = (
        rf"<meta[^>]*{attr}\s*=\s*(\"|'){re.escape(value)}\1[^>]*"
        r"content\s*=\s*(\"|')(.*?)\2"
    )
    match = re.search(pattern, html, re.I | re.S)
    if match:
        return " ".join(unescape(match.group(3)).split())
    pattern_rev = (
        rf"<meta[^>]*content\s*=\s*(\"|')(.*?)\1[^>]*"
        rf"{attr}\s*=\s*(\"|'){re.escape(value)}\3"
    )
    match = re.search(pattern_rev, html, re.I | re.S)
    if match:
        return " ".join(unescape(match.group(2)).split())
    return ""


def _ld_json_description(html: str) -> str:
    for block in re.findall(
        r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>", html, re.I | re.S
    ):
        try:
            payload = json.loads(unescape(block.strip()))
        except json.JSONDecodeError:
            continue
        candidates: list[dict] = []
        stack = [payload]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, dict):
                candidates.append(node)
                graph = node.get("@graph")
                if isinstance(graph, (list, dict)):
                    stack.append(graph)
        for node in candidates:
            node_type = node.get("@type")
            types = node_type if isinstance(node_type, list) else [node_type]
            if not any(str(t).lower() == "product" for t in types if t):
                continue
            desc = node.get("description")
            if isinstance(desc, str) and desc.strip():
                return strip_html(desc)
    return ""


def parse_gumroad_product(html: str) -> dict:
    """
    Buyer-facing text from a public Gumroad product page.

    Order: Inertia data-page props.product.summary + description_html,
    then <meta name="description">, og:description, schema.org Product.description.
    Never invents text — an unreadable page returns empty strings.
    """
    if not html:
        return {"summary": "", "description": "", "text": "", "source": ""}

    props = _data_page_props(html)
    product = props.get("product") if isinstance(props.get("product"), dict) else {}
    summary = ""
    description = ""
    source = ""
    if product:
        raw_summary = product.get("summary")
        if isinstance(raw_summary, str):
            summary = strip_html(raw_summary)
        raw_desc = product.get("description_html")
        if isinstance(raw_desc, str):
            description = strip_html(raw_desc)
        if summary or description:
            source = "inertia"

    if not (summary or description):
        meta = _meta_content(html, "name", "description")
        if meta:
            description = meta
            source = "meta-description"

    if not (summary or description):
        og = _meta_content(html, "property", "og:description") or _meta_content(
            html, "name", "og:description"
        )
        if og:
            description = og
            source = "og-description"

    if not (summary or description):
        ld = _ld_json_description(html)
        if ld:
            description = ld
            source = "ld-json"

    parts = [p for p in (summary, description) if p]
    text = " ".join(parts)
    seen_summary = summary.lower()
    if summary and description.lower().startswith(seen_summary):
        text = description
    return {
        "summary": summary,
        "description": description,
        "text": " ".join(text.split()),
        "source": source,
    }


def _pain_sentences(text: str, limit: int = 3) -> tuple[str, ...]:
    """
    Quote only the sentences that themselves trip has_pain_intent.

    Never invents pain: every returned string is verbatim source text that the
    existing pain/intent patterns matched, and hype-only sentences are dropped.
    """
    if not text:
        return ()
    found: list[str] = []
    seen: set[str] = set()
    for raw in re.split(r"(?<=[.!?])\s+|\n+", text):
        sentence = " ".join(raw.split())
        if len(sentence) < 12 or not has_pain_intent(sentence):
            continue
        if is_hype_only(sentence):
            continue
        snippet = sentence[:160]
        key = snippet.lower()
        if key in seen:
            continue
        seen.add(key)
        found.append(snippet)
        if len(found) >= limit:
            break
    return tuple(found)


def enrich_gumroad_products(
    signals: list[Signal],
    cap: int = GUMROAD_PRODUCT_PAGE_CAP,
) -> tuple[list[Signal], list[str]]:
    """
    GET each discover product page and attach only the pain/intent it really shows.

    A failed or empty product GET keeps the discover row untouched — never dropped,
    never given invented pain.
    """
    notes: list[str] = []
    enriched: list[Signal] = []
    fetched = 0
    with_clues = 0
    for index, signal in enumerate(signals):
        if index >= cap or not signal.url:
            enriched.append(signal)
            continue
        if not is_public_gumroad_url(signal.url):
            notes.append(f"gumroad product GET skipped (not gumroad https): {signal.url}")
            enriched.append(signal)
            continue
        status, body = http_get(signal.url)
        fetched += 1
        notes.append(f"gumroad product GET {signal.url} → {status}")
        if status != 200:
            enriched.append(signal)
            continue
        try:
            parsed = parse_gumroad_product(body)
        except Exception as exc:  # a weird page must not kill the run
            notes.append(f"gumroad product parse failed {signal.url}: {type(exc).__name__}")
            enriched.append(signal)
            continue
        extracted = parsed.get("text") or ""
        if not extracted:
            enriched.append(signal)
            continue
        pain = _pain_sentences(extracted) or _pain_from_text(extracted)
        buying = _buying_from_text(extracted)
        if pain or buying:
            with_clues += 1
        combined = f"{signal.text} — {extracted}".strip()
        enriched.append(
            replace(
                signal,
                text=combined[:SIGNAL_TEXT_CAP],
                pain_points=signal.pain_points + pain,
                buying_signals=signal.buying_signals + buying,
                relevance=0.75 if (pain or buying) else signal.relevance,
            )
        )
    if signals:
        notes.append(
            f"gumroad product pages: {fetched} fetched (cap {cap}), "
            f"{with_clues} with pain/intent"
        )
    return enriched, notes


def fetch_gumroad(topic: str) -> tuple[list[Signal], list[str]]:
    url = GUMROAD_DISCOVER.format(q=quote(topic))
    status, body = http_get(url)
    notes = [f"gumroad GET {url} → {status}"]
    if status != 200:
        return [], notes
    signals = parse_gumroad_discover(body)
    notes.append(f"gumroad parsed {len(signals)} products")
    signals, product_notes = enrich_gumroad_products(signals)
    notes.extend(product_notes)
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
