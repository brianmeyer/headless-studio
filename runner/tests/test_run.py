"""One-shot run writes a receipt and exits. Misses say miss."""

from __future__ import annotations

from pathlib import Path

from runner import run
from runner.__main__ import main
from runner.fixtures import sourced_hit_signals


def test_default_run_writes_miss_and_no_mock(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")
    receipt = tmp_path / "receipt.md"
    result = run(out_path=receipt)
    assert result.verdict == "miss"
    assert receipt.is_file()
    text = receipt.read_text(encoding="utf-8")
    assert "miss" in text
    assert result.mock_path is None
    assert not (tmp_path / "mocks").exists()
    assert all(s.fixture for s in result.signals)


def test_sourced_canned_run_writes_hit_and_static_mock(tmp_path: Path):
    receipt = tmp_path / "hit.md"
    result = run(
        topic="chatgpt prompts for property managers",
        out_path=receipt,
        signals=sourced_hit_signals(),
    )
    assert result.verdict == "hit"
    text = receipt.read_text(encoding="utf-8")
    assert "hit" in text
    assert result.mock_path is not None
    assert result.mock_path.is_file()
    mock = result.mock_path.read_text(encoding="utf-8")
    assert "LOCAL STATIC MOCK" in mock
    assert result.promise.title in mock


def test_main_one_liner_writes_miss(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ENVIRONMENT", "development")
    code = main(["--out", "receipts/latest.md"])
    assert code == 0
    captured = capsys.readouterr()
    assert "miss" in captured.out
    written = (tmp_path / "receipts" / "latest.md").read_text(encoding="utf-8")
    assert "miss" in written
