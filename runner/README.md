# Runner

The runner is the product. One command. Read-only scout. One product promise. Score. Local receipt. Exit.

It does **not** boot FastAPI, SQLite, Supabase, n8n, Railway, Gumroad, ads, or social.

## How to run

From the repo root, with no env keys:

```bash
python -m green
ENVIRONMENT=development python -m runner
```

Equivalent:

```bash
python -m runner --topic "chatgpt prompts for property managers" --out receipts/latest.md
```

Development (the default) never calls xAI, Gumroad, or Supabase. Missing APIs become fixtures. Fixture rows do not count as sourced signals.

## Silence

The receipt is **miss** and the process stops unless **all four** are true:

1. ≥5 sourced non-fixture signals
2. ≥3 pain/intent clues (hype does not count)
3. score >60, confidence medium or high, and source URLs
4. the promise still makes sense after reading the sources

A miss writes a markdown receipt that contains the word `miss` and does **not** write a static mock.

A hit writes the receipt plus a local static HTML mock under `receipts/mocks/`. Nothing is published.

## Tests

```bash
pytest runner/tests -v
```

## Example receipts

- `runner/examples/miss.md` — what `python -m runner` writes with no secrets (fixtures only). The file contains the word `miss` and no static mock.
- `runner/examples/hit.md` — canned sourced signals used by pytest. Not produced by the default no-keys command.
