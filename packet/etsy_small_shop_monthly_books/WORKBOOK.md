# Workbook skeleton — NOT APPROVED

Draft only. Four tabs, per Vera's lock. No KPI, budget, inventory, or tax-form-map tabs.

| # | Tab | File |
| --- | --- | --- |
| 1 | Instructions | `workbook/1_Instructions.csv` |
| 2 | Sales & fees | `workbook/2_Sales_and_fees.csv` |
| 3 | Expenses | `workbook/3_Expenses.csv` |
| 4 | Monthly P&L | `workbook/4_Monthly_P_and_L.csv` |

One CSV per tab so the skeleton reads in git and imports into Google Sheets or opens
in Excel with nothing installed. Regenerate them with the standard library:

```bash
python3 packet/etsy_small_shop_monthly_books/workbook/make_workbook_csvs.py
```

## 1. Instructions

Plain-language setup: what to type where, the pass-through treatment of sales tax
collected, the expense category list to copy, and a plain "this is not tax advice, and
it was not designed or reviewed by a CPA" line.

## 2. Sales & fees

One row per order. `Net to bank` is the only formula.

| Col | Header | Notes |
| --- | --- | --- |
| A | Date | A real date, not text |
| B | Order ID | From the Etsy or shop export |
| C | Channel | Etsy, own site, market stall |
| D | Gross sales | Item total before anything comes off |
| E | Discounts | Coupons and sales |
| F | Shipping charged to buyer | Income |
| G | Sales tax collected | Pass-through, never profit |
| H | Marketplace fees | Listing, transaction |
| I | Payment processing fees | Card and payment fees |
| J | Ads fees (on platform) | Etsy ads / offsite ads |
| K | Refunds | Money returned |
| L | Net to bank | `=IF($A2="","",D2-E2+F2+G2-H2-I2-J2-K2)` |

## 3. Expenses

One row per purchase, off-platform costs only (selling fees live on the Sales & fees
tab): Date, Vendor, Category, Description, Amount, Payment method, Notes.

Categories, spelled exactly as the Monthly P&L rows read them:

Materials & supplies · Packaging & shipping supplies · Postage & labels ·
Software & subscriptions · Advertising off Etsy · Home office & utilities share ·
Mileage & travel · Professional services · Bank & payment fees · Other

## 4. Monthly P&L

Type the first day of a month in `B2`. `B3` is `=EOMONTH($B$2,0)`. Everything else is
a `SUMIFS` over the two data tabs inside that date window.

- Money in: gross sales, discounts, refunds, net revenue, shipping charged, sales tax
  collected (shown, then excluded from profit)
- Selling fees: marketplace, payment processing, on-platform ads, total
- Expenses: one row per category, then a total
- `Profit before tax` = net revenue + shipping charged − total selling fees − total expenses
- A set-aside rate the seller picks, the money to set aside, and what is left

Formulas name the tabs exactly, so keep the tab names when importing:

```
=SUMIFS('Sales & fees'!$D:$D,'Sales & fees'!$A:$A,">="&$B$2,'Sales & fees'!$A:$A,"<="&$B$3)
=SUMIFS(Expenses!$E:$E,Expenses!$A:$A,">="&$B$2,Expenses!$A:$A,"<="&$B$3,Expenses!$C:$C,$A20)
```

## Google Sheets

1. New spreadsheet → **File → Import** → upload `1_Instructions.csv` → *Insert new sheet*.
2. Repeat for the other three CSVs.
3. Rename the four tabs to `Instructions`, `Sales & fees`, `Expenses`, `Monthly P&L`.
4. Open Monthly P&L and set `B2` to the first day of the month.

## Excel

1. Open each CSV (**File → Open**), then copy the sheet into one workbook.
2. Name the four sheets `Instructions`, `Sales & fees`, `Expenses`, `Monthly P&L`.
3. Save as `.xlsx`.
4. Set `B2` on Monthly P&L.

If a formula arrives as text, retype the leading `=` in that cell.

## Not claimed

Not tax, legal, or accounting advice. Not designed or reviewed by a CPA. No comparison
claim against any other shop's workbook, none of their reviews, no bestseller claim, no
lifetime updates, no community or club, and no sales numbers of our own.
