"""One-shot run writes a receipt and exits. Misses say miss. No ping."""

from __future__ import annotations

import json
from pathlib import Path

from runner import run
from runner.__main__ import main
from runner.fixtures import sourced_hit_signals
from runner.receipt import STILL_RED


def test_default_run_writes_miss_markdown_and_json(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")
    receipt = tmp_path / "receipt.md"
    result = run(out_path=receipt)
    assert result.verdict == "miss"
    text = receipt.read_text(encoding="utf-8")
    assert "miss" in text
    assert "ping:** no" in text
    for item in STILL_RED:
        assert item in text
    assert not (tmp_path / "mocks").exists()
    payload = json.loads((tmp_path / "receipt.json").read_text(encoding="utf-8"))
    assert payload["verdict"] == "miss"
    assert payload["paper_win"] is False
    assert payload["ping"] is False
    assert payload["still_red"] == list(STILL_RED)
    assert all(s.fixture for s in result.signals)


def test_sourced_canned_run_writes_hit_receipt_only(tmp_path: Path):
    receipt = tmp_path / "hit.md"
    result = run(
        topic="chatgpt prompts for property managers",
        out_path=receipt,
        signals=sourced_hit_signals(),
    )
    assert result.verdict == "hit"
    text = receipt.read_text(encoding="utf-8")
    assert "hit" in text
    assert "For property managers:" in result.promise.title
    assert not (tmp_path / "mocks").exists()
    payload = json.loads((tmp_path / "hit.json").read_text(encoding="utf-8"))
    assert payload["paper_win"] is True
    assert payload["ping"] is False
    assert payload["still_red"] == list(STILL_RED)


def test_main_one_liner_writes_miss(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ENVIRONMENT", "development")
    code = main(["--out", "receipts/latest.md"])
    assert code == 0
    captured = capsys.readouterr()
    assert "miss" in captured.out
    written = (tmp_path / "receipts" / "latest.md").read_text(encoding="utf-8")
    assert "miss" in written
    assert (tmp_path / "receipts" / "latest.json").is_file()
