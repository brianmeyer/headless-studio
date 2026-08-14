# Green runner (Vera locked)

One-shot, then exit:

`scout (READ-ONLY) → one product promise → score → local static mock + markdown receipt → exit`

This is the locked path. It does **not** start FastAPI, n8n, Railway, Pinterest, Gumroad publish, ads, MailerLite, auto-post, SQLite-as-the-product, deploy, or Roblox Studio.

## How to run

From the repo root. No secrets. No `.env` required.

```bash
python -m green
python -m green --topic "chatgpt prompts for property managers"
python -m green --fixtures
python -m green --out green/out/manual/RECEIPT.md
```

Equivalent entry (same pipeline):

```bash
python -m runner
python -m runner --topic "chatgpt prompts for property managers" --out receipts/latest.md
```

`--fixtures` forces the fixture scout (already the development default when APIs/keys are missing). Fixture rows are marked `fixture=true` and **do not** count toward the sourced-signal gate.

## Silence

Write `miss` and stop unless **all four** are true:

1. ≥5 sourced non-fixture signals
2. ≥3 pain/intent clues (not hype)
3. score >60 **and** confidence medium or high **and** sources listed
4. the product promise still makes sense after reading the sources

A miss prints `miss`, writes a short receipt, and does not write a sales mock.
A hit writes `mock.html` / `index.html` (local static, marked MOCK / not for sale) plus `RECEIPT.md`.

## Score

0–100 ≈ demand + intent + a default competition penalty (no Gumroad HTTP in this slice). Confidence is `low` / `medium` / `high`. Formula lives in `runner/scorer.py`.

## Brian Red gates (not this slice)

Documented on every receipt as **NOT DONE**:

- first post
- listing
- dollar
- buyer conversation

Do not implement them here.

## Tests

```bash
PYTHONPATH=. python -m pytest runner/tests tests/test_green_runner.py -v
```
