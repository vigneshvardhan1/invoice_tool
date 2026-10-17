"""Tests for the deterministic field checks.

Run: pytest -q

These need no API key and no network. They cover the logic that decides whether
a row is trusted, so they must not be skipped.
"""

from checks import (
    amounts_in,
    appears,
    is_last_amount,
    is_line,
    normalize,
    validate_row,
)

# Real text shape from the sample invoices (two-column, values before labels).
SAMPLE_TEXT = """INVOICE
# 12798
SuperStore
Bill To
:
Sarah Foster
Ship To
:
London, England,
United Kingdom
May 03 2012
Standard Class
$6,522.28
Date
:
Item
Quantity
Rate
Amount
Okidata Inkjet, Wireless
5
$1,413.45
$7,067.25
Subtotal
:
$7,067.25
Discount (10%)
:
$706.73
Shipping
:
$161.76
Total
:
$6,522.28
Notes
:
Thanks for your business!
"""

GOOD_ROW = {
    "customer_name": "Sarah Foster",
    "bill_no": "12798",
    "date": "May 03 2012",
    "total": 6522.28,
}


# --- normalize ---

def test_normalize_collapses_whitespace():
    assert normalize("a\n\n  b\tc ") == "a b c"


def test_normalize_strips_edges():
    assert normalize("  x  ") == "x"


# --- amounts_in ---

def test_amounts_in_finds_all_amounts():
    assert amounts_in(SAMPLE_TEXT) == {6522.28, 1413.45, 7067.25, 706.73, 161.76}


def test_grand_total_is_the_last_amount_on_the_page():
    """Mirrors the real PDFs: Balance Due repeats at the top, Total closes the doc."""
    amounts = [
        float(m.replace("$", "").replace(",", ""))
        for m in __import__("re").findall(r"\$[\d,]+\.\d{2}", SAMPLE_TEXT)
    ]
    assert amounts[0] == amounts[-1] == 6522.28


def test_amounts_in_handles_thousands_commas():
    assert amounts_in("Total: $1,234,567.89") == {1234567.89}


def test_amounts_in_empty_when_no_amounts():
    assert amounts_in("nothing here") == set()


def test_amounts_in_ignores_bare_numbers():
    # No $ prefix -> not an amount, so never trusted as a total
    assert amounts_in("total 6522.28") == set()


# --- appears ---

def test_appears_exact():
    assert appears("Sarah Foster", SAMPLE_TEXT) is True


def test_appears_is_case_insensitive():
    assert appears("SARAH FOSTER", SAMPLE_TEXT) is True


def test_appears_tolerates_line_wrapping():
    # wraps across lines with no punctuation in between
    assert appears("England United", "England\nUnited Kingdom") is True


def test_appears_does_not_strip_punctuation():
    # normalize collapses whitespace only; commas stay significant
    assert appears("London England", SAMPLE_TEXT) is False


def test_appears_rejects_absent_value():
    assert appears("John Smith", SAMPLE_TEXT) is False


# --- is_line ---

def test_is_line_matches_hash_prefix():
    assert is_line("12798", SAMPLE_TEXT) is True


def test_is_line_matches_without_hash():
    assert is_line("12798", "# 12798") is True


def test_is_line_rejects_substring_of_longer_number():
    # The reason this check exists: '1' is inside '12798'
    assert is_line("1", SAMPLE_TEXT) is False


def test_is_line_rejects_number_inside_amount():
    # '1' is inside '$1,413.45'
    assert is_line("1", SAMPLE_TEXT) is False


def test_is_line_rejects_absent_value():
    assert is_line("99999", SAMPLE_TEXT) is False


# --- validate_row ---

def test_validate_row_accepts_good_extraction():
    assert validate_row(GOOD_ROW, SAMPLE_TEXT) is None


def test_validate_row_rejects_wrong_total():
    bad = {**GOOD_ROW, "total": 999.99}
    assert "total" in validate_row(bad, SAMPLE_TEXT)


def test_validate_row_rejects_wrong_name():
    bad = {**GOOD_ROW, "customer_name": "John Smith"}
    assert "customer_name" in validate_row(bad, SAMPLE_TEXT)


def test_validate_row_rejects_wrong_date():
    bad = {**GOOD_ROW, "date": "Dec 25 1999"}
    assert "date" in validate_row(bad, SAMPLE_TEXT)


def test_validate_row_rejects_wrong_bill_no():
    bad = {**GOOD_ROW, "bill_no": "1"}
    assert "bill_no" in validate_row(bad, SAMPLE_TEXT)


def test_validate_row_rejects_subtotal_masquerading_as_total():
    """Subtotal 7067.25 is on the page, but it is not the grand total."""
    bad = {**GOOD_ROW, "total": 7067.25}
    assert validate_row(bad, SAMPLE_TEXT) is not None


def test_validate_row_rejects_shipping_masquerading_as_total():
    bad = {**GOOD_ROW, "total": 161.76}
    assert validate_row(bad, SAMPLE_TEXT) is not None


def test_validate_row_rejects_balance_due_when_due_differs():
    """Balance Due printed near the top is NOT the total when they differ."""
    text = SAMPLE_TEXT.replace("$6,522.28\nDate", "$5,000.00\nDate")
    row = {**GOOD_ROW, "total": 5000.00}
    assert validate_row(row, text) is not None
    # the real total is still accepted
    assert validate_row(GOOD_ROW, text) is None


# --- is_last_amount ---

def test_is_last_amount_accepts_final_figure():
    assert is_last_amount(6522.28, SAMPLE_TEXT) is True


def test_is_last_amount_rejects_earlier_figure():
    assert is_last_amount(1413.45, SAMPLE_TEXT) is False


def test_is_last_amount_rejects_when_no_amounts():
    assert is_last_amount(6522.28, "no figures here") is False


def test_validate_row_reports_missing_field():
    # CHECKS order is bill_no, date, customer_name, total, so `date` reports first
    partial = {"bill_no": "12798", "total": 6522.28}
    assert "date missing" in validate_row(partial, SAMPLE_TEXT)


def test_validate_row_reports_missing_customer_name():
    partial = {"bill_no": "12798", "date": "May 03 2012", "total": 6522.28}
    assert "customer_name missing" in validate_row(partial, SAMPLE_TEXT)


def test_validate_row_reports_empty_row():
    assert validate_row({}, SAMPLE_TEXT) is not None
