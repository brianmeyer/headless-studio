"""Write a local markdown + JSON receipt. Record hit/miss. Do not ping anyone."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from runner.models import RunResult

STILL_RED = (
    "first post",
    "listing",
    "dollar",
    "buyer conversation",
)

HOW_TO_RUN = (
    "cd /Users/brianmeyer/headless-studio && ENVIRONMENT=development python3 -m green"
)


def _signal_counts(result: RunResult) -> dict[str, int]:
    live = sum(1 for s in result.signals if not s.fixture)
    fixtures = sum(1 for s in result.signals if s.fixture)
    return {"live": live, "fixtures": fixtures, "total": len(result.signals)}


def receipt_payload(result: RunResult) -> dict:
    counts = _signal_counts(result)
    return {
        "verdict": result.verdict,
        "paper_win": result.verdict == "hit",
        "ping": False,
        "topic": result.topic,
        "environment": result.environment,
        "written": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "how_to_run": HOW_TO_RUN,
        "scout_notes": list(result.notes),
        "signal_counts": counts,
        "fixtures_count_as_sourced": False,
        "promise": {
            "text": result.promise.title,
            "description": result.promise.description,
            "audience": result.promise.audience,
            "product_type": result.promise.product_type,
        },
        "score": {
            "total": result.score.total,
            "demand": result.score.demand,
            "intent": result.score.intent,
            "competition": result.score.competition,
            "confidence": result.score.confidence,
            "source_urls": list(result.score.source_urls),
        },
        "gates": [
            {"name": c.name, "passed": c.passed, "detail": c.detail}
            for c in result.gates.checks
        ],
        "clues": list(result.clues),
        "still_red": list(STILL_RED),
    }


def render_receipt(result: RunResult) -> str:
    payload = receipt_payload(result)
    counts = payload["signal_counts"]
    gates_table = "\n".join(
        f"| {check.name} | {'pass' if check.passed else 'fail'} | {check.detail} |"
        for check in result.gates.checks
    )
    signal_lines = []
    for signal in result.signals:
        kind = "fixture" if signal.fixture else signal.source
        snippet = signal.text.replace("\n", " ")[:140]
        signal_lines.append(f"- [{kind}] {signal.id}: {snippet}")
    clues = "\n".join(f"- {clue}" for clue in result.clues) or "- (none)"
    sources = "\n".join(f"- {url}" for url in result.score.source_urls) or "- (none)"
    red = "\n".join(f"- {item}" for item in STILL_RED)
    notes = "\n".join(f"- {note}" for note in result.notes) or "- (none)"

    if result.verdict == "miss":
        headline = "miss"
        summary = (
            "Paper-win miss. Scouted one buyer-facing promise and stopped. "
            "No ping. Silence unless all four gates pass. No mock on miss."
        )
    else:
        headline = "hit"
        summary = (
            "Paper-win hit. One buyer-facing promise recorded. "
            "No ping. Nothing was posted, listed, or sold."
        )

    return f"""# Receipt

{headline}

{summary}

- **verdict:** {result.verdict}
- **paper_win:** {str(payload["paper_win"]).lower()}
- **ping:** no
- **topic:** {result.topic}
- **environment:** {result.environment}
- **written:** {payload["written"]}
- **how to run:** `{HOW_TO_RUN}`
- **live signals:** {counts["live"]}
- **fixture signals:** {counts["fixtures"]} (never sourced)

## Scout

{notes}

## Buyer-facing promise (draft only)

{result.promise.title}

{result.promise.description}

- **audience:** {result.promise.audience}
- **type:** {result.promise.product_type}

## Gates

| Gate | Result | Detail |
| --- | --- | --- |
{gates_table}

## Score

- **total:** {result.score.total}
- **demand:** {result.score.demand}
- **intent:** {result.score.intent}
- **competition:** {result.score.competition} (default penalty)
- **confidence:** {result.score.confidence}

## Pain / intent clues

{clues}

## Sources

{sources}

## Signals

{chr(10).join(signal_lines) if signal_lines else "- (none)"}

## Still Red

{red}
"""


def write_outputs(result: RunResult, receipt_path: Path) -> RunResult:
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = receipt_path.with_suffix(".json")
    result.json_path = json_path
    result.receipt_path = receipt_path
    receipt_path.write_text(render_receipt(result), encoding="utf-8")
    json_path.write_text(
        json.dumps(receipt_payload(result), indent=2) + "\n",
        encoding="utf-8",
    )
    return result
