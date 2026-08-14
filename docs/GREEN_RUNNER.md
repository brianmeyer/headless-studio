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

`--fixtures` (or `GREEN_FORCE_FIXTURES=1`) skips public HTTP and uses fixture rows (still a miss).

Equivalent entry (same pipeline):

```bash
ENVIRONMENT=development python3 -m runner
ENVIRONMENT=development python3 -m runner --topic "chatgpt prompts for property managers" --out receipts/latest.md
```

## Scout path (keys missing)

1. Try public/unauth HTTP: Reddit search JSON and/or the existing Gumroad discover scrape
2. Enrich each Gumroad discover row by GETting its public product page (cap 8 pages) and reading
   buyer-facing copy: Inertia `data-page` `props.product.summary` + HTML-stripped
   `description_html`, else `<meta name="description">`, `og:description`, or schema.org
   `Product.description`
3. If that yields zero live rows, fall back to fixtures
4. Still **miss** unless the four gates pass on **sourced** rows
5. Fixture rows are marked `fixture=true` and **never** count as sourced
6. `--fixtures` / `GREEN_FORCE_FIXTURES=1` skips HTTP and uses fixture rows (still a miss)

Live rows are returned alone. Fixtures are not mixed in to inflate counts. No sales mock on miss.

### Product-page enrich

Reddit keys stay **optional**. Gate 2 (≥3 pain/intent clues) can pass from Gumroad product copy
alone, because product descriptions frequently contain the same pain/intent phrases the Reddit path
looks for (`tired of`, `from scratch`, `manual`, `copy-paste`, `pay for`, `looking for`, `overwhelm`).

Rules the enrich step keeps:

- Pain is **quoted verbatim** from sentences that themselves trip `has_pain_intent`. Nothing is
  invented, paraphrased, or inferred.
- Hype-only copy ("game changer", "revolutionary", "10x viral must-have") yields **no** clues.
- A product GET that 403s, times out, or has no readable description leaves its discover row
  untouched — sourced, but with empty `pain_points`. The row is never dropped.
- `relevance` rises to `0.75` only when real pain/intent was found; otherwise it stays `0.5`.
- Scout notes record every product GET status and how many pages yielded pain/intent.

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
