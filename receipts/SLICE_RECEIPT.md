# Headless Green runner — slice receipt

**When:** Friday Aug 14, 2026, 5:08 PM ET

## Pair (this slice)

- **Builder:** Claude Max via `omni claude` on the Mac
- **Checker:** gpt5.6sol via Hermes on the Mac (Hermes default `gpt-5.6-sol` / OpenAI Codex)
- **Next pair:** Codex + kimi k3

## How to run

From repo root, no secrets, no `.env`:

```bash
python -m green
python -m green --topic "chatgpt prompts for property managers"
python -m green --fixtures
python -m green --out green/out
ENVIRONMENT=development python -m runner
```

Tests:

```bash
PYTHONPATH=. python -m pytest runner/tests tests/test_green_runner.py -v
```

## Receipt path

Default no-keys / `--fixtures` run (this machine):

`green/out/manual/RECEIPT.md`

Verdict: **miss** (0 sourced non-fixture signals). No static mock. That is the locked silence path.

Canned hit path is pytest-only (`sourced_hit_signals()`), which writes a local mock. Nothing is published.

## Git

- Branch: `green-runner-mac`
- Builder commit: `5586d48` (`python -m green` wrapper over `runner/`)
- Checker fix-up: this commit
- Remote: `origin/green-runner-mac`
- Do not use `cursor/green-runner-fa74` / PR #3 as the locked path — that cloud agent later dropped the HTML mock (“paper-win”), which changes the Green spec.

## Checker flags

Fixed: R2 (sourced needs URL), R3 (clues + text-only coherence), R4 (`--out` directory), R5 (CI import path).
Discarded: R1 (live HTTP — Red this slice), D1 (pre-existing backend lint).

## Brian Red (NOT DONE)

- first post
- listing
- dollar
- buyer conversation

No deploy. No listings. No Studio. No Brian ping.
