# Mac omni path receipt

**Builder:** Claude Max via `omni claude` (omnigent 0.9.0, Claude Code 2.1.232)
**Reviewer:** gpt5.6sol via Hermes (`hermes -z -m gpt-5.6-sol --provider openai-codex`)

## Harness / how to run

From `/Users/brianmeyer/headless-studio` on `green-runner-mac`, no secrets:

```bash
python3 -m green
python3 -m green --fixtures
python3 -m green --out green/out
ENVIRONMENT=development python3 -m runner
PYTHONPATH=. python3 -m pytest runner/tests tests/test_green_runner.py -v
```

## Receipt path

- This file: `/Users/brianmeyer/headless-studio/receipts/omni-claude-max__hermes-gpt5.6sol.md`
- Slice receipt: `/Users/brianmeyer/headless-studio/receipts/SLICE_RECEIPT.md`
- Default no-keys run: `/Users/brianmeyer/headless-studio/green/out/manual/RECEIPT.md` (verdict: **miss**)

## Git

- `5586d48` builder — `python -m green` wrapper
- `28719ef` first gpt5.6sol tighten
- `cb18dd5` mixed-fixture hole + rerun command
- Branch: `green-runner-mac` → `origin/green-runner-mac`
- No third cloud agent. PR #3 / `cursor/green-runner-fa74` is a separate paper-win path.

## Flags

Kept/fixed: sourced needs URL; clues need pain/intent; `--out` dir; CI import; **fixtures cannot authorize a hit once sourced rows exist**; receipt rerun command.
Discarded: live HTTP scout (locked Red this slice); adversarial bag-of-words beyond text-only (spec allows simple overlap); backend ruff.

## Brian Red (NOT DONE)

- first post
- listing
- dollar
- buyer conversation
