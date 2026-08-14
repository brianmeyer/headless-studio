"""python -m green — Vera-locked one-shot Green runner."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from runner.__main__ import main as runner_main


def _default_out() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return str(Path("green") / "out" / stamp / "RECEIPT.md")


def resolve_out(raw: str) -> str:
    """Treat a directory --out as the output folder; write RECEIPT.md inside."""
    path = Path(raw)
    as_dir = (
        raw.endswith(("/", "\\"))
        or path.suffix == ""
        or (path.exists() and path.is_dir())
    )
    if as_dir:
        path.mkdir(parents=True, exist_ok=True)
        return str(path / "RECEIPT.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--out" in args:
        idx = args.index("--out")
        if idx + 1 < len(args):
            args[idx + 1] = resolve_out(args[idx + 1])
    else:
        args = ["--out", _default_out(), *args]
    return runner_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
