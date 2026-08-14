# Green runner (Vera locked)

One vehicle. `python3 -m green` is the Mac entry for the same paper-win pipeline as `python -m runner`.

One-shot, then exit:

`scout (READ-ONLY) → at most one draft promise → score → local markdown + JSON receipt → exit`

This is the locked path. It does **not** start FastAPI, n8n, Railway, Pinterest, Gumroad publish, ads, MailerLite, auto-post, SQLite-as-the-product, deploy, or Roblox Studio.

## How to run

Exact entrypoint (Pepper crons this Monday 8:15am ET; do not add another scheduler):

```bash
cd /Users/brianmeyer/headless-studio && ENVIRONMENT=development python3 -m green
```

No secrets. No `.env` required. `TAVILY_API_KEY` is optional and never required.

```bash
python3 -m green
python3 -m green --topic "etsy shop bookkeeping spreadsheet"
python3 -m green --fixtures
python3 -m green --out green/out/manual/RECEIPT.md
```

Equivalent entry (same pipeline):

```bash
ENVIRONMENT=development python3 -m runner
ENVIRONMENT=development python3 -m runner --topic "etsy shop bookkeeping" --out receipts/latest.md
```

## Scout path (keys optional)

1. **Tavily Reddit** if a key resolves — process env `TAVILY_API_KEY`, else `TAVILY_API_KEY` alone out of `~/.hermes/.env`, else a note saying it fell back. The key is never printed, logged, or written to a receipt, and no other key in that file is read.
2. **Public Reddit search JSON** as an optional extra hop. Unauthenticated Reddit answers 403; that status is recorded once and **not retried** — no extra headers, no old.reddit, no oauth, no Reddit API credentials. Tavily is the Reddit path that can work.
3. **Gumroad discover, then each product page** (capped at 8, same read-only GET). Pain/intent is attached only when the **page text** says it, quoted as a whole sentence, and enough page text is folded into the signal so gate 4 can read it. A product title is not pain, and neither is a seller answering their own FAQ. A failed page GET keeps the discover row as sourced competition with no invented pain.
4. Zero live sourced rows falls back to fixtures.
5. Still **miss** unless the four gates pass on **sourced** rows.
6. Fixture rows are marked `fixture=true` and **never** count as sourced.
7. Live rows are returned alone — fixtures are not mixed in to inflate counts.
8. `--fixtures` skips HTTP **and** Tavily (still a miss).

Tavily reaches Reddit with `include_domains: ["reddit.com"]` and `site:reddit.com` in the query, plus the topic's buyer language. It is stdlib `urllib` only, no SDK. A 401, an HTTP failure, or an empty result set is noted and the scout continues. No sales mock on miss. No ping.

`python3 -m green` writes `green/out/<timestamp>/RECEIPT.md` (and `.json`) unless `--out` is set.
`python3 -m runner` writes `receipts/latest.md` (and `.json`) unless `--out` is set.

## Topic: scout input, not a SKU

The scouted topic is read from `runner/topics/etsy_small_shop_monthly_books.txt`. It is a **search target** — a topic, a query, direction, and what is out of scope. It is not a product, not approved, and not `runner.fixtures.DEFAULT_TOPIC`, which stays a pytest fixture. `--topic` overrides it.

## Packet: NOT APPROVED

Every receipt is stamped `NOT APPROVED`, hit or miss, with `published: no`.

- No promise is drafted from fixtures. With no sourced rows the packet is **empty** and the run is a miss.
- With sourced rows the runner drafts at most one promise, still `NOT APPROVED`, still not a SKU.
- Approval is a human step and is never automated. Nothing is published, listed, posted, or sold.

Hand-written drafts for the current topic live in `packet/etsy_small_shop_monthly_books/` — a four-tab workbook skeleton (Instructions, Sales & fees, Expenses, Monthly P&L), a listing draft, and post drafts, all marked `NOT APPROVED`.

## Paper-win bar

Write `miss` and stop unless **all four** are true:

1. ≥5 sourced non-fixture signals
2. ≥3 pain/intent clues (not hype)
3. score >60 **and** confidence medium or high **and** sources listed
4. the product promise still makes sense after reading the sources

A miss prints `miss`, writes a short receipt, and does not write a sales mock.
A hit records a `NOT APPROVED` draft on the receipt only. No factory. No ping.

## Score

0–100 ≈ demand + intent + a default competition penalty. Confidence is `low` / `medium` / `high`. Formula lives in `runner/scorer.py`. Live Gumroad rows are competition observations; their pain comes from the page text or not at all.

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

They pass with no secrets: Tavily HTTP is mocked and the Hermes path is pointed at a file that does not exist.
