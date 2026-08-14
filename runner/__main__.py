"""python -m runner — one scout, one promise, one receipt, then exit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from runner.fixtures import DEFAULT_TOPIC
from runner.pipeline import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "One-shot read-only scout → one buyer-facing promise → score → "
            "local markdown/JSON receipt. Writes miss and stops unless all "
            "four paper-win gates pass. Public HTTP if present, else fixtures. "
            "Fixtures never count as sourced. No ping."
        )
    )
    parser.add_argument("--topic", default=DEFAULT_TOPIC, help="Topic to scout")
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
