import unittest, json
from datetime import date
from decimal import Decimal
from ledger import parse_csv, total, render_report
from ledger.summary import totals_by_currency

DATA = """account,amount,day,status,currency
a,1.20,2026-01-01,posted,USD
b,2.30,2026-01-02,pending,USD
c,5.00,2026-01-03,posted,EUR
d,1.50,2026-01-04,posted,usd
"""


class TestCurrencyField(unittest.TestCase):
    def test_default_usd(self):
        e = parse_csv("""account,amount,day,status
a,1.00,2026-01-01,posted""" )[0]
        self.assertEqual(e.currency, "USD")

    def test_currency_normalized_uppercase(self):
        e = parse_csv("""account,amount,day,status,currency
a,1.00,2026-01-01,posted,eur""")[0]
        self.assertEqual(e.currency, "EUR")

    def test_invalid_code_too_short(self):
        with self.assertRaises(ValueError):
            parse_csv("""account,amount,day,status,currency
a,1.00,2026-01-01,posted,US""")

    def test_invalid_code_too_long(self):
        with self.assertRaises(ValueError):
            parse_csv("""account,amount,day,status,currency
a,1.00,2026-01-01,posted,XXXX""")

    def test_invalid_code_non_alpha(self):
        with self.assertRaises(ValueError):
            parse_csv("""account,amount,day,status,currency
a,1.00,2026-01-01,posted,U1D""")

    def test_invalid_code_empty(self):
        with self.assertRaises(ValueError):
            parse_csv("""account,amount,day,status,currency
a,1.00,2026-01-01,posted,""")

    def test_legacy_total_unchanged(self):
        self.assertEqual(total(parse_csv(DATA)), Decimal("10.00"))


class TestTotalsByCurrency(unittest.TestCase):
    def test_all_entries(self):
        t = totals_by_currency(parse_csv(DATA))
        self.assertEqual(t["USD"], Decimal("2.70"))
        self.assertEqual(t["EUR"], Decimal("5.00"))
        self.assertEqual(sorted(t), ["EUR", "USD"])

    def test_excludes_pending_by_default(self):
        t = totals_by_currency(parse_csv(DATA), include_pending=False)
        self.assertEqual(t["USD"], Decimal("2.70"))
        self.assertEqual(t["EUR"], Decimal("5.00"))

    def test_include_pending(self):
        t = totals_by_currency(parse_csv(DATA), include_pending=True)
        self.assertEqual(t["USD"], Decimal("5.00"))
        self.assertEqual(t["EUR"], Decimal("5.00"))

    def test_start_bound_inclusive(self):
        t = totals_by_currency(parse_csv(DATA), start=date(2026, 1, 3))
        self.assertEqual(t["EUR"], Decimal("5.00"))
        self.assertEqual(t["USD"], Decimal("1.50"))

    def test_end_bound_inclusive(self):
        t = totals_by_currency(parse_csv(DATA), end=date(2026, 1, 2))
        self.assertEqual(t["USD"], Decimal("1.20"))
        self.assertNotIn("EUR", t)

    def test_reversed_bounds_raise(self):
        with self.assertRaises(ValueError):
            totals_by_currency(parse_csv(DATA), start=date(2026, 1, 5), end=date(2026, 1, 1))

    def test_empty(self):
        self.assertEqual(totals_by_currency([]), {})

    def test_no_matching(self):
        t = totals_by_currency(parse_csv(DATA), start=date(2026, 2, 1), end=date(2026, 2, 28))
        self.assertEqual(t, {})


class TestRenderReport(unittest.TestCase):
    def test_legacy_unchanged(self):
        r = json.loads(render_report(DATA))
        self.assertEqual(r["total"], "10.00")
        self.assertEqual(list(r.keys()), ["total"])

    def test_by_currency(self):
        r = json.loads(render_report(DATA, by_currency=True))
        self.assertEqual(r["totals"]["EUR"], "5.00")
        self.assertEqual(r["totals"]["USD"], "2.70")
        self.assertEqual(sorted(r["totals"]), ["EUR", "USD"])

    def test_by_currency_with_dates(self):
        r = json.loads(render_report(DATA, by_currency=True, start=date(2026, 1, 3)))
        self.assertEqual(r["totals"]["EUR"], "5.00")
        self.assertEqual(r["totals"]["USD"], "1.50")

    def test_by_currency_excludes_pending(self):
        r = json.loads(render_report(DATA, by_currency=True))
        self.assertEqual(r["totals"]["USD"], "2.70")


if __name__ == "__main__":
    unittest.main()
