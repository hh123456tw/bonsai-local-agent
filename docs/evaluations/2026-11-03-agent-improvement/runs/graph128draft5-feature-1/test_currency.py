import unittest
from datetime import date
from decimal import Decimal

from ledger import (
    Entry,
    parse_csv,
    normalize_currency,
    render_report,
    totals_by_currency,
    total,
)


DATA = """account,amount,day,status,currency
a,1.20,2026-01-01,posted,USD
b,2.30,2026-01-02,pending,USD
c,5.00,2026-01-03,posted,EUR
d,0.50,2026-01-04,posted,eur
"""

# Two-row dataset matching the legacy contract (total 3.50).
LEGACY_DATA = "account,amount,day,status\na,1.20,2026-01-01,posted\nb,2.30,2026-01-02,pending\n"


class EntryCurrencyTests(unittest.TestCase):
    def test_entry_currency_defaults_to_usd(self):
        entry = Entry("a", Decimal("1"), date(2026, 1, 1))
        self.assertEqual(entry.currency, "USD")

    def test_entry_currency_explicit(self):
        entry = Entry("a", Decimal("1"), date(2026, 1, 1), currency="EUR")
        self.assertEqual(entry.currency, "EUR")


class NormalizeCurrencyTests(unittest.TestCase):
    def test_none_defaults_to_usd(self):
        self.assertEqual(normalize_currency(None), "USD")

    def test_lowercase_normalized(self):
        self.assertEqual(normalize_currency("usd"), "USD")

    def test_mixed_case_normalized(self):
        self.assertEqual(normalize_currency("EuR"), "EUR")

    def test_surrounding_whitespace_stripped(self):
        self.assertEqual(normalize_currency("  usd  "), "USD")

    def test_invalid_length_short(self):
        with self.assertRaises(ValueError):
            normalize_currency("US")

    def test_invalid_length_long(self):
        with self.assertRaises(ValueError):
            normalize_currency("EURR")

    def test_empty_string_invalid(self):
        with self.assertRaises(ValueError):
            normalize_currency("")

    def test_digit_invalid(self):
        with self.assertRaises(ValueError):
            normalize_currency("EU1")

    def test_symbol_invalid(self):
        with self.assertRaises(ValueError):
            normalize_currency("EUR$")

    def test_non_ascii_invalid(self):
        with self.assertRaises(ValueError):
            normalize_currency("\u20acUR")


class ParseCurrencyTests(unittest.TestCase):
    def test_missing_column_defaults_to_usd(self):
        rows = parse_csv("account,amount,day,status\na,1.00,2026-01-01,posted\n")
        self.assertEqual(rows[0].currency, "USD")

    def test_currency_column_parsed_and_normalized(self):
        rows = parse_csv(DATA)
        self.assertEqual([r.currency for r in rows], ["USD", "USD", "EUR", "EUR"])

    def test_invalid_currency_raises_on_parse(self):
        with self.assertRaises(ValueError):
            parse_csv("account,amount,day,status,currency\na,1.00,2026-01-01,posted,X\n")


class TotalsByCurrencyTests(unittest.TestCase):
    def setUp(self):
        self.entries = parse_csv(DATA)

    def test_returns_dict(self):
        result = totals_by_currency(self.entries)
        self.assertIsInstance(result, dict)

    def test_sums_per_currency_posted_only_default(self):
        result = totals_by_currency(self.entries)
        self.assertEqual(result["USD"], Decimal("1.20"))
        self.assertEqual(result["EUR"], Decimal("5.50"))

    def test_include_pending_includes_all_statuses(self):
        result = totals_by_currency(self.entries, include_pending=True)
        self.assertEqual(result["USD"], Decimal("3.50"))
        self.assertEqual(result["EUR"], Decimal("5.50"))

    def test_start_end_bounds_inclusive(self):
        # 2026-01-02..2026-01-03 posted only -> c (EUR 5.00)
        result = totals_by_currency(self.entries, start=date(2026, 1, 2), end=date(2026, 1, 3))
        self.assertEqual(result, {"EUR": Decimal("5.00")})

    def test_single_day_bound_inclusive(self):
        result = totals_by_currency(self.entries, start=date(2026, 1, 1), end=date(2026, 1, 1))
        self.assertEqual(result, {"USD": Decimal("1.20")})

    def test_reversed_bounds_raise(self):
        with self.assertRaises(ValueError):
            totals_by_currency(self.entries, start=date(2026, 1, 10), end=date(2026, 1, 1))

    def test_no_entries_returns_empty(self):
        self.assertEqual(totals_by_currency([]), {})


class RenderReportCurrencyTests(unittest.TestCase):
    def test_legacy_render_report_unchanged(self):
        from json import loads

        self.assertEqual(loads(render_report(LEGACY_DATA)), {"total": "3.50"})

    def test_by_currency_default_excludes_pending(self):
        from json import loads

        report = loads(render_report(DATA, by_currency=True))
        self.assertEqual(report, {"totals": {"EUR": "5.50", "USD": "1.20"}})

    def test_by_currency_with_date_filter(self):
        from json import loads

        report = loads(
            render_report(DATA, by_currency=True, start=date(2026, 1, 2), end=date(2026, 1, 3))
        )
        self.assertEqual(report, {"totals": {"EUR": "5.00"}})

    def test_by_currency_amounts_formatted_two_decimals(self):
        from json import loads

        report = loads(render_report(DATA, by_currency=True))
        for value in report["totals"].values():
            self.assertEqual(len(value.split(".")), 2)
            self.assertEqual(len(value.split(".")[1]), 2)


if __name__ == "__main__":
    unittest.main()
