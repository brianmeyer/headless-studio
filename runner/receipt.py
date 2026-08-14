"""Write a local markdown receipt and, on hit only, a static mock page."""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from pathlib import Path

from runner.models import RunResult


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60] or "promise"


def render_receipt(result: RunResult) -> str:
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
    mock_line = (
        f"Written to `{result.mock_path}` (local only, not published)."
        if result.mock_path
        else "Not written. Misses do not get a mock."
    )

    if result.verdict == "miss":
        headline = "miss"
        summary = (
            "Scouted one product promise and stopped. "
            "Silence unless all four gates pass."
        )
    else:
        headline = "hit"
        summary = "All four gates passed. Local static mock written. Nothing was published."

    return f"""# Receipt

{headline}

{summary}

- **verdict:** {result.verdict}
- **topic:** {result.topic}
- **environment:** {result.environment}
- **written:** {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}

## Gates

| Gate | Result | Detail |
| --- | --- | --- |
{gates_table}

## Promise (draft only)

- **title:** {result.promise.title}
- **type:** {result.promise.product_type}
- **audience:** {result.promise.audience}
- **description:** {result.promise.description}

## Score

- **total:** {result.score.total}
- **demand:** {result.score.demand}
- **intent:** {result.score.intent}
- **competition:** {result.score.competition} (default; no Gumroad HTTP)
- **confidence:** {result.score.confidence}

## Pain / intent clues

{clues}

## Sources

{sources}

## Signals

{chr(10).join(signal_lines) if signal_lines else "- (none)"}

## Static mock

{mock_line}
"""


def write_static_mock(result: RunResult, mock_dir: Path) -> Path:
    mock_dir.mkdir(parents=True, exist_ok=True)
    path = mock_dir / "index.html"
    bullets = "\n".join(
        f"        <li>{html.escape(bullet)}</li>" for bullet in result.promise.bullets
    )
    path.write_text(
        f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(result.promise.title)} — local mock</title>
  <style>
    body {{ font-family: sans-serif; max-width: 40rem; margin: 2rem auto; color: #111; }}
    .banner {{ background: #111; color: #fff; padding: 0.4rem 0.7rem; font-size: 0.8rem; }}
    h1 {{ margin-top: 1.5rem; }}
  </style>
</head>
<body>
  <p class="banner">LOCAL STATIC MOCK — not listed, not deployed, not for sale</p>
  <h1>{html.escape(result.promise.title)}</h1>
  <p>{html.escape(result.promise.description)}</p>
  <p>For {html.escape(result.promise.audience)}.</p>
  <ul>
{bullets}
  </ul>
  <p>Score {result.score.total} ({result.score.confidence}). Receipt: {html.escape(str(result.receipt_path))}.</p>
</body>
</html>
""",
        encoding="utf-8",
    )
    return path


def write_outputs(result: RunResult, receipt_path: Path) -> RunResult:
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    if result.verdict == "hit":
        mock_dir = receipt_path.parent / "mocks" / _slug(result.promise.title)
        result.mock_path = write_static_mock(result, mock_dir)
    else:
        result.mock_path = None
    receipt_path.write_text(render_receipt(result), encoding="utf-8")
    result.receipt_path = receipt_path
    return result
