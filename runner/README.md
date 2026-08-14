# Runner

One command. Read-only scout (or fixtures if no keys). Exactly one buyer-facing promise. Score. Local markdown + JSON receipt. Exit.

Not a factory. No FastAPI, SQLite, post, listing, checkout, or ping.

## How to run

From the repo root, with no env keys:

```bash
ENVIRONMENT=development python -m runner
```

Writes:

- `receipts/latest.md`
- `receipts/latest.json`

Development never calls xAI, Gumroad, or Supabase. Missing APIs become fixtures. Fixture rows do not count as sourced.

## Paper-win bar

Record hit/miss only. Do not ping anyone. Miss unless **all four** are true:

1. ≥5 sourced non-fixture signals
2. ≥3 pain/intent clues (hype does not count)
3. score >60, confidence medium or high, and source URLs
4. the promise still makes sense after reading the sources

A miss writes the word `miss` and exits.

## Still Red

- first post
- listing
- dollar
- buyer conversation

## Tests

```bash
PYTHONPATH=. python -m pytest runner/tests -v
```

## Sample receipts

- `runner/examples/miss.md` / `runner/examples/miss.json` — default no-keys run
- `runner/examples/hit.md` / `runner/examples/hit.json` — canned sourced path used by pytest
