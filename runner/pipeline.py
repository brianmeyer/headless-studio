"""One-shot pipeline: scout → one promise → score → gates → receipt → exit."""

from __future__ import annotations

from pathlib import Path

from runner.clues import extract_clues
from runner.draft import draft_promise
from runner.fixtures import DEFAULT_TOPIC
from runner.gates import evaluate_gates
from runner.models import RunResult, Signal
from runner.receipt import write_outputs
from runner.scorer import score_promise
from runner.scout import environment_name, scout


def run(
    topic: str = DEFAULT_TOPIC,
    out_path: str | Path | None = None,
    signals: list[Signal] | None = None,
) -> RunResult:
    """
    Scout (read-only) → draft one buyer-facing promise → score → paper-win gates → receipt.

    Pass `signals` to skip scout (tests / canned sourced objects).
    Default development scout is fixtures only. Fixture rows cannot pass gate 1.
    """
    env = environment_name()
    observed = tuple(signals if signals is not None else scout(topic))
    promise = draft_promise(observed, topic)
    score = score_promise(observed, promise)
    gates = evaluate_gates(observed, promise, score)
    clues = tuple(extract_clues(observed))
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
    )
    return write_outputs(result, receipt_path)
