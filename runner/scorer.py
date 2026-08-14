"""Score one promise from scouted signals. Competition is a default penalty; this slice does not scrape to change it."""

from __future__ import annotations

from runner.clues import extract_clues, is_hype_only
from runner.models import Promise, Score, Signal


def _has_source_url(signal: Signal) -> bool:
    url = (signal.url or "").strip()
    return url.startswith("http://") or url.startswith("https://")


def sourced_signals(signals: list[Signal] | tuple[Signal, ...]) -> list[Signal]:
    """Non-fixture rows with a source URL. Fixture or URL-less rows are not sourced."""
    return [s for s in signals if (not s.fixture) and _has_source_url(s)]


def score_promise(
    signals: list[Signal] | tuple[Signal, ...],
    promise: Promise | None = None,
) -> Score:
    """
    Demand (0-50) + intent (0-40) + competition (-20 to 0).

    Competition stays at the default medium penalty. This slice does not
    scrape Gumroad. Confidence requires sourced (non-fixture) signals.
    """
    _ = promise
    sourced = sourced_signals(signals)
    if not sourced:
        return Score(
            total=0,
            demand=0,
            intent=0,
            competition=0,
            confidence="low",
            source_urls=(),
        )

    demand = _demand(sourced)
    intent = _intent(sourced)
    competition = -5.0
    total = max(0.0, min(100.0, demand + intent + competition))

    source_urls = tuple(s.url for s in sourced if s.url)
    if len(sourced) >= 10 and total >= 70:
        confidence = "high"
    elif len(sourced) >= 5 and total >= 50:
        confidence = "medium"
    else:
        confidence = "low"

    return Score(
        total=round(total, 1),
        demand=round(demand, 1),
        intent=round(intent, 1),
        competition=round(competition, 1),
        confidence=confidence,
        source_urls=source_urls,
    )


def _demand(signals: list[Signal] | tuple[Signal, ...]) -> float:
    score = 0.0
    count = len(signals)
    if count >= 12:
        score += 28
    elif count >= 8:
        score += 22
    elif count >= 5:
        score += 16
    elif count >= 2:
        score += 8

    sources = {s.source for s in signals if s.source}
    if len(sources) >= 3:
        score += 12
    elif len(sources) >= 2:
        score += 8

    engagement = sum(s.engagement for s in signals)
    if engagement >= 400:
        score += 10
    elif engagement >= 150:
        score += 7
    elif engagement >= 40:
        score += 4

    avg_rel = sum(s.relevance for s in signals) / len(signals)
    score += avg_rel * 8
    return min(score, 50)


def _intent(signals: list[Signal] | tuple[Signal, ...]) -> float:
    score = 0.0
    clues = extract_clues(signals)
    if len(clues) >= 8:
        score += 24
    elif len(clues) >= 5:
        score += 18
    elif len(clues) >= 3:
        score += 12
    elif clues:
        score += 5

    buying = []
    seen: set[str] = set()
    for signal in signals:
        for item in signal.buying_signals:
            if is_hype_only(item):
                continue
            key = item.lower().strip()
            if key and key not in seen:
                seen.add(key)
                buying.append(item)
    if len(buying) >= 5:
        score += 12
    elif len(buying) >= 2:
        score += 8
    elif buying:
        score += 4

    return min(score, 40)
