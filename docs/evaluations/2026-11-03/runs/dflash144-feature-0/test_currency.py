import unittest, json
from datetime import date
from decimal import Decimal
from ledger import parse_csv, total, render_report
from ledger.summary import totals_by_currency

NL = chr(10)
DATA = ('account,amount,day,status,currency' + NL +
        'a,1.20,2026-01-01,posted,usd' + NL +
        'b,2.30,2026-01-02,pending,EUR' + NL +
        'c,0.50,2026-01-03,posted,usd' + NL +
        'd,0.80,2026-01-04,pending,EUR' + NL)

class TestCurrencyParse(unittest.TestCase):
    def test_default_currency_usd(self):
        entries = parse_csv('account,amount,day,status' + NL + 'x,1.00,2026-01-01,posted' + NL)
        self.assertEqual(entries[0].currency, 'USD')

    def test_currency_normalized_uppercase(self):
        entries = parse_csv(DATA)
        self.assertEqual(entries[0].currency, 'USD')
        self.assertEqual(entries[1].currency, 'EUR')

    def test_missing_column_defaults_to_usd(self):
        entries = parse_csv('account,amount,day,status' + NL + 'x,1.00,2026-01-01,posted' + NL)
        self.assertEqual(entries[0].currency, 'USD')

    def test_invalid_currency_raises(self):
        for bad in ['us', 'EURX', '123', 'US$', '']:
            row = ('account,amount,day,status,currency' + NL + 'x,1.00,2026-01-01,posted,' + bad + NL)
            with self.assertRaises(ValueError):
                parse_csv(row)

class TestTotalsByCurrency(unittest.TestCase):
    def _entries(self):
        return parse_csv(DATA)

    def test_sums_by_currency_excludes_pending_by_default(self):
        r = totals_by_currency(self._entries())
        self.assertEqual(r, {'USD': Decimal('1.70')})

    def test_include_pending(self):
        r = totals_by_currency(self._entries(), include_pending=True)
        self.assertEqual(r, {'USD': Decimal('1.70'), 'EUR': Decimal('3.10')})

    def test_inclusive_date_bounds(self):
        r = totals_by_currency(self._entries(), start=date(2026, 1, 2), end=date(2026, 1, 4), include_pending=True)
        self.assertEqual(r, {'EUR': Decimal('3.10'), 'USD': Decimal('0.50')})

    def test_start_only_and_end_only(self):
        r = totals_by_currency(self._entries(), start=date(2026, 1, 2), include_pending=True)
        self.assertEqual(r, {'EUR': Decimal('3.10'), 'USD': Decimal('0.50')})
        r = totals_by_currency(self._entries(), end=date(2026, 1, 2), include_pending=True)
        self.assertEqual(r, {'USD': Decimal('1.20'), 'EUR': Decimal('2.30')})

    def test_reversed_bounds_raise(self):
        with self.assertRaises(ValueError):
            totals_by_currency(self._entries(), start=date(2026, 1, 3), end=date(2026, 1, 1))

    def test_no_entries_empty_dict(self):
        self.assertEqual(totals_by_currency([]), {})

class TestRenderReportCurrency(unittest.TestCase):
    def test_by_currency_default_excludes_pending(self):
        out = json.loads(render_report(DATA, by_currency=True))
        self.assertEqual(out, {'totals': {'USD': '1.70'}})

    def test_by_currency_with_date_filter(self):
        out = json.loads(render_report(DATA, by_currency=True, start='2026-01-01', end='2026-01-02'))
        self.assertEqual(out, {'totals': {'USD': '1.20'}})

    def test_by_currency_reversed_bounds_raise(self):
        with self.assertRaises(ValueError):
            render_report(DATA, by_currency=True, start='2026-01-03', end='2026-01-01')

    def test_legacy_total_includes_pending_unchanged(self):
        self.assertEqual(json.loads(render_report(DATA)), {'total': '4.80'})
        self.assertEqual(total(parse_csv(DATA)), Decimal('4.80'))

if __name__ == '__main__':
    unittest.main()