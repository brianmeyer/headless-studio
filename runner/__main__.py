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
            "four paper-win gates pass. No secrets in development. No ping."
        )
    )
    parser.add_argument("--topic", default=DEFAULT_TOPIC, help="Topic to scout")
    parser.add_argument(
        "--out",
        default="receipts/latest.md",
        help="Markdown receipt path (default: receipts/latest.md)",
    )
    args = parser.parse_args(argv)

    result = run(topic=args.topic, out_path=Path(args.out))
    print(result.verdict)
    print(result.receipt_path)
    if result.json_path:
        print(result.json_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
