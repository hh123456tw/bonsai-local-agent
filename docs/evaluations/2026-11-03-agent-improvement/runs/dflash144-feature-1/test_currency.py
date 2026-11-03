import unittest
from decimal import Decimal
from datetime import date
from ledger import parse_csv, totals_by_currency, render_report
from ledger.models import Entry

NL = chr(10)
DATA = ("account,amount,day,status" + NL +
        "a,1.20,2026-01-01,posted" + NL +
        "b,2.30,2026-01-02,pending" + NL)
MULTI = ("account,amount,day,status,currency" + NL +
         "a,1.20,2026-01-01,posted,EUR" + NL +
         "b,2.30,2026-01-02,posted,GBP" + NL +
         "c,5.00,2026-01-03,posted,USD" + NL)
PENDING = ("account,amount,day,status,currency" + NL +
           "a,1.00,2026-01-01,posted,USD" + NL +
           "b,2.00,2026-01-02,pending,USD" + NL)


class CurrencyEntryTests(unittest.TestCase):
    def test_entry_default_currency(self):
        e = Entry("a", Decimal("1.0"), date(2026, 1, 1))
        self.assertEqual(e.currency, "USD")

    def test_parse_defaults_to_usd_when_column_missing(self):
        rows = parse_csv(DATA)
        self.assertEqual([r.currency for r in rows], ["USD", "USD"])

    def test_currency_normalized_uppercase(self):
        rows = parse_csv("account,amount,day,status,currency" + NL +
                         "a,1.00,2026-01-01,posted,eur" + NL)
        self.assertEqual(rows[0].currency, "EUR")

    def test_invalid_currency_two_letters_raises(self):
        with self.assertRaises(ValueError):
            parse_csv("account,amount,day,status,currency" + NL +
                      "a,1.00,2026-01-01,posted,EU" + NL)

    def test_invalid_currency_four_letters_raises(self):
        with self.assertRaises(ValueError):
            parse_csv("account,amount,day,status,currency" + NL +
                      "a,1.00,2026-01-01,posted,EURE" + NL)

    def test_invalid_currency_non_alpha_raises(self):
        with self.assertRaises(ValueError):
            parse_csv("account,amount,day,status,currency" + NL +
                      "a,1.00,2026-01-01,posted,US1" + NL)

    def test_empty_currency_is_invalid(self):
        with self.assertRaises(ValueError):
            parse_csv("account,amount,day,status,currency" + NL +
                      "a,1.00,2026-01-01,posted," + NL)


class TotalsByCurrencyTests(unittest.TestCase):
    def test_sums_by_currency(self):
        rows = parse_csv(MULTI)
        result = totals_by_currency(rows)
        self.assertEqual(result["EUR"], Decimal("1.20"))
        self.assertEqual(result["GBP"], Decimal("2.30"))
        self.assertEqual(result["USD"], Decimal("5.00"))

    def test_excludes_pending_by_default(self):
        rows = parse_csv(PENDING)
        result = totals_by_currency(rows)
        self.assertEqual(result["USD"], Decimal("1.00"))

    def test_include_pending(self):
        rows = parse_csv(PENDING)
        result = totals_by_currency(rows, include_pending=True)
        self.assertEqual(result["USD"], Decimal("3.00"))

    def test_start_bound_inclusive(self):
        rows = parse_csv(MULTI)
        result = totals_by_currency(rows, start=date(2026, 1, 2))
        self.assertNotIn("EUR", result)
        self.assertEqual(result["GBP"], Decimal("2.30"))
        self.assertEqual(result["USD"], Decimal("5.00"))

    def test_end_bound_inclusive(self):
        rows = parse_csv(MULTI)
        result = totals_by_currency(rows, end=date(2026, 1, 2))
        self.assertNotIn("USD", result)
        self.assertIn("EUR", result)
        self.assertEqual(result["EUR"], Decimal("1.20"))

    def test_reversed_bounds_raise(self):
        rows = parse_csv(MULTI)
        with self.assertRaises(ValueError):
            totals_by_currency(rows, start=date(2026, 1, 5), end=date(2026, 1, 1))

    def test_no_filter_returns_all(self):
        rows = parse_csv(MULTI)
        result = totals_by_currency(rows)
        self.assertEqual(len(result), 3)

    def test_single_bound_only(self):
        rows = parse_csv(MULTI)
        result = totals_by_currency(rows, start=None, end=None)
        self.assertEqual(sum(result.values()), Decimal("8.50"))


class RenderReportTests(unittest.TestCase):
    def test_legacy_unchanged(self):
        import json
        out = render_report(MULTI)
        self.assertEqual(json.loads(out), {"total": "8.50"})

    def test_legacy_includes_pending(self):
        import json
        out = render_report(PENDING)
        self.assertEqual(json.loads(out), {"total": "3.00"})

    def test_by_currency(self):
        import json
        out = render_report(MULTI, by_currency=True)
        self.assertEqual(json.loads(out), {"totals": {"EUR": "1.20", "GBP": "2.30", "USD": "5.00"}})

    def test_by_currency_with_date_filter(self):
        import json
        out = render_report(MULTI, by_currency=True, start=date(2026, 1, 2))
        self.assertEqual(json.loads(out), {"totals": {"GBP": "2.30", "USD": "5.00"}})

    def test_by_currency_excludes_pending_by_default(self):
        import json
        out = render_report(PENDING, by_currency=True)
        self.assertEqual(json.loads(out), {"totals": {"USD": "1.00"}})


if __name__ == "__main__":
    unittest.main()
