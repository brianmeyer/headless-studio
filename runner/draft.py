"""Draft exactly one product promise from scouted signals."""

from __future__ import annotations

import re

from runner.clues import extract_clues, is_hype_only
from runner.fixtures import DEFAULT_TOPIC
from runner.models import Promise, Signal

PRODUCT_TYPE_KEYWORDS = {
    "prompt_pack": ("prompt", "chatgpt", "gpt", "claude", "llm"),
    "template_pack": ("template", "spreadsheet", "notion", "worksheet"),
    "checklist": ("checklist", "framework", "sop", "routine"),
    "guide": ("guide", "tutorial", "how to", "course"),
    "roadmap": ("roadmap", "plan", "strategy"),
}

TYPE_LABELS = {
    "prompt_pack": "Prompt Pack",
    "template_pack": "Template Bundle",
    "checklist": "Checklist",
    "guide": "Guide",
    "roadmap": "Roadmap",
}

STOP_WORDS = {
    "the", "a", "an", "is", "are", "for", "to", "of", "and", "or",
    "in", "on", "at", "by", "with", "how", "what", "why", "when",
    "i", "you", "my", "your", "this", "that", "it", "do", "does",
    "from", "into", "about", "just", "have", "has",
}


def infer_product_type(signals: list[Signal] | tuple[Signal, ...], topic: str) -> str:
    scores = {key: 0 for key in PRODUCT_TYPE_KEYWORDS}
    blob = " ".join(s.text for s in signals) + " " + topic
    lowered = blob.lower()
    for product_type, keywords in PRODUCT_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lowered:
                scores[product_type] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "guide"


def infer_audience(signals: list[Signal] | tuple[Signal, ...], topic: str) -> str:
    blob = f"{topic} " + " ".join(s.text for s in signals)
    lowered = blob.lower()
    if "property manager" in lowered or "tenant" in lowered or "listing" in lowered:
        return "property managers"
    if "real estate" in lowered or "agent" in lowered:
        return "real estate agents"
    if "teacher" in lowered or "lesson" in lowered:
        return "teachers"
    if "freelance" in lowered:
        return "freelancers"
    return "non-technical professionals"


_TITLE_MAP = {"chatgpt": "ChatGPT", "gpt": "GPT", "ai": "AI"}


def _topic_title(topic: str) -> str:
    words = [w for w in re.findall(r"[A-Za-z0-9]+", topic) if w.lower() not in STOP_WORDS]
    if not words:
        return "Digital Product"
    pretty = []
    for word in words[:8]:
        pretty.append(_TITLE_MAP.get(word.lower(), word.capitalize() if not word.isupper() else word))
    return " ".join(pretty)


def draft_promise(
    signals: list[Signal] | tuple[Signal, ...],
    topic: str = DEFAULT_TOPIC,
) -> Promise:
    """Turn scouted signals into one promise. Does not publish anything."""
    clues = extract_clues(signals)
    pains: list[str] = []
    seen: set[str] = set()
    for signal in signals:
        for pain in signal.pain_points:
            if is_hype_only(pain):
                continue
            key = pain.lower().strip()
            if key and key not in seen:
                seen.add(key)
                pains.append(pain)
    if not pains:
        pains = clues[:3]

    product_type = infer_product_type(signals, topic)
    audience = infer_audience(signals, topic)
    title = f"{_topic_title(topic)} {TYPE_LABELS[product_type]}"
    if pains:
        description = f"Helps {audience} with: {', '.join(pains[:3])}."
    else:
        description = f"A {product_type.replace('_', ' ')} for {audience} based on scouted demand."

    bullets = tuple(pains[:4] or clues[:4] or (f"Practical {product_type.replace('_', ' ')} for {audience}",))
    return Promise(
        title=title,
        description=description,
        audience=audience,
        product_type=product_type,
        pain_addressed=tuple(pains[:5]),
        bullets=bullets,
        topic=topic,
    )
