import unittest, json
from datetime import date
from decimal import Decimal
from ledger import parse_csv, total, render_report
from ledger.summary import totals_by_currency
from ledger.models import Entry

DATA = chr(10).join([
    "account,amount,day,status,currency",
    "a,1.20,2026-01-01,posted,usd",
    "b,2.30,2026-01-02,pending,EUR",
    "c,0.50,2026-01-03,posted,usd",
])

class TestEntry(unittest.TestCase):
    def test_currency_defaults_to_usd(self):
        e = Entry('a', Decimal('1.00'), date(2026,1,1))
        self.assertEqual(e.currency, 'USD')
    def test_entry_currency_can_be_set(self):
        e = Entry('a', Decimal('1.00'), date(2026,1,1), status='pending', currency='EUR')
        self.assertEqual(e.currency, 'EUR')

class TestParseCurrency(unittest.TestCase):
    def test_missing_column_defaults_to_usd(self):
        rows = parse_csv('account,amount,day,status' + chr(10) + 'x,1.00,2026-01-01,posted' + chr(10))
        self.assertEqual([e.currency for e in rows], ['USD'])
    def test_lowercase_normalized_to_uppercase(self):
        rows = parse_csv(DATA)
        self.assertEqual([e.currency for e in rows], ['USD','EUR','USD'])
    def test_mixed_case_normalized(self):
        rows = parse_csv('account,amount,day,status,currency' + chr(10) + 'a,1.00,2026-01-01,posted,eUr' + chr(10))
        self.assertEqual(rows[0].currency, 'EUR')
    def test_invalid_short_code_raises(self):
        with self.assertRaises(ValueError):
            parse_csv('account,amount,day,status,currency' + chr(10) + 'a,1.00,2026-01-01,posted,us' + chr(10))
    def test_invalid_long_code_raises(self):
        with self.assertRaises(ValueError):
            parse_csv('account,amount,day,status,currency' + chr(10) + 'a,1.00,2026-01-01,posted,usdx' + chr(10))
    def test_invalid_non_alpha_raises(self):
        with self.assertRaises(ValueError):
            parse_csv('account,amount,day,status,currency' + chr(10) + 'a,1.00,2026-01-01,posted,123' + chr(10))
    def test_empty_code_raises(self):
        with self.assertRaises(ValueError):
            parse_csv('account,amount,day,status,currency' + chr(10) + 'a,1.00,2026-01-01,posted,' + chr(10))

class TestTotalsByCurrency(unittest.TestCase):
    def setUp(self):
        self.entries = parse_csv(DATA)
    def test_returns_dict_grouped_by_currency(self):
        t = totals_by_currency(self.entries, include_pending=True)
        self.assertIsInstance(t, dict)
        self.assertEqual(t, {'USD': Decimal('1.70'), 'EUR': Decimal('2.30')})
    def test_excludes_pending_by_default(self):
        t = totals_by_currency(self.entries)
        self.assertNotIn('EUR', t)
        self.assertEqual(t['USD'], Decimal('1.70'))
    def test_include_pending_includes_all_statuses(self):
        t = totals_by_currency(self.entries, include_pending=True)
        self.assertEqual(t, {'USD': Decimal('1.70'), 'EUR': Decimal('2.30')})
    def test_start_bound_inclusive(self):
        t = totals_by_currency(self.entries, start=date(2026,1,2))
        self.assertEqual(t, {'USD': Decimal('0.50')})
    def test_end_bound_inclusive(self):
        t = totals_by_currency(self.entries, end=date(2026,1,1))
        self.assertEqual(t, {'USD': Decimal('1.20')})
    def test_both_bounds_inclusive(self):
        t = totals_by_currency(self.entries, start=date(2026,1,1), end=date(2026,1,2))
        self.assertEqual(t, {'USD': Decimal('1.20')})
    def test_reversed_bounds_raise(self):
        with self.assertRaises(ValueError):
            totals_by_currency(self.entries, start=date(2026,1,2), end=date(2026,1,1))
    def test_equal_bounds_allowed(self):
        t = totals_by_currency(self.entries, start=date(2026,1,1), end=date(2026,1,1))
        self.assertEqual(t, {'USD': Decimal('1.20')})
    def test_empty_entries(self):
        self.assertEqual(totals_by_currency([]), {})

class TestRenderReport(unittest.TestCase):
    def test_legacy_default_unchanged(self):
        self.assertEqual(json.loads(render_report(DATA)), {'total':'4.00'})
    def test_legacy_total_still_includes_pending(self):
        self.assertEqual(total(parse_csv(DATA)), Decimal('4.00'))
    def test_by_currency_default_excludes_pending(self):
        r = json.loads(render_report(DATA, by_currency=True))
        self.assertEqual(r, {'totals':{'USD':'1.70'}})
    def test_by_currency_with_date_filter(self):
        r = json.loads(render_report(DATA, by_currency=True, start=date(2026,1,2)))
        self.assertEqual(r, {'totals':{'USD':'0.50'}})
    def test_by_currency_date_filter_includes_boundary(self):
        r = json.loads(render_report(DATA, by_currency=True, start=date(2026,1,1), end=date(2026,1,1)))
        self.assertEqual(r, {'totals':{'USD':'1.20'}})
    def test_by_currency_amounts_two_decimals(self):
        r = json.loads(render_report(DATA, by_currency=True))
        for v in r['totals'].values():
            parts = v.split('.')
            self.assertEqual(len(parts), 2)
            self.assertEqual(len(parts[1]), 2)

if __name__ == '__main__':
    unittest.main()
