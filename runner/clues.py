"""Pain/intent clues vs hype. Hype never counts toward the silence gates."""

from __future__ import annotations

import re

from runner.models import Signal

HYPE_PHRASES = (
    "game changer",
    "game-changer",
    "revolutionary",
    "amazing",
    "best ever",
    "viral",
    "passive income",
    "10x",
    "crushing it",
    "insane",
    "unbelievable",
    "must have",
    "must-have",
    "holy grail",
    "life changing",
    "life-changing",
    "next level",
    "next-level",
    "guaranteed",
    "secret weapon",
)

PAIN_INTENT_PATTERNS = (
    r"\bcan'?t\b",
    r"\bcannot\b",
    r"\bfrustrat",
    r"need help",
    r"looking for",
    r"how do i",
    r"wish there (was|were)",
    r"\bstruggl",
    r"wasting",
    r"doesn'?t work",
    r"\bbroken\b",
    r"overwhelm",
    r"too expensive",
    r"no time",
    r"\bmanual\b",
    r"copy.?paste",
    r"from scratch",
    r"where can i find",
    r"anyone (have|know)",
    r"tired of",
    r"sick of",
    r"takes (hours|forever)",
    r"starting over",
    r"need a (prompt|template|guide|checklist)",
    r"pay for",
    r"would pay",
    r"willing to pay",
)


def has_pain_intent(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in PAIN_INTENT_PATTERNS)


def is_hype_only(text: str) -> bool:
    lowered = text.lower()
    has_hype = any(phrase in lowered for phrase in HYPE_PHRASES)
    return has_hype and not has_pain_intent(lowered)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_clues(signals: list[Signal] | tuple[Signal, ...]) -> list[str]:
    """Unique pain/intent clues. Hype-only phrases are dropped."""
    clues: list[str] = []
    seen: set[str] = set()

    def add(raw: str) -> None:
        text = _normalize(raw)
        if len(text) < 8:
            return
        if is_hype_only(text):
            return
        if not has_pain_intent(text):
            return
        key = text.lower()
        if key in seen:
            return
        seen.add(key)
        clues.append(text)

    for signal in signals:
        if signal.fixture:
            continue
        for item in (*signal.pain_points, *signal.buying_signals, *signal.questions):
            add(item)
        if has_pain_intent(signal.text):
            add(signal.text[:160])

    return clues
