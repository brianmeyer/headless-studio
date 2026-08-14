# NOT APPROVED — packet draft: monthly books for a small Etsy/shop seller

Draft only. Nothing in this folder is published, listed, posted, priced live, or sold.
Approval is a human step and is not automated. The runner stamps every packet
`NOT APPROVED`, hit or miss.

## What this is

A Google Sheets and Excel workbook so a non-technical Etsy or small-shop seller can
enter sales and fees, log expenses, and see a monthly profit and loss without
QuickBooks.

- Price band (draft): **$15–30**. Not $97.
- Google Sheets + Excel. Not Notion. Not a prompt pack.
- Skeleton only: headers, categories, and formulas. No customer data.

## Tab list (Vera LOCK — four tabs, nothing else)

1. Instructions
2. Sales & fees
3. Expenses
4. Monthly P&L

No KPI, budget, inventory, or tax-form-map tabs. See [WORKBOOK.md](WORKBOOK.md) for
the columns and formulas, and `workbook/` for the four CSV tabs.

## Files

| File | What it is |
| --- | --- |
| [WORKBOOK.md](WORKBOOK.md) | Tab spec, columns, formulas, import steps |
| `workbook/*.csv` | The four locked tabs, one CSV each |
| `workbook/make_workbook_csvs.py` | stdlib generator for those CSVs |
| [listing.md](listing.md) | `NOT APPROVED` listing draft |
| [posts.md](posts.md) | `NOT APPROVED` post drafts |

## Claims we do not make

No comparison claim against Paper+Spark or anyone else, and none of their proof:

- not "the same as" any other shop's product, and not "not a clone" either
- no borrowed review counts (their 118 reviews are theirs)
- no bestseller claim
- no CPA-designed claim
- no "automagical"
- no lifetime updates promise
- no Facebook club or community promise
- no sales, revenue, or customer numbers of our own — we have none

Anything the workbook cannot do stays unclaimed until the workbook does it.

## Out of scope this week

prompt packs, PM/RE, Notion rental OS, Paper+Spark feature clone, manufacture this week.

## Still Red (documented, not built)

first post, listing, dollar, buyer conversation.

## Where the topic came from

`runner/topics/etsy_small_shop_monthly_books.txt` is a **scout input** — a search
target for `python3 -m green`. It is not a SKU and it is not
`runner.fixtures.DEFAULT_TOPIC`, which stays a pytest fixture.
