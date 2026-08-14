#!/usr/bin/env python3
"""
Generate the four locked workbook tabs as CSV. Standard library only.

Vera LOCK: Instructions, Sales & fees, Expenses, Monthly P&L. Four tabs, nothing
else — no KPI, budget, inventory, or tax-form-map tabs.

CSV keeps the skeleton readable in git and importable by both Google Sheets and
Excel without any dependency. Run from anywhere:

    python3 packet/etsy_small_shop_monthly_books/workbook/make_workbook_csvs.py

Draft only. NOT APPROVED. Nothing here is published, listed, or sold.
"""

from __future__ import annotations

import csv
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
DATA_ROWS = 50

TABS = ("Instructions", "Sales & fees", "Expenses", "Monthly P&L")
FILES = {
    "Instructions": "1_Instructions.csv",
    "Sales & fees": "2_Sales_and_fees.csv",
    "Expenses": "3_Expenses.csv",
    "Monthly P&L": "4_Monthly_P_and_L.csv",
}

SALES_SHEET = "'Sales & fees'"
EXPENSE_SHEET = "Expenses"

EXPENSE_CATEGORIES = (
    "Materials & supplies",
    "Packaging & shipping supplies",
    "Postage & labels",
    "Software & subscriptions",
    "Advertising off Etsy",
    "Home office & utilities share",
    "Mileage & travel",
    "Professional services",
    "Bank & payment fees",
    "Other",
)


def instructions_rows() -> list[list[str]]:
    return [
        ["Monthly books for a small Etsy/shop seller", "DRAFT — NOT APPROVED"],
        ["", ""],
        [
            "What this workbook does",
            "Enter sales and fees, log expenses, and see a monthly profit and loss "
            "— without QuickBooks.",
        ],
        ["Works in", "Google Sheets and Excel. Nothing to install."],
        ["Tabs", "Instructions, Sales & fees, Expenses, Monthly P&L. That is all four."],
        ["", ""],
        ["Step 1", "Open the Sales & fees tab. One row per order."],
        [
            "Step 2",
            "Paste Date, Order ID, gross sales, discounts, shipping charged, sales tax "
            "collected, fees, and refunds. Net to bank fills itself in.",
        ],
        ["Step 3", "Open the Expenses tab. One row per purchase. Pick a category from the list."],
        [
            "Step 4",
            "Open the Monthly P&L tab and type the first day of the month in cell B2 "
            "(for example 2026-01-01). Every total updates.",
        ],
        ["", ""],
        [
            "Dates",
            "Use real dates, not text. Type 2026-01-31 or use your local date format "
            "consistently.",
        ],
        [
            "Sales tax collected",
            "Tracked as pass-through money. It is held for the state, so it is not "
            "counted as profit.",
        ],
        [
            "Fees",
            "Marketplace fees, payment processing, and on-platform ads live on the "
            "Sales & fees tab so each order shows what it really paid out.",
        ],
        [
            "Expenses",
            "Off-platform costs live on the Expenses tab. Keep the category spelling "
            "identical to the Monthly P&L rows so the totals find them.",
        ],
        [
            "Rows run out?",
            "Copy the last row down. The formula in the Net to bank column copies with it.",
        ],
        [
            "Formula shows as text?",
            "Some CSV imports paste formulas as plain text. Retype the equals sign in "
            "that cell and it will calculate.",
        ],
        ["", ""],
        [
            "Not tax advice",
            "This is a bookkeeping worksheet, not tax, legal, or accounting advice, and "
            "it is not designed or reviewed by a CPA. Check your own numbers and ask a "
            "professional about your return.",
        ],
        [
            "Status",
            "NOT APPROVED draft. No reviews, no bestseller claim, no comparison to any "
            "other shop's product, and no sales numbers.",
        ],
        ["", ""],
        ["Expense categories", "Type these exactly on the Expenses tab"],
        *[[category, ""] for category in EXPENSE_CATEGORIES],
    ]


def sales_rows() -> list[list[str]]:
    header = [
        "Date",
        "Order ID",
        "Channel",
        "Gross sales",
        "Discounts",
        "Shipping charged to buyer",
        "Sales tax collected",
        "Marketplace fees",
        "Payment processing fees",
        "Ads fees (on platform)",
        "Refunds",
        "Net to bank",
    ]
    rows = [header]
    for line in range(2, DATA_ROWS + 2):
        formula = (
            f'=IF($A{line}="","",'
            f"D{line}-E{line}+F{line}+G{line}-H{line}-I{line}-J{line}-K{line})"
        )
        rows.append(["", "", "", "", "", "", "", "", "", "", "", formula])
    return rows


def expense_rows() -> list[list[str]]:
    header = [
        "Date",
        "Vendor",
        "Category",
        "Description",
        "Amount",
        "Payment method",
        "Notes",
    ]
    rows = [header]
    rows.extend([""] * len(header) for _ in range(DATA_ROWS))
    return rows


def _sales_sum(column: str) -> str:
    return (
        f"=SUMIFS({SALES_SHEET}!${column}:${column},"
        f'{SALES_SHEET}!$A:$A,">="&$B$2,'
        f'{SALES_SHEET}!$A:$A,"<="&$B$3)'
    )


def _expense_sum(label_cell: str) -> str:
    return (
        f"=SUMIFS({EXPENSE_SHEET}!$E:$E,"
        f'{EXPENSE_SHEET}!$A:$A,">="&$B$2,'
        f'{EXPENSE_SHEET}!$A:$A,"<="&$B$3,'
        f"{EXPENSE_SHEET}!$C:$C,${label_cell})"
    )


def profit_rows() -> list[list[str]]:
    """Monthly P&L. Row numbers are fixed so the formulas stay readable."""
    rows: list[list[str]] = []
    rows.append(["Monthly P&L", "DRAFT — NOT APPROVED", ""])  # row 1
    rows.append(["Month starts on", "2026-01-01", "Type the first day of the month"])  # row 2
    rows.append(["Month ends on", "=EOMONTH($B$2,0)", "Fills itself in"])  # row 3
    rows.append(["", "", ""])  # row 4

    rows.append(["Money in", "", ""])  # row 5
    rows.append(["Gross sales", _sales_sum("D"), "From Sales & fees"])  # row 6
    rows.append(["Discounts", _sales_sum("E"), "From Sales & fees"])  # row 7
    rows.append(["Refunds", _sales_sum("K"), "From Sales & fees"])  # row 8
    rows.append(["Net revenue", "=B6-B7-B8", "Gross sales less discounts and refunds"])  # row 9
    rows.append(["Shipping charged to buyers", _sales_sum("F"), "Counted as income"])  # row 10
    rows.append(
        [
            "Sales tax collected",
            _sales_sum("G"),
            "Pass-through — held for the state, not profit",
        ]
    )  # row 11
    rows.append(["", "", ""])  # row 12

    rows.append(["Selling fees", "", ""])  # row 13
    rows.append(["Marketplace fees", _sales_sum("H"), "From Sales & fees"])  # row 14
    rows.append(["Payment processing fees", _sales_sum("I"), "From Sales & fees"])  # row 15
    rows.append(["Ads fees (on platform)", _sales_sum("J"), "From Sales & fees"])  # row 16
    rows.append(["Total selling fees", "=SUM(B14:B16)", ""])  # row 17
    rows.append(["", "", ""])  # row 18

    rows.append(["Expenses", "", "Category spelling must match the Expenses tab"])  # row 19
    first_category_row = 20
    for offset, category in enumerate(EXPENSE_CATEGORIES):
        line = first_category_row + offset
        rows.append([category, _expense_sum(f"A{line}"), "From Expenses"])
    last_category_row = first_category_row + len(EXPENSE_CATEGORIES) - 1
    total_expense_row = last_category_row + 1
    rows.append(
        [
            "Total expenses",
            f"=SUM(B{first_category_row}:B{last_category_row})",
            "",
        ]
    )  # row 30
    rows.append(["", "", ""])  # row 31

    profit_row = total_expense_row + 2
    rows.append(
        [
            "Profit before tax",
            f"=B9+B10-B17-B{total_expense_row}",
            "Net revenue plus shipping, less fees and expenses",
        ]
    )  # row 32
    rows.append(["Set-aside rate", "0.25", "Your own guess, not tax advice"])  # row 33
    rows.append(
        [
            "Money to set aside",
            f'=IF(B{profit_row}>0,B{profit_row}*B{profit_row + 1},0)',
            "Estimate only",
        ]
    )  # row 34
    rows.append(
        [
            "Left after set-aside",
            f"=B{profit_row}-B{profit_row + 2}",
            "",
        ]
    )  # row 35
    rows.append(["", "", ""])
    rows.append(
        [
            "Not tax advice",
            "",
            "Bookkeeping worksheet only. Not designed or reviewed by a CPA.",
        ]
    )
    return rows


def write_tabs(out_dir: Path = OUT_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "Instructions": instructions_rows(),
        "Sales & fees": sales_rows(),
        "Expenses": expense_rows(),
        "Monthly P&L": profit_rows(),
    }
    written: list[Path] = []
    for tab in TABS:
        path = out_dir / FILES[tab]
        with path.open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerows(tables[tab])
        written.append(path)
    return written


if __name__ == "__main__":
    for path in write_tabs():
        print(path)
