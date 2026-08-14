"""One-shot pipeline: scout → one promise → score → gates → receipt → exit."""

from __future__ import annotations

from pathlib import Path

from runner.clues import extract_clues
from runner.draft import draft_promise
from runner.fixtures import DEFAULT_TOPIC
from runner.gates import evaluate_gates
from runner.models import RunResult, Signal
from runner.receipt import write_outputs
from runner.scorer import score_promise, sourced_signals
from runner.scout import environment_name, scout


def run(
    topic: str = DEFAULT_TOPIC,
    out_path: str | Path | None = None,
    signals: list[Signal] | None = None,
    use_fixtures: bool = False,
) -> RunResult:
    """
    Scout (read-only) → draft one buyer-facing promise → score → paper-win gates → receipt.

    Pass `signals` to skip scout (tests / canned sourced objects).
    Keys missing: public HTTP, then fixtures. Fixture rows cannot pass gate 1.
    """
    env = environment_name()
    notes: list[str] = []
    if signals is not None:
        observed = tuple(signals)
        notes.append("scout skipped: signals provided")
    else:
        outcome = scout(topic, use_fixtures=use_fixtures)
        observed = tuple(outcome.signals)
        notes.extend(outcome.notes)

    promise = draft_promise(observed, topic)
    score = score_promise(observed, promise)
    gates = evaluate_gates(observed, promise, score)
    clues = tuple(extract_clues(sourced_signals(observed)))
    verdict = "hit" if gates.all_passed else "miss"

    receipt_path = Path(out_path) if out_path else Path("receipts") / "latest.md"
    result = RunResult(
        verdict=verdict,
        topic=topic,
        environment=env,
        promise=promise,
        score=score,
        gates=gates,
        signals=observed,
        clues=clues,
        receipt_path=receipt_path,
        notes=notes,
    )
    return write_outputs(result, receipt_path)
