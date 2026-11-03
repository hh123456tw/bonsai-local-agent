import unittest
from datetime import date
from decimal import Decimal
from ledger import parse_csv, total, render_report
from ledger.models import Entry
from ledger.summary import totals_by_currency
import json

DATA = "account,amount,day,status,currency
a,1.20,2026-01-01,posted,USD
b,2.30,2026-01-02,pending,EUR
"

class EntryCurrencyTests(unittest.TestCase):
    def test_entry_currency_defaults_to_usd(self):
        entry = Entry("a", Decimal("1"), date(2026, 1, 1))
        self.assertEqual(entry.currency, "USD")

    def test_parse_defaults_to_usd_when_column_missing(self):
        entries = parse_csv("account,amount,day
x,1.00,2026-01-01
")
        self.assertEqual(entries[0].currency, "USD")

    def test_parse_normalizes_lowercase_and_whitespace(self):
        entries = parse_csv("account,amount,day,currency
x,1.00,2026-01-01, eur 
")
        self.assertEqual(entries[0].currency, "EUR")

    def test_parse_rejects_invalid_currencies(self):
        for bad in ("", "US", "USDX", "us1", "u$D", "123"):
            with self.assertRaises(ValueError):
                parse_csv("account,amount,day,currency
x,1.00,2026-01-01,%s
" % bad)

    def test_parse_preserves_legacy_columns(self):
        entries = parse_csv("account,amount,day,status
a,1.20,2026-01-01,posted
b,2.30,2026-01-02,pending
")
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].status, "posted")
        self.assertEqual(entries[1].status, "pending")

class TotalsByCurrencyTests(unittest.TestCase):
    def _entries(self):
        return [
            Entry("a", Decimal("1.20"), date(2026, 1, 1), "posted", "USD"),
            Entry("b", Decimal("2.30"), date(2026, 1, 2), "pending", "EUR"),
            Entry("c", Decimal("0.50"), date(2026, 1, 3), "posted", "EUR"),
            Entry("d", Decimal("0.75"), date(2026, 1, 4), "pending", "USD"),
        ]

    def test_sums_per_currency_excludes_pending_by_default(self):
        result = totals_by_currency(self._entries())
        self.assertEqual(result["USD"], Decimal("1.20"))
        self.assertEqual(result["EUR"], Decimal("0.50"))
        self.assertEqual(set(result), {"USD", "EUR"})

    def test_include_pending(self):
        result = totals_by_currency(self._entries(), include_pending=True)
        self.assertEqual(result["USD"], Decimal("1.95"))
        self.assertEqual(result["EUR"], Decimal("2.80"))

    def test_date_bounds_are_inclusive(self):
        result = totals_by_currency(self._entries(), start=date(2026, 1, 2), end=date(2026, 1, 3))
        self.assertEqual(result["EUR"], Decimal("0.50"))
        self.assertNotIn("USD", result)

    def test_single_bound_start_only(self):
        result = totals_by_currency(self._entries(), start=date(2026, 1, 3))
        self.assertEqual(result["EUR"], Decimal("0.50"))
        self.assertNotIn("USD", result)

    def test_single_bound_end_only(self):
        result = totals_by_currency(self._entries(), end=date(2026, 1, 2))
        self.assertEqual(result["USD"], Decimal("1.20"))
        self.assertEqual(result["EUR"], Decimal("2.30"))

    def test_reversed_bounds_raise_value_error(self):
        with self.assertRaises(ValueError):
            totals_by_currency(self._entries(), start=date(2026, 1, 5), end=date(2026, 1, 1))

    def test_empty_entries_returns_empty_dict(self):
        self.assertEqual(totals_by_currency([]), {})

class RenderReportTests(unittest.TestCase):
    def test_legacy_default_json_unchanged(self):
        expected = json.dumps({"total": "3.50"}, sort_keys=True)
        self.assertEqual(render_report(DATA), expected)

    def test_by_currency_format(self):
        report = render_report(DATA, by_currency=True)
        expected = json.dumps({"totals": {"EUR": "2.30", "USD": "1.20"}}, sort_keys=True)
        self.assertEqual(report, expected)

    def test_by_currency_applies_date_filters(self):
        report = render_report(DATA, by_currency=True, start=date(2026, 1, 2), end=date(2026, 1, 2))
        expected = json.dumps({"totals": {"EUR": "2.30"}}, sort_keys=True)
        self.assertEqual(report, expected)

    def test_by_currency_excludes_pending_by_default(self):
        data = "account,amount,day,status,currency
a,1.00,2026-01-01,posted,USD
b,2.00,2026-01-02,pending,USD
"
        expected = json.dumps({"totals": {"USD": "1.00"}}, sort_keys=True)
        self.assertEqual(render_report(data, by_currency=True), expected)

    def test_by_currency_reversed_bounds_raise(self):
        with self.assertRaises(ValueError):
            render_report(DATA, by_currency=True, start=date(2026, 1, 5), end=date(2026, 1, 1))

    def test_totals_by_currency_allows_pending(self):
        entries = parse_csv("account,amount,day,status,currency
a,1.00,2026-01-01,posted,USD
b,2.00,2026-01-02,pending,USD
")
        self.assertEqual(totals_by_currency(entries, include_pending=True)["USD"], Decimal("3.00"))

if __name__ == "__main__":
    unittest.main()
