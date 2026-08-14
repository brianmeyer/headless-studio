# Runner

One command. Read-only scout: public/unauth HTTP if it works, else fixtures. Exactly one buyer-facing promise. Score. Local markdown + JSON receipt. Exit.

Not a factory. No FastAPI, SQLite, post, listing, checkout, or ping.

## How to run

```bash
cd /Users/brianmeyer/headless-studio && ENVIRONMENT=development python3 -m green
```

Pepper crons that command Monday 8:15am ET. Do not add a second scheduler.

Writes (via `python3 -m runner`):

- `receipts/latest.md`
- `receipts/latest.json`

`--fixtures` (or `GREEN_FORCE_FIXTURES=1`) skips HTTP. Missing keys are fine: the default tries public Reddit JSON and Gumroad discover first, then falls back to fixtures. Fixture rows do not count as sourced.

Gumroad discover rows are enriched by GETting each public product page (cap 8) and reading buyer-facing copy — Inertia `data-page` summary/`description_html`, else `<meta name="description">`, `og:description`, or schema.org `Product.description`. Pain is quoted verbatim from sentences that trip the existing pain/intent patterns, so **Reddit keys stay optional** and gate 2 can pass from product copy alone. Hype-only copy yields nothing; a failed product GET keeps the discover row sourced with empty pain.

## Paper-win bar

Record hit/miss only. Do not ping anyone. Miss unless **all four** are true:

1. ≥5 sourced non-fixture signals
2. ≥3 pain/intent clues (hype does not count)
3. score >60, confidence medium or high, and source URLs
4. the promise still makes sense after reading the sources

A miss writes the word `miss` and exits. No mock on miss.

## Still Red

- first post
- listing
- dollar
- buyer conversation

## Tests

```bash
PYTHONPATH=. python3 -m pytest runner/tests tests/test_green_runner.py -v
```

## Sample receipts

- `runner/examples/miss.md` / `runner/examples/miss.json` — fixtures / no sourced rows
- `runner/examples/hit.md` / `runner/examples/hit.json` — canned sourced path used by pytest
