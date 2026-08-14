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
