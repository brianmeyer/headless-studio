"""
The packet is a draft: NOT APPROVED on every path, no invented promise, no borrowed proof.

Also guards the locked pieces: four workbook tabs, the exact listing sentence, the
$15–30 band, and DEFAULT_TOPIC staying a pytest fixture rather than a SKU string.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from runner import run
from runner.fixtures import DEFAULT_TOPIC, sourced_hit_signals
from runner.receipt import PACKET_APPROVAL
from runner.scout_input import (
    SCOUT_TOPIC_FILE,
    load_scout_input,
    parse_scout_input,
    scout_topic,
)

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "packet" / "etsy_small_shop_monthly_books"
WORKBOOK = PACKET / "workbook"

LOCKED_SENTENCE = (
    "A Google Sheets and Excel workbook for Etsy sellers to enter sales and fees, log "
    "expenses, and see a monthly profit and loss — without QuickBooks."
)

LOCKED_TABS = ("Instructions", "Sales & fees", "Expenses", "Monthly P&L")
TAB_FILES = (
    "1_Instructions.csv",
    "2_Sales_and_fees.csv",
    "3_Expenses.csv",
    "4_Monthly_P_and_L.csv",
)

# Claims Vera struck. None of these may appear as a claim in packet copy.
BANNED_CLAIMS = (
    "118 reviews",
    "bestseller",
    "best seller",
    "cpa-designed",
    "cpa designed",
    "automagical",
    "lifetime updates",
    "facebook club",
    "not a clone",
    "$97",
)

BANNED_TABS = ("kpi", "budget", "inventory", "tax form map", "tax-form map")

# Sections that exist to forbid copy. Listing a banned phrase here is the point.
FORBIDDING_HEADINGS = (
    "claims we do not make",
    "claims not to make",
    "do not write",
    "not claimed",
    "what it is not",
    "out of scope",
)


def _packet_docs() -> list[Path]:
    return sorted(PACKET.glob("*.md"))


def _claim_lines(text: str) -> list[str]:
    """Lines that read as our own copy, skipping the do-not-say sections."""
    lines: list[str] = []
    forbidding = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip().lower()
            forbidding = any(marker in heading for marker in FORBIDDING_HEADINGS)
            continue
        if not forbidding:
            lines.append(stripped)
    return lines


def test_packet_docs_exist_and_are_marked_not_approved():
    names = {path.name for path in _packet_docs()}
    assert {"README.md", "WORKBOOK.md", "listing.md", "posts.md"} <= names
    for path in _packet_docs():
        head = path.read_text(encoding="utf-8").splitlines()[0]
        assert "NOT APPROVED" in head, f"{path.name} must be stamped in its first line"


def test_listing_uses_the_locked_sentence_and_price_band():
    listing = (PACKET / "listing.md").read_text(encoding="utf-8")
    assert LOCKED_SENTENCE in listing
    assert "$15–30" in listing
    assert "$97" not in listing.replace("Not $97.", "")


def test_packet_copy_makes_no_banned_claim():
    """A do-not-say list may name a phrase. Our own copy may not use it."""
    for path in _packet_docs():
        for line in _claim_lines(path.read_text(encoding="utf-8").lower()):
            for phrase in BANNED_CLAIMS:
                if phrase not in line:
                    continue
                assert any(
                    marker in line
                    for marker in ("not ", "no ", "never", "none of", "stays out", "n't")
                ), f"{path.name} appears to claim '{phrase}': {line}"


def test_packet_never_claims_paper_and_spark_parity():
    for path in _packet_docs():
        for line in _claim_lines(path.read_text(encoding="utf-8").lower()):
            if "paper+spark" not in line and "paper + spark" not in line:
                continue
            assert any(
                marker in line for marker in ("not ", "no ", "never", "out of scope", "none of")
            ), f"{path.name} compares us to Paper+Spark: {line}"


def test_workbook_has_exactly_the_four_locked_tabs():
    csvs = sorted(p.name for p in WORKBOOK.glob("*.csv"))
    assert csvs == sorted(TAB_FILES)

    spec = (PACKET / "WORKBOOK.md").read_text(encoding="utf-8")
    for tab in LOCKED_TABS:
        assert tab in spec

    # The tab table in WORKBOOK.md lists four tabs and no fifth.
    table_rows = [
        line
        for line in spec.splitlines()
        if line.startswith("| ") and ".csv`" in line
    ]
    assert len(table_rows) == 4
    for banned in BANNED_TABS:
        assert not any(banned in row.lower() for row in table_rows)
        assert not any(banned in name.lower() for name in csvs)


def test_workbook_tabs_parse_and_monthly_pl_reads_the_other_tabs():
    for name in TAB_FILES:
        rows = list(csv.reader((WORKBOOK / name).open(encoding="utf-8")))
        assert rows, f"{name} is empty"
        assert all(isinstance(cell, str) for row in rows for cell in row)

    profit = (WORKBOOK / "4_Monthly_P_and_L.csv").read_text(encoding="utf-8")
    assert "'Sales & fees'!$D:$D" in profit
    assert "Expenses!$E:$E" in profit
    assert "EOMONTH($B$2,0)" in profit
    assert "Profit before tax" in profit
    assert "NOT APPROVED" in profit

    sales = list(csv.reader((WORKBOOK / "2_Sales_and_fees.csv").open(encoding="utf-8")))
    assert sales[0][0] == "Date"
    assert sales[0][-1] == "Net to bank"
    assert sales[1][-1].startswith("=IF($A2=")


def test_workbook_generator_is_reproducible(tmp_path: Path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "make_workbook_csvs", WORKBOOK / "make_workbook_csvs.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.TABS == LOCKED_TABS
    written = module.write_tabs(tmp_path)
    assert sorted(p.name for p in written) == sorted(TAB_FILES)
    for path in written:
        assert path.read_text(encoding="utf-8") == (WORKBOOK / path.name).read_text(
            encoding="utf-8"
        )


def test_scout_input_is_a_search_target_not_a_sku():
    spec = load_scout_input()
    assert spec.topic == "etsy_small_shop_monthly_books"
    assert spec.approved is False
    assert spec.query
    assert "etsy" in spec.search_text.lower()
    assert "prompt packs" in spec.out_of_scope
    assert scout_topic() == spec.topic
    raw = SCOUT_TOPIC_FILE.read_text(encoding="utf-8")
    assert "not a SKU" in raw
    assert "DEFAULT_TOPIC" in raw


def test_scout_input_parser_ignores_comments_and_unknown_keys():
    spec = parse_scout_input(
        "\n".join(
            [
                "# comment: ignored",
                "topic: t",
                "query: q",
                "hint: h",
                "surprise: ignored",
                "out_of_scope: a, b ,, c",
            ]
        )
    )
    assert (spec.topic, spec.query, spec.hint) == ("t", "q", "h")
    assert spec.out_of_scope == ("a", "b", "c")


def test_missing_scout_input_file_is_not_a_crash(tmp_path: Path):
    spec = load_scout_input(tmp_path / "gone.txt")
    assert spec.topic == ""
    assert spec.search_text == ""


def test_default_topic_stays_a_pytest_fixture():
    """DEFAULT_TOPIC is fixture furniture. It is not the scout topic and not a SKU."""
    assert DEFAULT_TOPIC == "chatgpt prompts for property managers"
    assert DEFAULT_TOPIC != scout_topic()
    assert "etsy" not in DEFAULT_TOPIC.lower()


def test_fixtures_run_drafts_no_promise_and_stays_not_approved(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    receipt = tmp_path / "RECEIPT.md"
    result = run(out_path=receipt, use_fixtures=True)

    assert result.verdict == "miss"
    assert result.topic == "etsy_small_shop_monthly_books"
    assert result.drafted is False
    assert result.promise.title == ""
    assert result.promise.pain_addressed == ()

    text = receipt.read_text(encoding="utf-8")
    assert PACKET_APPROVAL in text
    assert "nothing drafted" in text
    assert "property managers" not in text.lower().split("## signals")[0]

    payload = json.loads((tmp_path / "RECEIPT.json").read_text(encoding="utf-8"))
    assert payload["approved"] is False
    assert payload["approval"] == PACKET_APPROVAL
    assert payload["published"] is False
    assert payload["promise"]["drafted"] is False
    assert payload["promise"]["text"] == ""
    assert payload["scout_input"]["approved"] is False
    assert payload["scout_input"]["topic"] == "etsy_small_shop_monthly_books"
    assert "prompt packs" in payload["scout_input"]["out_of_scope"]


def test_hit_packet_is_still_not_approved(tmp_path: Path):
    receipt = tmp_path / "RECEIPT.md"
    result = run(topic="chatgpt prompts for property managers", out_path=receipt,
                 signals=sourced_hit_signals())
    assert result.verdict == "hit"
    assert result.drafted is True
    text = receipt.read_text(encoding="utf-8")
    assert PACKET_APPROVAL in text
    assert "not a SKU" in text
    payload = json.loads((tmp_path / "RECEIPT.json").read_text(encoding="utf-8"))
    assert payload["paper_win"] is True
    assert payload["approved"] is False
    assert payload["published"] is False
    assert payload["ping"] is False


def test_no_promise_is_drafted_from_fixture_rows(tmp_path: Path, monkeypatch):
    """Fixtures cannot manufacture a promise, even when live HTTP fails."""
    monkeypatch.setattr("runner.live.http_get", lambda url, timeout=12.0: (403, "Blocked"))
    result = run(out_path=tmp_path / "RECEIPT.md")
    assert all(s.fixture for s in result.signals)
    assert result.drafted is False
    assert result.promise.description == ""
