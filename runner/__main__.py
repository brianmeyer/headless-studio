"""python -m runner — one scout, one promise, one receipt, then exit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from runner.pipeline import run
from runner.scout_input import SCOUT_TOPIC_FILE


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "One-shot read-only scout → at most one draft promise → score → "
            "local markdown/JSON receipt. Writes miss and stops unless all "
            "four paper-win gates pass. Tavily Reddit if a key resolves, public "
            "HTTP, else fixtures. Fixtures never count as sourced. Every packet "
            "is NOT APPROVED. No ping."
        )
    )
    parser.add_argument(
        "--topic",
        default=None,
        help=f"Topic to scout (default: the scout input topic in {SCOUT_TOPIC_FILE.name})",
    )
    parser.add_argument(
        "--out",
        default="receipts/latest.md",
        help="Markdown receipt path (default: receipts/latest.md)",
    )
    parser.add_argument(
        "--fixtures",
        action="store_true",
        help="Skip public HTTP and use fixture rows (still a miss)",
    )
    args = parser.parse_args(argv)

    result = run(
        topic=args.topic,
        out_path=Path(args.out),
        use_fixtures=args.fixtures,
    )
    print(result.verdict)
    print(result.receipt_path)
    if result.json_path:
        print(result.json_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
