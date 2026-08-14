# Hermes review (gpt-5.6-sol)

Builder: Claude Max via `omni claude` (Mac), commit 5586d48 plus this fix-up.
Checker: gpt-5.6-sol via Hermes on the Mac (session 20260814_170239_cd5c1a).

## Verdict

approve-with-fixes (fixes applied on green-runner-mac)

## Real flags

### R2 — sourced without a URL — FIXED
`runner/scorer.py` counted every `fixture=False` row as sourced. Five URL-less rows plus one URL could pass gate 1+3. `sourced_signals()` now requires an `http(s)` URL. Test: `test_url_less_non_fixture_is_not_sourced`.

### R3 — clues too loose / coherence used metadata — FIXED
`extract_clues` treated any 12-character structured field as pain/intent. Gate 4 mixed `pain_points` metadata into the source corpus. A probe of five neutral records could pass. Clues now require a pain/intent pattern. Gate 4 reads signal text only. Tests: `test_neutral_signals_cannot_pass_silence_gates`, `test_fewer_than_three_clues_is_a_miss`.

### R4 — `python -m green --out green/out` — FIXED
`--out` was forwarded as a receipt filename, so a directory raised `IsADirectoryError`. Directory `--out` now writes `RECEIPT.md` inside. Test: `test_green_out_directory_writes_receipt`.

### R5 — CI `ModuleNotFoundError: runner` — FIXED
Job used `pytest runner/tests`. Now `PYTHONPATH=. python -m pytest runner/tests tests/test_green_runner.py`. Added `runner/tests/conftest.py` so a bare pytest invocation still imports `runner`.

## Discarded

### R1 — scout always returns fixtures — discarded
Green/Red for this slice: no live xAI, Gumroad HTTP, or Supabase. `scout()` is fixtures-only on purpose. `live_keys_present()` is detection-only. A default no-keys run must miss. The hit path is the canned pytest objects, not a live API. Implementing live adapters would violate the locked Red list.

### D1 — backend lint job — discarded
Pre-existing `backend/app/services/*` Ruff findings. Not in this slice. Not caused by the runner.

## Spec check

| Check | Result |
| --- | --- |
| ≥5 sourced non-fixture + URL | pass (R2) |
| ≥3 pain/intent, not hype | pass (R3) |
| score >60, medium+, source URLs | pass |
| promise matches source text | pass (R3) |
| no live HTTP | pass (R1 discarded) |
| miss contains `miss`, no mock | pass |
| how to run (`python -m green` / `python -m runner`) | pass |
