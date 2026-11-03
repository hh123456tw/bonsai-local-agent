import unittest, json
from datetime import date
from decimal import Decimal
from ledger import parse_csv, total, render_report
from ledger.models import Entry
from ledger.summary import totals_by_currency

DATA = "account,amount,day,status,currency" + chr(10) + "a,1.20,2026-01-01,posted,USD" + chr(10) + "b,2.30,2026-01-02,pending,EUR" + chr(10) + "c,5.00,2026-01-03,posted,GBP" + chr(10)

class TestEntryCurrency(unittest.TestCase):
    def test_default_usd(self):
        e = Entry(chr(120), Decimal("1"), date(2026, 1, 1))
        self.assertEqual(e.currency, "USD")
    def test_explicit_currency(self):
        e = Entry("x", Decimal("1"), date(2026, 1, 1), "posted", "EUR")
        self.assertEqual(e.currency, "EUR")

class TestParseCurrency(unittest.TestCase):
    def test_optional_column_defaults_usd(self):
        rows = parse_csv("account,amount,day,status" + chr(10) + "a,1.00,2026-01-01,posted" + chr(10))
        self.assertEqual(rows[0].currency, "USD")
    def test_lowercase_normalized(self):
        rows = parse_csv(DATA)
        self.assertEqual(rows[2].currency, "GBP")
    def test_whitespace_and_mixed_case_normalized(self):
        rows = parse_csv("account,amount,day,status,currency" + chr(10) + "x,1.00,2026-01-01,posted, gbp " + chr(10))
        self.assertEqual(rows[0].currency, "GBP")
    def test_invalid_length_raises(self):
        with self.assertRaises(ValueError):
            parse_csv("account,amount,day,status,currency" + chr(10) + "x,1.00,2026-01-01,posted,US" + chr(10))
    def test_invalid_non_alpha_raises(self):
        for bad in ("U$D", "EU4"):
            with self.assertRaises(ValueError):
                parse_csv("account,amount,day,status,currency" + chr(10) + "x,1.00,2026-01-01,posted," + bad + chr(10))
    def test_legacy_data_still_parses(self):
        D = "account,amount,day,status" + chr(10) + "a,1.20,2026-01-01,posted" + chr(10) + "b,2.30,2026-01-02,pending" + chr(10)
        self.assertEqual(len(parse_csv(D)), 2)
        self.assertEqual([e.currency for e in parse_csv(D)], ["USD", "USD"])

class TestTotalsByCurrency(unittest.TestCase):
    def entries(self):
        return [
            Entry("a", Decimal("1.20"), date(2026, 1, 1), "posted", "USD"),
            Entry("b", Decimal("2.30"), date(2026, 1, 2), "pending", "EUR"),
            Entry("c", Decimal("5.00"), date(2026, 1, 3), "posted", "EUR"),
            Entry("d", Decimal("0.75"), date(2026, 1, 4), "pending", "USD"),
        ]
    def test_sums_by_currency_posted_only_default(self):
        r = totals_by_currency(self.entries())
        self.assertEqual(r, {"USD": Decimal("1.20"), "EUR": Decimal("5.00")})
    def test_include_pending(self):
        r = totals_by_currency(self.entries(), include_pending=True)
        self.assertEqual(r, {"USD": Decimal("1.95"), "EUR": Decimal("7.30")})
    def test_date_bounds_inclusive(self):
        r = totals_by_currency(self.entries(), start=date(2026, 1, 2), end=date(2026, 1, 3))
        self.assertEqual(r, {"EUR": Decimal("5.00")})
    def test_reversed_bounds_raise(self):
        with self.assertRaises(ValueError):
            totals_by_currency(self.entries(), start=date(2026, 1, 5), end=date(2026, 1, 1))
    def test_single_bound_ok(self):
        r = totals_by_currency(self.entries(), end=date(2026, 1, 2))
        self.assertEqual(r, {"USD": Decimal("1.20")})
    def test_empty(self):
        self.assertEqual(totals_by_currency([]), {})

class TestRenderReport(unittest.TestCase):
    def test_legacy_unchanged(self):
        D = "account,amount,day,status" + chr(10) + "a,1.20,2026-01-01,posted" + chr(10) + "b,2.30,2026-01-02,pending" + chr(10)
        self.assertEqual(json.loads(render_report(D)), {"total": "3.50"})
    def test_by_currency(self):
        r = json.loads(render_report(DATA, by_currency=True))
        self.assertEqual(r, {"totals": {"USD": "1.20", "GBP": "5.00"}})
    def test_by_currency_date_filter(self):
        r = json.loads(render_report(DATA, by_currency=True, start="2026-01-02", end="2026-01-03"))
        self.assertEqual(r, {"totals": {"GBP": "5.00"}})
    def test_by_currency_accepts_date_objects(self):
        r = json.loads(render_report(DATA, by_currency=True, start=date(2026, 1, 1), end=date(2026, 1, 1)))
        self.assertEqual(r, {"totals": {"USD": "1.20"}})
    def test_by_currency_rounding(self):
        r = json.loads(render_report(DATA, by_currency=True))
        self.assertEqual(r["totals"]["USD"], "1.20")
