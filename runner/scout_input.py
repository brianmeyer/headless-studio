"""
The scout's topic input: a search target, not a SKU.

`runner.fixtures.DEFAULT_TOPIC` stays what it always was — the pytest fixture
topic. The topic scouted by `python3 -m green` is read from a file here so a
topic can change without anyone hardcoding a product promise into the runner.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

TOPIC_DIR = Path(__file__).resolve().parent / "topics"
SCOUT_TOPIC_FILE = TOPIC_DIR / "etsy_small_shop_monthly_books.txt"
APPROVAL = "NOT APPROVED"


@dataclass(frozen=True)
class ScoutInput:
    """One scout target. `approved` is always False: this is not a SKU."""

    topic: str = ""
    query: str = ""
    hint: str = ""
    out_of_scope: tuple[str, ...] = ()
    path: str = ""

    @property
    def approved(self) -> bool:
        return False

    @property
    def search_text(self) -> str:
        return self.query or self.topic


def parse_scout_input(text: str, path: str = "") -> ScoutInput:
    """Parse `key: value` lines. Comments and unknown keys are ignored."""
    fields: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        fields[key.strip().lower()] = value.strip()
    scope = fields.get("out_of_scope", "")
    return ScoutInput(
        topic=fields.get("topic", ""),
        query=fields.get("query", ""),
        hint=fields.get("hint", ""),
        out_of_scope=tuple(item.strip() for item in scope.split(",") if item.strip()),
        path=path,
    )


def load_scout_input(path: str | Path | None = None) -> ScoutInput:
    """Read the scout input file. A missing file yields an empty target, not a crash."""
    target = Path(path) if path is not None else SCOUT_TOPIC_FILE
    try:
        raw = target.read_text(encoding="utf-8")
    except OSError:
        return ScoutInput(path=str(target))
    return parse_scout_input(raw, path=str(target))


def scout_topic() -> str:
    """Default `--topic` value: the scout input topic, never a product string."""
    return load_scout_input().topic
