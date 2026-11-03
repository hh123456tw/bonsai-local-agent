import unittest
from datetime import date
from decimal import Decimal
from ledger import parse_csv, total, render_report, totals_by_currency

DATA = """account,amount,day,status,currency
a,1.20,2026-01-01,posted,usd
b,2.30,2026-01-02,pending,EUR
c,0.50,2026-01-03,posted,EUR
d,1.00,2026-01-04,posted,eur
"""

class EntryCurrencyDefault(unittest.TestCase):
    def test_default_is_usd(self):
        h = "account,amount,day" + chr(10)
        entry = parse_csv(h + "a,1.00,2026-01-01")[0]
        self.assertEqual(entry.currency, "USD")

    def test_entry_currency_can_be_set(self):
        from ledger.models import Entry
        e = Entry("x", Decimal("1"), date(2026, 1, 1), "pending", "EUR")
        self.assertEqual(e.currency, "EUR")

class ParseCurrency(unittest.TestCase):
    def test_missing_column_defaults_to_usd(self):
        h = "account,amount,day" + chr(10)
        entries = parse_csv(h + "a,1.00,2026-01-01")
        self.assertEqual([e.currency for e in entries], ["USD"])

    def test_lowercase_normalized(self):
        h = "account,amount,day,currency" + chr(10)
        entries = parse_csv(h + "a,1.00,2026-01-01,usd")
        self.assertEqual(entries[0].currency, "USD")

    def test_mixed_case_normalized(self):
        h = "account,amount,day,currency" + chr(10)
        entries = parse_csv(h + "a,1.00,2026-01-01,eUr")
        self.assertEqual(entries[0].currency, "EUR")

    def test_invalid_length_raises(self):
        with self.assertRaises(ValueError):
            h = "account,amount,day,currency" + chr(10)
            parse_csv(h + "a,1.00,2026-01-01,us")
        with self.assertRaises(ValueError):
            h = "account,amount,day,currency" + chr(10)
            parse_csv(h + "a,1.00,2026-01-01,usd1")

    def test_non_ascii_raises(self):
        with self.assertRaises(ValueError):
            h = "account,amount,day,currency" + chr(10)
            parse_csv(h + "a,1.00,2026-01-01,u$")

class TotalsByCurrency(unittest.TestCase):
    def setUp(self):
        self.entries = parse_csv(DATA)

    def test_sums_by_currency_posted_only(self):
        t = totals_by_currency(self.entries)
        self.assertEqual(t["USD"], Decimal("1.20"))
        self.assertEqual(t["EUR"], Decimal("1.50"))
        self.assertEqual(set(t), {"USD", "EUR"})

    def test_excludes_pending_by_default(self):
        t = totals_by_currency(self.entries, include_pending=True)
        self.assertEqual(t["EUR"], Decimal("3.80"))
        self.assertEqual(t["USD"], Decimal("1.20"))

    def test_inclusive_date_bounds(self):
        t = totals_by_currency(self.entries, start=date(2026, 1, 2), end=date(2026, 1, 3))
        self.assertEqual(t["EUR"], Decimal("0.50"))
        self.assertNotIn("USD", t)

    def test_single_bound_inclusive(self):
        t = totals_by_currency(self.entries, start=date(2026, 1, 2))
        self.assertEqual(t["EUR"], Decimal("1.50"))
        self.assertNotIn("USD", t)
        t = totals_by_currency(self.entries, end=date(2026, 1, 2))
        self.assertEqual(t["USD"], Decimal("1.20"))
        self.assertNotIn("EUR", t)

    def test_reversed_bounds_raise(self):
        with self.assertRaises(ValueError):
            totals_by_currency(self.entries, start=date(2026, 1, 5), end=date(2026, 1, 1))

    def test_no_bounds_returns_all(self):
        t = totals_by_currency(self.entries, start=None, end=None)
        self.assertEqual(t["EUR"], Decimal("1.50"))

    def test_empty_entries(self):
        self.assertEqual(totals_by_currency([]), {})

    def test_total_unchanged(self):
        self.assertEqual(total(self.entries), Decimal("5.00"))

class RenderReportCurrency(unittest.TestCase):
    def test_legacy_unchanged(self):
        import json
        s = render_report(DATA)
        self.assertEqual(json.loads(s), {"total": "5.00"})

    def test_by_currency_format(self):
        import json
        s = render_report(DATA, by_currency=True)
        d = json.loads(s)
        self.assertEqual(d, {"totals": {"EUR": "1.50", "USD": "1.20"}})

    def test_by_currency_with_filters(self):
        import json
        s = render_report(DATA, by_currency=True, start=date(2026, 1, 2), end=date(2026, 1, 3))
        d = json.loads(s)
        self.assertEqual(d, {"totals": {"EUR": "0.50"}})

    def test_by_currency_excludes_pending(self):
        import json
        s = render_report(DATA, by_currency=True)
        d = json.loads(s)
        self.assertEqual(d["totals"]["EUR"], "1.50")

if __name__ == "__main__":
    unittest.main()
