"""Vera-locked Green entry: fixtures miss; hit writes mock; Red gates documented."""

from __future__ import annotations

from pathlib import Path

from green.__main__ import main as green_main
from runner import run
from runner.fixtures import sourced_hit_signals


def test_green_fixtures_cli_writes_miss(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    code = green_main(["--fixtures", "--out", "green/out/t/RECEIPT.md"])
    assert code == 0
    out = capsys.readouterr().out
    assert "miss" in out
    receipt = tmp_path / "green" / "out" / "t" / "RECEIPT.md"
    text = receipt.read_text(encoding="utf-8")
    assert "miss" in text
    assert "first post" in text
    assert "NOT DONE" in text
    assert not (tmp_path / "green" / "out" / "t" / "mocks").exists()


def test_green_hit_writes_mock_and_red_gates(tmp_path: Path):
    receipt = tmp_path / "RECEIPT.md"
    result = run(
        topic="chatgpt prompts for property managers",
        out_path=receipt,
        signals=sourced_hit_signals(),
    )
    assert result.verdict == "hit"
    text = receipt.read_text(encoding="utf-8")
    assert "hit" in text
    assert "buyer conversation" in text
    assert "NOT DONE" in text
    assert result.mock_path is not None
    assert result.mock_path.is_file()


def test_score_60_or_less_is_miss(tmp_path: Path):
    from runner.draft import draft_promise
    from runner.fixtures import sourced_hit_signals
    from runner.gates import evaluate_gates
    from runner.models import Score

    signals = sourced_hit_signals()
    promise = draft_promise(signals, "chatgpt prompts for property managers")
    score = Score(total=60, demand=40, intent=25, competition=-5, confidence="medium", source_urls=("https://example.com/a",))
    report = evaluate_gates(signals, promise, score)
    assert report.by_name("score_medium_sources").passed is False
    assert report.all_passed is False
