import unittest, json
from datetime import date
from decimal import Decimal
from ledger import parse_csv, total, render_report, totals_by_currency
from ledger.models import Entry

_NL = chr(10)

def _csv(*rows):
    return _NL.join(rows)

class TestCurrencyParsing(unittest.TestCase):
    def test_default_currency_is_usd(self):
        entries = parse_csv(_csv('account,amount,day,status', 'x,5.00,2026-01-01,posted'))
        self.assertEqual(entries[0].currency, 'USD')

    def test_explicit_currency_normalized_uppercase(self):
        entries = parse_csv(_csv('account,amount,day,status,currency', 'x,5.00,2026-01-01,posted,eur'))
        self.assertEqual(entries[0].currency, 'EUR')

    def test_invalid_currency_raises(self):
        for bad in ['US', 'USDX', 'us$', '', '123']:
            with self.assertRaises(ValueError):
                parse_csv(_csv('account,amount,day,status,currency', 'x,5.00,2026-01-01,posted,' + bad))

    def test_legacy_csv_without_currency_column_still_works(self):
        data = _csv('account,amount,day,status', 'a,1.20,2026-01-01,posted', 'b,2.30,2026-01-02,pending')
        entries = parse_csv(data)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].currency, 'USD')

class TestTotalsByCurrency(unittest.TestCase):
    def make_entries(self):
        return [
            Entry('a', Decimal('1.20'), date(2026,1,1), 'posted', 'USD'),
            Entry('b', Decimal('2.30'), date(2026,1,2), 'posted', 'EUR'),
            Entry('c', Decimal('0.80'), date(2026,1,3), 'posted', 'USD'),
            Entry('d', Decimal('5.00'), date(2026,1,4), 'pending', 'EUR'),
        ]

    def test_default_excludes_pending(self):
        r = totals_by_currency(self.make_entries())
        self.assertEqual(r['USD'], Decimal('2.00'))
        self.assertEqual(r['EUR'], Decimal('2.30'))
        # pending EUR 5.00 must not be counted
        self.assertNotEqual(r['EUR'], Decimal('7.30'))

    def test_include_pending_includes_all_statuses(self):
        r = totals_by_currency(self.make_entries(), include_pending=True)
        self.assertEqual(r['USD'], Decimal('2.00'))
        self.assertEqual(r['EUR'], Decimal('7.30'))

    def test_start_bound_inclusive(self):
        r = totals_by_currency(self.make_entries(), start=date(2026,1,2))
        self.assertEqual(r['EUR'], Decimal('2.30'))
        self.assertEqual(r['USD'], Decimal('0.80'))

    def test_end_bound_inclusive(self):
        r = totals_by_currency(self.make_entries(), end=date(2026,1,2))
        self.assertEqual(r['USD'], Decimal('1.20'))
        self.assertEqual(r['EUR'], Decimal('2.30'))

    def test_reversed_bounds_raise(self):
        with self.assertRaises(ValueError):
            totals_by_currency(self.make_entries(), start=date(2026,1,2), end=date(2026,1,1))

class TestRenderReport(unittest.TestCase):
    def test_legacy_unchanged(self):
        data = _csv('account,amount,day,status', 'a,1.20,2026-01-01,posted', 'b,2.30,2026-01-02,pending')
        self.assertEqual(json.loads(render_report(data)), {'total': '3.50'})

    def test_by_currency(self):
        data = _csv('account,amount,day,status,currency',
                    'a,1.20,2026-01-01,posted,USD',
                    'b,2.30,2026-01-02,posted,EUR',
                    'c,0.80,2026-01-03,posted,USD',
                    'd,5.00,2026-01-04,pending,EUR')
        out = json.loads(render_report(data, by_currency=True))
        self.assertEqual(out, {'totals': {'USD': '2.00', 'EUR': '2.30'}})

    def test_by_currency_with_date_filter(self):
        data = _csv('account,amount,day,status,currency',
                    'a,1.20,2026-01-01,posted,USD',
                    'b,2.30,2026-01-02,posted,EUR',
                    'c,0.80,2026-01-03,posted,USD',
                    'd,5.00,2026-01-04,pending,EUR')
        out = json.loads(render_report(data, by_currency=True, start=date(2026,1,2)))
        self.assertEqual(out, {'totals': {'USD': '0.80', 'EUR': '2.30'}})

if __name__ == '__main__':
    unittest.main()
