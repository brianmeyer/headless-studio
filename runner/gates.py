"""Silence unless all four Green gates pass. Otherwise the receipt is a miss."""

from __future__ import annotations

import re

from runner.clues import extract_clues
from runner.models import GateCheck, GateReport, Promise, Score, Signal
from runner.scorer import evidence_signals, sourced_signals

STOP_WORDS = {
    "the", "a", "an", "is", "are", "for", "to", "of", "and", "or",
    "in", "on", "at", "by", "with", "how", "what", "why", "when",
    "that", "this", "from", "into", "about", "helps", "with",
    "based", "scouted", "demand", "product", "digital",
}


def content_words(text: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z]{4,}", text.lower())
        if word not in STOP_WORDS
    }


def promise_matches_sources(
    promise: Promise,
    signals: list[Signal] | tuple[Signal, ...],
) -> tuple[bool, str]:
    """Gate 4: the promise still makes sense after reading the sources."""
    if not signals:
        return False, "no sources to read"

    # Gate 4 reads source text only — not attached pain_points metadata.
    corpus_text = " ".join(s.text for s in signals)
    corpus = content_words(corpus_text)

    promise_text = " ".join(
        [
            promise.title,
            promise.description,
            promise.audience,
            " ".join(promise.pain_addressed),
            " ".join(promise.bullets),
        ]
    )
    promised = content_words(promise_text)
    if not promised:
        return False, "promise has no content words"

    overlap = promised & corpus
    ratio = len(overlap) / len(promised)
    if len(overlap) < 2 or ratio < 0.25:
        return False, (
            f"promise does not match sources "
            f"(overlap {len(overlap)} words, {ratio:.0%})"
        )

    if promise.pain_addressed:
        pain_blob = corpus_text.lower()
        matched_pain = any(
            any(word in pain_blob for word in content_words(pain))
            for pain in promise.pain_addressed
        )
        if not matched_pain:
            return False, "promised pain is not in the sources"

    return True, f"{len(overlap)} promise words appear in sources"


def evaluate_gates(
    signals: list[Signal] | tuple[Signal, ...],
    promise: Promise,
    score: Score,
) -> GateReport:
    sourced = sourced_signals(signals)
    evidence = evidence_signals(signals)
    clues = extract_clues(evidence)
    # Gate 4 reads sourced text when any sourced rows exist.
    coherent, coherent_detail = promise_matches_sources(promise, sourced or list(signals))

    sourced_ok = len(sourced) >= 5
    clues_ok = len(clues) >= 3
    score_ok = (
        score.total > 60
        and score.confidence in {"medium", "high"}
        and len(score.source_urls) >= 1
    )

    return GateReport(
        checks=(
            GateCheck(
                name="sourced_signals",
                passed=sourced_ok,
                detail=f"{len(sourced)} sourced non-fixture signals (need ≥5)",
            ),
            GateCheck(
                name="pain_intent_clues",
                passed=clues_ok,
                detail=f"{len(clues)} pain/intent clues, hype excluded (need ≥3)",
            ),
            GateCheck(
                name="score_medium_sources",
                passed=score_ok,
                detail=(
                    f"score {score.total} ({score.confidence}), "
                    f"{len(score.source_urls)} source URLs (need >60, medium+, sources)"
                ),
            ),
            GateCheck(
                name="promise_matches_sources",
                passed=coherent,
                detail=coherent_detail,
            ),
        )
    )
