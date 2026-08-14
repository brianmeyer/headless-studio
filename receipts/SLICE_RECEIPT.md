# Headless Green runner — slice receipt

**When:** Friday Aug 14, 2026, 5:10 PM ET

## Pair (this slice)

- **Builder:** Claude Max via `omni claude` on Brian's Mac (omnigent 0.9.0, Claude Code 2.1.232, `--effort xhigh`)
- **Checker:** gpt5.6sol via Hermes on the Mac (`hermes -z -m gpt-5.6-sol --provider openai-codex`)
- **Next pair:** Codex / grok5.6 (builder ≠ Claude Max; checker ≠ gpt5.6sol)

## Harness used

`omni claude` (Claude Max, print mode, bypassPermissions after /tmp sandbox stall). Repo: `/Users/brianmeyer/headless-studio` on `green-runner-mac`. Local clone only; no third cloud agent.

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

`green/out/manual/RECEIPT.md` (this machine, fixtures / no keys). Verdict: **miss**. No static mock.

Canned hit path is pytest-only (`sourced_hit_signals()`). Nothing is published.

## Git

- Branch: `green-runner-mac` → `origin/green-runner-mac`
- Builder: `5586d48` (`python -m green` wrapper over `runner/`)
- First checker fix-up: `28719ef`
- Remaining mixed-fixture / rerun fix-up: this commit
- Cloud PR #3 / `cursor/green-runner-fa74` is a parallel paper-win path — not this Mac lock

## Checker flags

Kept and fixed:
- R2 sourced-without-URL (`sourced_signals` requires http(s) URL)
- R3 clues required a pain/intent pattern; gate 4 reads source text only
- `--out` directory writes `RECEIPT.md` inside
- CI / `PYTHONPATH` so `runner` imports
- **Mixed fixtures cannot authorize a hit** (clues/score/draft use sourced-only once any sourced row exists). Reproduced: 5 weather URLs + 4 fixtures went from score 72.6 medium / 8 fixture clues to score 32.2 low / 0 clues. Test: `test_mixed_fixtures_cannot_authorize_a_hit`
- Receipt now includes how to re-run

Discarded:
- R1 live HTTP scout — Vera lock this slice: no live xAI / Gumroad HTTP / Supabase. Fixtures-only CLI is the product. Hit path is canned pytest objects.
- Loose bag-of-words coherence (beyond text-only) — spec allows a simple keyword/theme overlap check
- Backend ruff / pre-existing FastAPI lint — out of slice

## Brian Red (NOT DONE)

- first post
- listing
- dollar
- buyer conversation

No deploy. No listings. No Studio. No Brian ping.
