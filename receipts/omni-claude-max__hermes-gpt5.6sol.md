# Mac omni path receipt

**Builder:** Claude Max via `omni claude` (session fc8ee55ed8604790982b50db4dc0fed0) on host :6767
**Checker:** gpt5.6sol via Hermes / OpenAI Codex (sessions 20260814_170239_cd5c1a, 20260814_170528_7dacb2)
**Next pair:** Codex + kimi k3

## How to run the pair

```bash
# host already on :6767
cd /Users/brianmeyer/headless-studio   # omni requires a local path
omni claude --server http://127.0.0.1:6767 --use-native-config
hermes chat -q "$(cat receipts/_review_prompt.md)" -m gpt-5.6-sol -Q --yolo --ignore-rules
```

## How to run the product

```bash
python3 -m green
python3 -m green --fixtures
python3 -m green --out green/out
ENVIRONMENT=development python3 -m runner
PYTHONPATH=. python3 -m pytest runner/tests tests/test_green_runner.py -v
```

## Receipt paths

- Dual-named path receipt (this file): `/Users/brianmeyer/headless-studio/receipts/omni-claude-max__hermes-gpt5.6sol.md`
- Slice receipt (also names both): `/Users/brianmeyer/headless-studio/receipts/SLICE_RECEIPT.md`
- Default no-keys Green run: `/Users/brianmeyer/headless-studio/green/out/manual/RECEIPT.md` (verdict: miss)
- Equivalent runner run: `/Users/brianmeyer/headless-studio/receipts/latest.md` (verdict: miss)
- Hermes review: `/Users/brianmeyer/headless-studio/receipts/_review_gpt56sol.md` and `/Users/brianmeyer/headless-studio/receipts/_hermes_review.md`

## Git

- Branch: `green-runner-mac` (Mac harness path)
- Not PR #3 / `cursor/green-runner-fa74` (paper-win dropped the local mock; spec unchanged here)
- No third cloud agent. No Studio. No Brian ping. No deploy.

## Reviewer verdict

Hermes gpt-5.6-sol initially **block** (scout always fixtures; fixture-inflated hit; `--out` dir crash; missing rerun command).
Fixes applied. Follow-up: **approve-with-fixes**.
R1 (live scout) discarded — fixtures-only is locked Red for this slice.
