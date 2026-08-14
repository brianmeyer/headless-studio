"""python -m green — Vera-locked one-shot Green runner."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from runner.__main__ import main as runner_main


def _default_out() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return str(Path("green") / "out" / stamp / "RECEIPT.md")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    # --fixtures is accepted (dev default already fixtures-only). Strip so runner argparse stays clean
    # after runner gains the flag; still pass through.
    if "--out" not in args:
        args = ["--out", _default_out(), *args]
    return runner_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
