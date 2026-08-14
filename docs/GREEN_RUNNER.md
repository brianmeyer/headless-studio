# Green runner (Vera locked)

One vehicle. `python3 -m green` is the Mac entry for the same paper-win pipeline as `python -m runner`.

One-shot, then exit:

`scout (READ-ONLY) → one buyer-facing promise → score → local markdown + JSON receipt → exit`

This is the locked path. It does **not** start FastAPI, n8n, Railway, Pinterest, Gumroad publish, ads, MailerLite, auto-post, SQLite-as-the-product, deploy, or Roblox Studio.

## How to run

Exact entrypoint (Pepper crons this Monday 8:15am ET; do not add another scheduler):

```bash
cd /Users/brianmeyer/headless-studio && ENVIRONMENT=development python3 -m green
```

No secrets. No `.env` required.

```bash
python3 -m green
python3 -m green --topic "chatgpt prompts for property managers"
python3 -m green --fixtures
python3 -m green --out green/out/manual/RECEIPT.md
```

Equivalent entry (same pipeline):

```bash
ENVIRONMENT=development python3 -m runner
ENVIRONMENT=development python3 -m runner --topic "chatgpt prompts for property managers" --out receipts/latest.md
```

## Scout path (keys missing)

1. Try public/unauth HTTP: Reddit search JSON and/or the existing Gumroad discover scrape
2. If that yields zero live rows, fall back to fixtures
3. Still **miss** unless the four gates pass on **sourced** rows
4. Fixture rows are marked `fixture=true` and **never** count as sourced
5. `--fixtures` skips HTTP and uses fixture rows (still a miss)

Live rows are returned alone. Fixtures are not mixed in to inflate counts. No sales mock on miss.

`python3 -m green` writes `green/out/<timestamp>/RECEIPT.md` (and `.json`) unless `--out` is set.
`python3 -m runner` writes `receipts/latest.md` (and `.json`) unless `--out` is set.

## Paper-win bar

Write `miss` and stop unless **all four** are true:

1. ≥5 sourced non-fixture signals
2. ≥3 pain/intent clues (not hype)
3. score >60 **and** confidence medium or high **and** sources listed
4. the product promise still makes sense after reading the sources

A miss prints `miss`, writes a short receipt, and does not write a sales mock.
A hit records the promise on the receipt only. No factory. No ping.

## Score

0–100 ≈ demand + intent + a default competition penalty. Confidence is `low` / `medium` / `high`. Formula lives in `runner/scorer.py`. Live Gumroad rows are competition observations, not invented buyer pain.

## Still Red (not this slice)

Documented on every receipt. Do not implement them here.

- first post
- listing
- dollar
- buyer conversation

## Tests

```bash
PYTHONPATH=. python3 -m pytest runner/tests tests/test_green_runner.py -v
```
