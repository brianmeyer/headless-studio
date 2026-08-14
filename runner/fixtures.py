"""Canned signals. Fixture rows never count as sourced."""

from __future__ import annotations

from runner.models import Signal

DEFAULT_TOPIC = "chatgpt prompts for property managers"


def fixture_signals(topic: str = DEFAULT_TOPIC) -> list[Signal]:
    """Development stand-ins when live APIs are absent. Marked fixture=True."""
    return [
        Signal(
            id="fix-1",
            source="fixture",
            text=(
                f"Looking for {topic} that don't sound like a robot. "
                "Tired of rewriting listing copy from scratch every week."
            ),
            url="https://example.invalid/fixture/1",
            created_at="2026-01-01T00:00:00Z",
            fixture=True,
            pain_points=("rewriting listing copy from scratch",),
            buying_signals=("looking for prompts",),
            engagement=12,
            relevance=0.6,
            author="fixture-user-1",
        ),
        Signal(
            id="fix-2",
            source="fixture",
            text=(
                "Property managers: how do I keep tenant notices consistent? "
                "Manual copy-paste is wasting hours."
            ),
            url="https://example.invalid/fixture/2",
            created_at="2026-01-02T00:00:00Z",
            fixture=True,
            pain_points=("manual copy-paste wasting hours",),
            questions=("how do I keep tenant notices consistent?",),
            engagement=8,
            relevance=0.55,
            author="fixture-user-2",
        ),
        Signal(
            id="fix-3",
            source="fixture",
            text="This prompt pack is a game changer and revolutionary 10x viral must-have.",
            url="https://example.invalid/fixture/3",
            created_at="2026-01-03T00:00:00Z",
            fixture=True,
            pain_points=("game changer revolutionary pack",),
            buying_signals=("must-have viral prompts",),
            engagement=40,
            relevance=0.2,
            author="fixture-hype",
        ),
        Signal(
            id="fix-4",
            source="fixture",
            text=f"Anyone know a decent starting point for {topic}?",
            url="https://example.invalid/fixture/4",
            created_at="2026-01-04T00:00:00Z",
            fixture=True,
            questions=("anyone know a decent starting point?",),
            engagement=3,
            relevance=0.4,
            author="fixture-user-4",
        ),
    ]


def sourced_hit_signals() -> list[Signal]:
    """Canned *sourced* (non-fixture) signals used by tests for a passing path."""
    return [
        Signal(
            id="x-1",
            source="x",
            text=(
                "I keep wasting hours rewriting listing descriptions. "
                "Need a prompt pack that actually works for property managers."
            ),
            url="https://x.com/example/status/1001",
            created_at="2026-02-01T12:00:00Z",
            fixture=False,
            pain_points=("wasting hours rewriting listing descriptions",),
            buying_signals=("need a prompt pack",),
            engagement=84,
            relevance=0.86,
            author="pm_ops",
        ),
        Signal(
            id="x-2",
            source="x",
            text=(
                "Tenant notices are a mess. How do I keep the tone consistent "
                "without starting from scratch every time?"
            ),
            url="https://x.com/example/status/1002",
            created_at="2026-02-01T13:00:00Z",
            fixture=False,
            pain_points=("tenant notices inconsistent", "starting from scratch"),
            questions=("how do I keep the tone consistent?",),
            engagement=61,
            relevance=0.81,
            author="lease_desk",
        ),
        Signal(
            id="rd-1",
            source="reddit",
            text=(
                "Looking for ChatGPT prompts for renewal letters. "
                "Current ones don't work and residents get confused."
            ),
            url="https://reddit.com/r/PropertyManagement/comments/aaa111",
            created_at="2026-02-02T09:00:00Z",
            fixture=False,
            pain_points=("renewal letters don't work",),
            buying_signals=("looking for ChatGPT prompts",),
            engagement=140,
            relevance=0.9,
            author="u/on_site_mgr",
        ),
        Signal(
            id="rd-2",
            source="reddit",
            text=(
                "Frustrated with showing follow-ups. Manual copy-paste takes hours "
                "and I still miss units."
            ),
            url="https://reddit.com/r/realestate/comments/bbb222",
            created_at="2026-02-02T10:00:00Z",
            fixture=False,
            pain_points=("manual copy-paste takes hours", "miss units on follow-up"),
            buying_signals=("would pay for a checklist plus prompts",),
            engagement=97,
            relevance=0.84,
            author="u/showing_coord",
        ),
        Signal(
            id="x-3",
            source="x",
            text=(
                "Wish there was a prompt pack for maintenance updates that "
                "doesn't sound like a robot. Tired of rewriting from scratch."
            ),
            url="https://x.com/example/status/1003",
            created_at="2026-02-03T08:00:00Z",
            fixture=False,
            pain_points=("maintenance updates sound like a robot",),
            buying_signals=("wish there was a prompt pack",),
            engagement=73,
            relevance=0.8,
            author="maint_lead",
        ),
        Signal(
            id="rd-3",
            source="reddit",
            text=(
                "Anyone know a template + prompt combo for delinquency notices? "
                "Need help staying firm without sounding cruel."
            ),
            url="https://reddit.com/r/PropertyManagement/comments/ccc333",
            created_at="2026-02-03T11:00:00Z",
            fixture=False,
            pain_points=("delinquency tone too harsh or too soft",),
            questions=("anyone know a template plus prompt combo?",),
            buying_signals=("need help staying firm",),
            engagement=118,
            relevance=0.88,
            author="u/collections_pm",
        ),
        Signal(
            id="x-4",
            source="x",
            text=(
                "Can't find prompts that mention actual lease clauses. "
                "Generic ChatGPT output is useless for property managers."
            ),
            url="https://x.com/example/status/1004",
            created_at="2026-02-04T15:00:00Z",
            fixture=False,
            pain_points=("can't find prompts that mention lease clauses",),
            buying_signals=("looking for property-manager-specific prompts",),
            engagement=55,
            relevance=0.83,
            author="legalish_pm",
        ),
        Signal(
            id="rd-4",
            source="reddit",
            text=(
                "Overwhelmed writing owner reports every Friday. "
                "Would pay for a guide with prompts I can paste into ChatGPT."
            ),
            url="https://reddit.com/r/smallbusiness/comments/ddd444",
            created_at="2026-02-04T16:00:00Z",
            fixture=False,
            pain_points=("overwhelmed writing owner reports",),
            buying_signals=("would pay for a guide with prompts",),
            engagement=166,
            relevance=0.87,
            author="u/owner_reporter",
        ),
    ]
