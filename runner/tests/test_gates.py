"""Silence gates: miss unless all four Green conditions are true."""

from __future__ import annotations

from runner.draft import draft_promise
from runner.fixtures import fixture_signals, sourced_hit_signals
from runner.gates import evaluate_gates, promise_matches_sources
from runner.models import Promise, Score, Signal
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


def test_fixture_clues_do_not_count_in_mixed_run():
    """Fixtures must not inflate gate 2 when sourced rows have no pain/intent."""
    signals = fixture_signals() + _neutral_sourced()
    promise = draft_promise(signals, "chatgpt prompts for property managers")
    score = score_promise(signals, promise)
    report = evaluate_gates(signals, promise, score)
    clues = report.by_name("pain_intent_clues")
    assert clues is not None
    assert clues.passed is False
    assert not report.all_passed


def test_generic_overlap_without_pain_fails_gate_four():
    """Audience/product words without the claimed pain must not pass gate 4."""
    signals = [
        Signal(
            id=f"g-{i}",
            source="x",
            text="Office hours directory: property managers catalogue one prompt pack.",
            url=f"https://x.com/example/status/{4000 + i}",
            fixture=False,
            engagement=40,
            relevance=0.7,
        )
        for i in range(5)
    ]
    promise = Promise(
        title="For property managers: stop wasting hours on listing copy",
        description="A prompt pack for property managers.",
        audience="property managers",
        product_type="prompt pack",
        pain_addressed=("wasting hours",),
        bullets=("prompt pack",),
        topic="chatgpt prompts for property managers",
    )
    ok, detail = promise_matches_sources(promise, signals)
    assert ok is False
    assert "pain" in detail or "not" in detail
