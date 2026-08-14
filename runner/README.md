# Runner

One command. Read-only scout: optional Tavily Reddit, public HTTP, else fixtures. At most one draft promise. Score. Local markdown + JSON receipt. Exit.

Not a factory. No FastAPI, SQLite, post, listing, checkout, or ping. Every packet is `NOT APPROVED`.

## How to run

```bash
cd /Users/brianmeyer/headless-studio && ENVIRONMENT=development python3 -m green
```

Pepper crons that command Monday 8:15am ET. Do not add a second scheduler.

Writes (via `python3 -m runner`):

- `receipts/latest.md`
- `receipts/latest.json`

## Scout order (keys optional)

1. **Tavily Reddit** — `TAVILY_API_KEY` from the process env, else that one key out of `~/.hermes/.env`, else a note that it fell back. Optional, never required, never printed. `include_domains: ["reddit.com"]` plus `site:reddit.com` in the query, stdlib `urllib`, no SDK.
2. **Public Reddit JSON** — an extra hop. 403 without auth is expected, recorded once, and **not retried**.
3. **Gumroad discover + product pages** — up to 8 pages, read-only. Pain/intent only if the page text says it, quoted as a sentence; a product title is not pain, and a seller's own FAQ ("Q: How do I…") is not pain either. A failed page GET stays sourced competition with no invented pain.
4. No live sourced rows → fixtures → still a miss.

Fixture rows never count as sourced, and live rows are never mixed with them. `--fixtures` skips HTTP and Tavily.

## Topic

`--topic` overrides; the default is the scout input in `runner/topics/`. That file is a search target, not a SKU. `DEFAULT_TOPIC` in `runner/fixtures.py` is pytest furniture and stays that way.

## Paper-win bar

Record hit/miss only. Do not ping anyone. Miss unless **all four** are true:

1. ≥5 sourced non-fixture signals
2. ≥3 pain/intent clues (hype does not count)
3. score >60, confidence medium or high, and source URLs
4. the promise still makes sense after reading the sources

A miss writes the word `miss` and exits. No mock on miss. Nothing is drafted from fixtures, so a miss with no sourced rows has an empty packet.

## Still Red

- first post
- listing
- dollar
- buyer conversation

## Tests

```bash
PYTHONPATH=. python3 -m pytest runner/tests tests/test_green_runner.py -v
```

No secrets needed: Tavily HTTP is mocked and the Hermes `.env` path is redirected in `conftest.py`.

## Sample receipts

- `runner/examples/miss.md` / `runner/examples/miss.json` — fixtures / no sourced rows, empty packet
- `runner/examples/hit.md` / `runner/examples/hit.json` — canned sourced path used by pytest
