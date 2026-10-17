"""Deterministic field checks: does each extracted value actually appear in the
source PDF text?

These are the guard rails around the LLM. They are pure functions on purpose —
no model, no network — so they can be tested in milliseconds.
"""

import re


def normalize(s: str) -> str:
    """Collapse runs of whitespace so PDF line-wrapping doesn't break matching."""
    return re.sub(r"\s+", " ", s).strip()


def amounts_in(text: str) -> set:
    """Every $-prefixed amount in the text, as floats."""
    return {
        float(m.replace("$", "").replace(",", ""))
        for m in re.findall(r"\$[\d,]+\.\d{2}", text)
    }


def appears(value, text: str) -> bool:
    """True if value occurs in text, ignoring case and whitespace differences."""
    return normalize(str(value)).casefold() in normalize(text).casefold()


def is_line(value, text: str) -> bool:
    """True if a whole line equals value, optionally prefixed with '#'.

    Needed for bill_no: a bare substring test would match '1' inside '12798'
    or inside '$1,413.45', so short invoice numbers would pass unverified.
    """
    pattern = r"^\s*#?\s*" + re.escape(str(value)) + r"\s*$"
    return bool(re.search(pattern, text, re.MULTILINE))


def is_last_amount(value, text: str) -> bool:
    """True if value is the final dollar amount in the document.

    Membership alone is far too weak: subtotal, discount, shipping and every
    line item are all amounts, so any of them would pass a `total in amounts`
    test. On an invoice the grand total is the last figure printed before the
    footer, so require exactly that.
    """
    ordered = [
        float(m.replace("$", "").replace(",", ""))
        for m in re.findall(r"\$[\d,]+\.\d{2}", text)
    ]
    return bool(ordered) and ordered[-1] == value


CHECKS = [
    ("bill_no", is_line),
    ("date", appears),
    ("customer_name", appears),
    ("total", is_last_amount),
]


def validate_row(row: dict, text: str):
    """Return None if every field checks out, else a reason string."""
    if not row:
        return "no row"
    for field, check in CHECKS:
        if field not in row:
            return f"{field} missing from row"
        if not check(row[field], text):
            return f"{field} {row[field]!r} not found in pdf text"
    return None
