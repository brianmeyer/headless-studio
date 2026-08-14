# Headless Green runner — slice receipt

**When:** Friday Aug 14, 2026, 5:12 PM ET

## Pair (this slice)

- **Builder:** Claude Max via `omni claude` on the Mac (session fc8ee55ed8604790982b50db4dc0fed0), plus Cursor cloud agent bc-caaec6cb draft of `runner/`
- **Checker:** gpt5.6sol via Hermes on the Mac (OpenAI Codex; sessions 20260814_170239_cd5c1a, 20260814_170528_7dacb2)
- **Next pair:** Codex + kimi k3
- **How the pair was run:**
  - Builder: `omni claude --server http://127.0.0.1:6767` in `/Users/brianmeyer/headless-studio` (clone required; omni needs a local path)
  - Checker: `hermes chat -q <plan+diff> -m gpt-5.6-sol --yolo` in the same checkout

## How to run the product

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

- This file: `receipts/SLICE_RECEIPT.md`
- Dual-named pair receipt: `receipts/omni-claude-max__hermes-gpt5.6sol.md`
- Checker write-up: `receipts/_hermes_review.md` and `receipts/_review_gpt56sol.md`
- Default no-keys Green run: `green/out/manual/RECEIPT.md` (verdict: **miss**)
- Equivalent runner run: `receipts/latest.md` (verdict: **miss**)

Canned hit path is pytest-only (`sourced_hit_signals()`), which writes a local mock. Nothing is published.

## Git

- Branch: `green-runner-mac`
- PR: https://github.com/brianmeyer/headless-studio/pull/5
- Do not treat merged PR #3 / `cursor/green-runner-fa74` (paper-win, no mock) as the locked path. Spec unchanged: hit still writes a local static mock.

## Checker flags

Fixed:
- R2 sourced rows need an http(s) URL
- R3 clues + text-only coherence; mixed fixtures cannot authorize a hit
- R4 `--out` directory writes `RECEIPT.md`; receipt includes how to re-run
- R5 CI / `PYTHONPATH=.` import path

Discarded:
- R1 live HTTP scout — Red this slice; fixtures-only is locked
- D1 pre-existing backend lint

## Brian Red (NOT DONE)

- first post
- listing
- dollar
- buyer conversation

No deploy. No listings. No Studio. No Brian ping.
