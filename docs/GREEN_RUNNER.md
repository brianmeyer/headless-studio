# Green runner (Vera locked)

One vehicle. `python -m green` is the Mac entry for the same paper-win pipeline as `python -m runner`.

One-shot, then exit:

`scout (READ-ONLY) → one buyer-facing promise → score → local markdown + JSON receipt → exit`

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
ENVIRONMENT=development python -m runner
ENVIRONMENT=development python -m runner --topic "chatgpt prompts for property managers" --out receipts/latest.md
```

`--fixtures` documents the development default (already fixtures-only when APIs/keys are missing). Fixture rows are marked `fixture=true` and **do not** count toward the sourced-signal gate.

`python -m green` writes `green/out/<timestamp>/RECEIPT.md` (and `.json`) unless `--out` is set.
`python -m runner` writes `receipts/latest.md` (and `.json`) unless `--out` is set.

## Paper-win bar

Write `miss` and stop unless **all four** are true:

1. ≥5 sourced non-fixture signals
2. ≥3 pain/intent clues (not hype)
3. score >60 **and** confidence medium or high **and** sources listed
4. the product promise still makes sense after reading the sources

A miss prints `miss`, writes a short receipt, and does not write a sales mock.
A hit records the promise on the receipt only. No factory. No ping.

## Score

0–100 ≈ demand + intent + a default competition penalty (no Gumroad HTTP in this slice). Confidence is `low` / `medium` / `high`. Formula lives in `runner/scorer.py`.

## Still Red (not this slice)

Documented on every receipt. Do not implement them here.

- first post
- listing
- dollar
- buyer conversation

## Tests

```bash
PYTHONPATH=. python -m pytest runner/tests tests/test_green_runner.py -v
```
