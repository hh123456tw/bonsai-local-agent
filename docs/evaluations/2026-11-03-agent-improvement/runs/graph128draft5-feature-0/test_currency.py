import unittest, json
from datetime import date
from decimal import Decimal
from ledger import parse_csv, total, render_report
from ledger.summary import totals_by_currency
from ledger.models import Entry

DATA = "account,amount,day,status" + chr(10) + "a,1.20,2026-01-01,posted" + chr(10) + "b,2.30,2026-01-02,pending" + chr(10)

class CurrencyParseTests(unittest.TestCase):
    def test_default_currency_usd(self):
        entry = parse_csv("account,amount,day,status,currency" + chr(10) + "a,1.00,2026-01-01,posted" + chr(10))[0]
        self.assertEqual(entry.currency, "USD")

    def test_missing_currency_column_defaults_usd(self):
        entry = parse_csv(DATA)[0]
        self.assertEqual(entry.currency, "USD")

    def test_currency_normalized_uppercase(self):
        entry = parse_csv("account,amount,day,status,currency" + chr(10) + "x,5.00,2026-01-02,posted,usd" + chr(10))[0]
        self.assertEqual(entry.currency, "USD")

    def test_invalid_code_too_short(self):
        with self.assertRaises(ValueError):
            parse_csv("account,amount,day,status,currency" + chr(10) + "y,5.00,2026-01-02,posted,us" + chr(10))

    def test_invalid_code_too_long(self):
        with self.assertRaises(ValueError):
            parse_csv("account,amount,day,status,currency" + chr(10) + "y,5.00,2026-01-02,posted,usdx" + chr(10))

    def test_invalid_code_non_ascii(self):
        with self.assertRaises(ValueError):
            parse_csv("account,amount,day,status,currency" + chr(10) + "y,5.00,2026-01-02,posted,us" + chr(233) + chr(10))

    def test_invalid_code_empty(self):
        with self.assertRaises(ValueError):
            parse_csv("account,amount,day,status,currency" + chr(10) + "y,5.00,2026-01-02,posted," + chr(10))

    def test_invalid_code_digits(self):
        with self.assertRaises(ValueError):
            parse_csv("account,amount,day,status,currency" + chr(10) + "y,5.00,2026-01-02,posted,123" + chr(10))

class TotalsByCurrencyTests(unittest.TestCase):
    def make_entries(self):
        return [
            Entry("a", Decimal("1.20"), date(2026, 1, 1), "posted", "USD"),
            Entry("b", Decimal("2.30"), date(2026, 1, 2), "pending", "USD"),
            Entry("c", Decimal("1.50"), date(2026, 1, 2), "posted", "USD"),
            Entry("d", Decimal("4.00"), date(2026, 1, 3), "posted", "EUR"),
            Entry("e", Decimal("0.75"), date(2026, 1, 4), "posted", "GBP"),
        ]

    def test_sums_per_currency_posted_only(self):
        result = totals_by_currency(self.make_entries())
        self.assertEqual(result["USD"], Decimal("2.70"))
        self.assertEqual(result["EUR"], Decimal("4.00"))
        self.assertEqual(result["GBP"], Decimal("0.75"))

    def test_includes_all_statuses_when_requested(self):
        result = totals_by_currency(self.make_entries(), include_pending=True)
        self.assertEqual(result["USD"], Decimal("5.00"))
        self.assertEqual(result["EUR"], Decimal("4.00"))
        self.assertEqual(result["GBP"], Decimal("0.75"))

    def test_start_inclusive(self):
        result = totals_by_currency(self.make_entries(), start=date(2026, 1, 2))
        self.assertEqual(result["USD"], Decimal("1.50"))
        self.assertEqual(result["EUR"], Decimal("4.00"))
        self.assertEqual(result["GBP"], Decimal("0.75"))

    def test_end_inclusive(self):
        result = totals_by_currency(self.make_entries(), end=date(2026, 1, 2))
        self.assertEqual(result["USD"], Decimal("2.70"))
        self.assertNotIn("EUR", result)
        self.assertNotIn("GBP", result)

    def test_range_both_bounds_inclusive(self):
        result = totals_by_currency(self.make_entries(), start=date(2026, 1, 2), end=date(2026, 1, 3))
        self.assertEqual(result["USD"], Decimal("1.50"))
        self.assertEqual(result["EUR"], Decimal("4.00"))
        self.assertNotIn("GBP", result)

    def test_reversed_bounds_raise(self):
        with self.assertRaises(ValueError):
            totals_by_currency(self.make_entries(), start=date(2026, 1, 3), end=date(2026, 1, 1))

    def test_returns_dict(self):
        result = totals_by_currency(self.make_entries())
        self.assertIsInstance(result, dict)

    def test_no_entries_empty(self):
        self.assertEqual(totals_by_currency([]), {})

    def test_legacy_total_unchanged(self):
        entries = parse_csv(DATA)
        self.assertEqual(total(entries), Decimal("3.50"))

class RenderReportTests(unittest.TestCase):
    def test_legacy_unchanged(self):
        self.assertEqual(json.loads(render_report(DATA)), {"total": "3.50"})

    def test_by_currency(self):
        data = "account,amount,day,status,currency" + chr(10) + "a,1.20,2026-01-01,posted,USD" + chr(10) + "b,2.30,2026-01-02,posted,EUR" + chr(10)
        out = json.loads(render_report(data, by_currency=True))
        self.assertEqual(out, {"totals": {"EUR": "2.30", "USD": "1.20"}})

    def test_by_currency_with_date_filter(self):
        data = ("account,amount,day,status,currency" + chr(10) + "a,1.20,2026-01-01,posted,USD" + chr(10) + "b,2.30,2026-01-02,posted,USD" + chr(10) + "c,4.00,2026-01-03,posted,EUR" + chr(10))
        out = json.loads(render_report(data, by_currency=True, start="2026-01-02", end="2026-01-03"))
        self.assertEqual(out, {"totals": {"EUR": "4.00", "USD": "2.30"}})

    def test_by_currency_excludes_pending_by_default(self):
        data = ("account,amount,day,status,currency" + chr(10) + "a,1.20,2026-01-01,posted,USD" + chr(10) + "b,2.30,2026-01-02,pending,USD" + chr(10))
        out = json.loads(render_report(data, by_currency=True))
        self.assertEqual(out, {"totals": {"USD": "1.20"}})

    def test_by_currency_two_decimal_formatting(self):
        data = "account,amount,day,status,currency" + chr(10) + "a,1,2026-01-01,posted,USD" + chr(10)
        out = json.loads(render_report(data, by_currency=True))
        self.assertEqual(out, {"totals": {"USD": "1.00"}})

if __name__ == "__main__":
    unittest.main()
