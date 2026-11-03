import unittest, json
from datetime import date
from decimal import Decimal
from ledger import parse_csv, total, render_report
from ledger.summary import totals_by_currency
from ledger.models import Entry

H = 'account,amount,day,status,currency\n'
DATA = H + 'a,1.20,2026-01-01,posted,USD\nb,2.30,2026-01-02,pending,EUR\n'


def _p(*rows):
    return parse_csv(H + '\n'.join(rows) + '\n')


class TestCurrencyDefault(unittest.TestCase):
    def test_default_usd(self):
        e = _p('a,1.00,2026-01-01,posted')[0]
        self.assertEqual(e.currency, 'USD')

    def test_explicit_currency(self):
        e = _p('a,1.00,2026-01-01,posted,EUR')[0]
        self.assertEqual(e.currency, 'EUR')

    def test_lowercase_normalized(self):
        e = _p('a,1.00,2026-01-01,posted,eur')[0]
        self.assertEqual(e.currency, 'EUR')

    def test_mixed_case_normalized(self):
        e = _p('a,1.00,2026-01-01,posted,eUr')[0]
        self.assertEqual(e.currency, 'EUR')

    def test_invalid_too_short(self):
        with self.assertRaises(ValueError):
            _p('a,1.00,2026-01-01,posted,EU')

    def test_invalid_too_long(self):
        with self.assertRaises(ValueError):
            _p('a,1.00,2026-01-01,posted,XXXX')

    def test_invalid_non_alpha(self):
        with self.assertRaises(ValueError):
            _p('a,1.00,2026-01-01,posted,US-D')

    def test_invalid_digits(self):
        with self.assertRaises(ValueError):
            _p('a,1.00,2026-01-01,posted,123')

    def test_empty_defaults_usd(self):
        e = _p('a,1.00,2026-01-01,posted,')[0]
        self.assertEqual(e.currency, 'USD')


class TestTotalsByCurrency(unittest.TestCase):
    def _entries(self):
        return [
            Entry('a', Decimal('1.20'), date(2026, 1, 1), 'posted', 'USD'),
            Entry('b', Decimal('2.30'), date(2026, 1, 2), 'pending', 'EUR'),
            Entry('c', Decimal('5.00'), date(2026, 1, 3), 'posted', 'EUR'),
            Entry('d', Decimal('7.00'), date(2026, 1, 4), 'posted', 'GBP'),
        ]

    def test_default_excludes_pending(self):
        r = totals_by_currency(self._entries())
        self.assertEqual(r['USD'], Decimal('1.20'))
        self.assertEqual(r['EUR'], Decimal('5.00'))
        self.assertEqual(r['GBP'], Decimal('7.00'))
        self.assertNotIn('pending', r)

    def test_include_pending(self):
        r = totals_by_currency(self._entries(), include_pending=True)
        self.assertEqual(r['EUR'], Decimal('7.30'))

    def test_start_inclusive(self):
        r = totals_by_currency(self._entries(), start=date(2026, 1, 3))
        self.assertEqual(r['EUR'], Decimal('5.00'))
        self.assertEqual(r['GBP'], Decimal('7.00'))
        self.assertNotIn('USD', r)

    def test_end_inclusive(self):
        r = totals_by_currency(self._entries(), end=date(2026, 1, 2))
        self.assertEqual(r['USD'], Decimal('1.20'))
        self.assertNotIn('GBP', r)

    def test_end_inclusive_with_pending(self):
        r = totals_by_currency(self._entries(), end=date(2026, 1, 2), include_pending=True)
        self.assertEqual(r['USD'], Decimal('1.20'))
        self.assertEqual(r['EUR'], Decimal('2.30'))
        self.assertNotIn('GBP', r)

    def test_reversed_bounds_raises(self):
        with self.assertRaises(ValueError):
            totals_by_currency(self._entries(), start=date(2026, 1, 5), end=date(2026, 1, 1))

    def test_no_entries(self):
        self.assertEqual(totals_by_currency([]), {})


class TestRenderReport(unittest.TestCase):
    def test_legacy_unchanged(self):
        self.assertEqual(json.loads(render_report(DATA)), {'total': '3.50'})

    def test_by_currency(self):
        out = json.loads(render_report(DATA, by_currency=True))
        self.assertEqual(out, {'totals': {'EUR': '2.30', 'USD': '1.20'}})

    def test_by_currency_with_date_filter(self):
        out = json.loads(render_report(DATA, by_currency=True, start=date(2026, 1, 2)))
        self.assertEqual(out, {'totals': {'EUR': '2.30'}})

    def test_by_currency_end_inclusive(self):
        out = json.loads(render_report(DATA, by_currency=True, end=date(2026, 1, 1)))
        self.assertEqual(out, {'totals': {'USD': '1.20'}})

    def test_by_currency_format_two_decimals(self):
        out = json.loads(render_report(DATA, by_currency=True))
        for v in out['totals'].values():
            self.assertEqual(len(v.split('.')[-1]), 2)


if __name__ == '__main__':
    unittest.main()
