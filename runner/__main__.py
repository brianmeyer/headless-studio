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
            "One-shot read-only scout → one product promise → score → "
            "local receipt. Writes miss and stops unless all four gates pass. "
            "No secrets required in development."
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
        help="Force fixture scout (development default when APIs/keys are missing).",
    )
    args = parser.parse_args(argv)
    # --fixtures is the only scout this slice has; flag documents the contract.
    _ = args.fixtures

    result = run(topic=args.topic, out_path=Path(args.out))
    print(result.verdict)
    print(result.receipt_path)
    if result.mock_path:
        print(result.mock_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
