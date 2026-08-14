"""Scorer and draft path on canned objects. No live APIs."""

from __future__ import annotations

from runner.clues import extract_clues, is_hype_only
from runner.draft import draft_promise
from runner.fixtures import fixture_signals, sourced_hit_signals
from runner.models import Promise, Score, Signal
from runner.scorer import score_promise


def test_draft_one_promise_from_canned_sourced_signals():
    signals = sourced_hit_signals()
    promise = draft_promise(signals, topic="chatgpt prompts for property managers")
    assert promise.title
    assert promise.product_type == "prompt_pack"
    assert promise.audience == "property managers"
    assert promise.pain_addressed
    assert "property" in promise.description.lower() or "listing" in promise.description.lower() or promise.pain_addressed


def test_score_canned_sourced_signals_is_medium_over_60():
    signals = sourced_hit_signals()
    promise = draft_promise(signals, "chatgpt prompts for property managers")
    score = score_promise(signals, promise)
    assert score.total > 60
    assert score.confidence in {"medium", "high"}
    assert len(score.source_urls) >= 5
    assert all("example.invalid" not in url for url in score.source_urls)


def test_fixture_signals_cannot_earn_medium_confidence():
    signals = fixture_signals()
    promise = draft_promise(signals, "chatgpt prompts for property managers")
    score = score_promise(signals, promise)
    assert score.confidence == "low"
    assert score.source_urls == ()


def test_hype_only_phrases_are_not_clues():
    assert is_hype_only("This is a revolutionary game changer 10x viral must-have")
    hype = Signal(
        id="hype",
        source="x",
        text="Amazing revolutionary 10x viral game changer pack.",
        url="https://x.com/example/status/9",
        fixture=False,
        pain_points=("revolutionary game changer",),
        buying_signals=("must-have viral prompts",),
    )
    assert extract_clues([hype]) == []


def test_empty_signals_score_zero():
    score = score_promise([])
    assert score == Score(
        total=0,
        demand=0,
        intent=0,
        competition=0,
        confidence="low",
        source_urls=(),
    )


def test_draft_uses_topic_when_signals_are_thin():
    promise = draft_promise([], topic="notion templates for coaches")
    assert isinstance(promise, Promise)
    assert "Notion" in promise.title or "Coaches" in promise.title
    assert promise.product_type in {"template_pack", "guide"}
