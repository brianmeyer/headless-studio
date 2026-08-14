"""One-shot pipeline: scout → at most one draft promise → score → gates → receipt → exit."""

from __future__ import annotations

from pathlib import Path

from runner.clues import extract_clues
from runner.draft import draft_promise
from runner.gates import evaluate_gates
from runner.models import Promise, RunResult, Signal
from runner.receipt import PACKET_APPROVAL, write_outputs
from runner.scorer import score_promise, sourced_signals
from runner.scout import environment_name, scout
from runner.scout_input import ScoutInput, load_scout_input


def empty_promise(topic: str) -> Promise:
    """No sourced rows, no promise. The packet stays empty rather than invented."""
    return Promise(
        title="",
        description="",
        audience="",
        product_type="",
        pain_addressed=(),
        bullets=(),
        topic=topic,
    )


def run(
    topic: str | None = None,
    out_path: str | Path | None = None,
    signals: list[Signal] | None = None,
    use_fixtures: bool = False,
) -> RunResult:
    """
    Scout (read-only) → draft at most one promise from **sourced** rows → score →
    paper-win gates → receipt.

    The topic comes from the scout input file unless one is passed. Nothing is
    drafted from fixtures: with no sourced rows the packet is empty and the
    verdict is a miss. Every packet is NOT APPROVED, hit or miss.

    Pass `signals` to skip the scout (tests / canned sourced objects).
    """
    env = environment_name()
    spec: ScoutInput = load_scout_input()
    if topic is None or not topic.strip():
        topic = spec.topic
        query = spec.search_text
    else:
        query = topic

    notes: list[str] = []
    if spec.topic:
        notes.append(f"scout input: {spec.topic} (scout target only — not a SKU)")
    if spec.out_of_scope:
        notes.append("out of scope: " + ", ".join(spec.out_of_scope))

    if signals is not None:
        observed = tuple(signals)
        notes.append("scout skipped: signals provided")
    else:
        outcome = scout(query, use_fixtures=use_fixtures)
        observed = tuple(outcome.signals)
        notes.extend(outcome.notes)

    sourced = sourced_signals(observed)
    if sourced:
        promise = draft_promise(sourced, topic)
        notes.append(f"packet: {PACKET_APPROVAL} draft from {len(sourced)} sourced rows")
    else:
        promise = empty_promise(topic)
        notes.append(f"packet: {PACKET_APPROVAL}, empty — no sourced rows, nothing drafted")

    score = score_promise(observed, promise)
    gates = evaluate_gates(observed, promise, score)
    clues = tuple(extract_clues(sourced))
    verdict = "hit" if gates.all_passed else "miss"
    notes.append(f"{PACKET_APPROVAL}: nothing published, listed, or posted")

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
        query=query,
        scout_input=spec,
    )
    return write_outputs(result, receipt_path)
