"""Silence gates: miss unless all four Green conditions are true."""

from __future__ import annotations

from runner.draft import draft_promise
from runner.fixtures import fixture_signals, sourced_hit_signals
from runner.gates import evaluate_gates, promise_matches_sources
from runner.models import Promise, Score
from runner.scorer import score_promise


def test_fixture_path_is_a_miss():
    signals = fixture_signals()
    promise = draft_promise(signals, "chatgpt prompts for property managers")
    score = score_promise(signals, promise)
    report = evaluate_gates(signals, promise, score)
    assert not report.all_passed
    sourced = report.by_name("sourced_signals")
    assert sourced is not None
    assert sourced.passed is False


def test_canned_sourced_path_passes_all_four_gates():
    signals = sourced_hit_signals()
    promise = draft_promise(signals, "chatgpt prompts for property managers")
    score = score_promise(signals, promise)
    report = evaluate_gates(signals, promise, score)
    assert report.all_passed
    for check in report.checks:
        assert check.passed, check


def test_score_of_60_is_not_enough():
    signals = sourced_hit_signals()
    promise = draft_promise(signals, "chatgpt prompts for property managers")
    score = Score(
        total=60.0,
        demand=40,
        intent=25,
        competition=-5,
        confidence="medium",
        source_urls=tuple(s.url for s in signals),
    )
    report = evaluate_gates(signals, promise, score)
    score_gate = report.by_name("score_medium_sources")
    assert score_gate is not None
    assert score_gate.passed is False
    assert not report.all_passed


def test_incoherent_promise_fails_gate_four():
    signals = sourced_hit_signals()
    score = score_promise(signals)
    yoga = Promise(
        title="Sunrise Yoga Retreat Journal",
        description="A wellness journal for yoga retreats in Bali.",
        audience="yoga instructors",
        product_type="guide",
        pain_addressed=("need more namaste",),
        bullets=("sun salutations",),
        topic="yoga retreats",
    )
    ok, detail = promise_matches_sources(yoga, signals)
    assert ok is False
    report = evaluate_gates(signals, yoga, score)
    gate = report.by_name("promise_matches_sources")
    assert gate is not None
    assert gate.passed is False
    assert "overlap" in detail or "not" in detail


from runner.models import Signal


def _neutral_sourced(n: int = 5) -> list[Signal]:
    return [
        Signal(
            id=f"n-{i}",
            source="x",
            text="The weather is pleasant this afternoon in Cleveland.",
            url=f"https://x.com/example/status/{2000 + i}",
            fixture=False,
            pain_points=("pleasant weather notes",),
            buying_signals=("afternoon update",),
            engagement=80,
            relevance=0.9,
        )
        for i in range(n)
    ]


def test_url_less_non_fixture_is_not_sourced():
    signals = [
        Signal(
            id=f"u-{i}",
            source="x",
            text="Tired of rewriting listing copy from scratch every week.",
            url="",
            fixture=False,
            pain_points=("rewriting listing copy from scratch",),
            engagement=50,
            relevance=0.8,
        )
        for i in range(5)
    ]
    promise = draft_promise(signals, "chatgpt prompts for property managers")
    score = score_promise(signals, promise)
    report = evaluate_gates(signals, promise, score)
    sourced = report.by_name("sourced_signals")
    assert sourced is not None
    assert sourced.passed is False
    assert not report.all_passed


def test_neutral_signals_cannot_pass_silence_gates():
    signals = _neutral_sourced()
    promise = draft_promise(signals, "chatgpt prompts for property managers")
    score = score_promise(signals, promise)
    report = evaluate_gates(signals, promise, score)
    clues = report.by_name("pain_intent_clues")
    assert clues is not None
    assert clues.passed is False
    assert not report.all_passed


def test_fewer_than_three_clues_is_a_miss():
    signals = [
        Signal(
            id="one-pain",
            source="x",
            text="Tired of rewriting listing copy from scratch every week.",
            url="https://x.com/example/status/3001",
            fixture=False,
            pain_points=("rewriting listing copy from scratch",),
            engagement=50,
            relevance=0.8,
        ),
        Signal(
            id="weather-1",
            source="x",
            text="Nice morning for a walk around the block.",
            url="https://x.com/example/status/3002",
            fixture=False,
            engagement=10,
            relevance=0.2,
        ),
        Signal(
            id="weather-2",
            source="reddit",
            text="The coffee shop downtown opened early today.",
            url="https://reddit.com/r/example/comments/eee555",
            fixture=False,
            engagement=10,
            relevance=0.2,
        ),
        Signal(
            id="weather-3",
            source="x",
            text="Traffic on main street looks lighter than usual.",
            url="https://x.com/example/status/3003",
            fixture=False,
            engagement=10,
            relevance=0.2,
        ),
        Signal(
            id="weather-4",
            source="reddit",
            text="Someone posted a photo of a sunset near the lake.",
            url="https://reddit.com/r/example/comments/fff666",
            fixture=False,
            engagement=10,
            relevance=0.2,
        ),
    ]
    promise = draft_promise(signals, "chatgpt prompts for property managers")
    score = score_promise(signals, promise)
    report = evaluate_gates(signals, promise, score)
    clues = report.by_name("pain_intent_clues")
    assert clues is not None
    assert clues.passed is False
    assert not report.all_passed


def test_mixed_fixtures_cannot_authorize_a_hit():
    """Fixture pain/intent must not pass gates when sourced rows are weather-only."""
    signals = _neutral_sourced() + fixture_signals()
    promise = draft_promise(signals, "chatgpt prompts for property managers")
    score = score_promise(signals, promise)
    report = evaluate_gates(signals, promise, score)
    clues = report.by_name("pain_intent_clues")
    score_gate = report.by_name("score_medium_sources")
    assert clues is not None and clues.passed is False
    assert score_gate is not None and score_gate.passed is False
    assert not report.all_passed
    assert score.confidence == "low" or score.total <= 60
