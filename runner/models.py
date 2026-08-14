"""Dataclasses for the one-shot runner. No third-party deps."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Signal:
    """One read-only scout observation."""

    id: str
    source: str
    text: str
    url: str = ""
    created_at: str = ""
    fixture: bool = False
    pain_points: tuple[str, ...] = ()
    buying_signals: tuple[str, ...] = ()
    questions: tuple[str, ...] = ()
    engagement: int = 0
    relevance: float = 0.0
    author: str = ""


@dataclass(frozen=True)
class Promise:
    """A single drafted product promise."""

    title: str
    description: str
    audience: str
    product_type: str
    pain_addressed: tuple[str, ...] = ()
    bullets: tuple[str, ...] = ()
    topic: str = ""


@dataclass(frozen=True)
class Score:
    """Demand + intent + competition, with confidence and source URLs."""

    total: float
    demand: float
    intent: float
    competition: float
    confidence: str
    source_urls: tuple[str, ...] = ()


@dataclass(frozen=True)
class GateCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class GateReport:
    checks: tuple[GateCheck, ...]

    @property
    def all_passed(self) -> bool:
        return bool(self.checks) and all(c.passed for c in self.checks)

    def by_name(self, name: str) -> GateCheck | None:
        for check in self.checks:
            if check.name == name:
                return check
        return None


@dataclass
class RunResult:
    verdict: str
    topic: str
    environment: str
    promise: Promise
    score: Score
    gates: GateReport
    signals: tuple[Signal, ...]
    clues: tuple[str, ...]
    receipt_path: Path
    mock_path: Path | None = None
    notes: list[str] = field(default_factory=list)
