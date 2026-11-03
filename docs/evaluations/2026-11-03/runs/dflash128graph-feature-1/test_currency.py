import json
import unittest
from datetime import date
from decimal import Decimal

from ledger import Entry, parse_csv, totals_by_currency, render_report


def _csv(*lines):
    return chr(10).join(lines)


class TestEntryCurrency(unittest.TestCase):
    def test_default_is_usd(self):
        e = Entry('a', Decimal('1'), date(2026, 1, 1))
        self.assertEqual(e.currency, 'USD')

    def test_explicit_currency(self):
        e = Entry('a', Decimal('1'), date(2026, 1, 1), currency='EUR')
        self.assertEqual(e.currency, 'EUR')


class TestParseCurrency(unittest.TestCase):
    def test_missing_column_defaults_to_usd(self):
        rows = parse_csv(_csv('account,amount,day,status', 'a,1.20,2026-01-01,posted'))
        self.assertEqual(rows[0].currency, 'USD')

    def test_lowercase_normalized_to_uppercase(self):
        rows = parse_csv(_csv('account,amount,day,currency', 'a,1.20,2026-01-01,eur'))
        self.assertEqual(rows[0].currency, 'EUR')

    def test_mixed_case_normalized(self):
        rows = parse_csv(_csv('account,amount,day,currency', 'a,1.20,2026-01-01,eUr'))
        self.assertEqual(rows[0].currency, 'EUR')

    def test_whitespace_surrounding_normalized(self):
        rows = parse_csv(_csv('account,amount,day,currency', 'a,1.20,2026-01-01, usd '))
        self.assertEqual(rows[0].currency, 'USD')

    def test_empty_string_invalid(self):
        with self.assertRaises(ValueError):
            parse_csv(_csv('account,amount,day,currency', 'a,1.20,2026-01-01,'))

    def test_two_letters_invalid(self):
        with self.assertRaises(ValueError):
            parse_csv(_csv('account,amount,day,currency', 'a,1.20,2026-01-01,US'))

    def test_four_letters_invalid(self):
        with self.assertRaises(ValueError):
            parse_csv(_csv('account,amount,day,currency', 'a,1.20,2026-01-01,USDX'))

    def test_non_ascii_invalid(self):
        with self.assertRaises(ValueError):
            parse_csv(_csv('account,amount,day,currency', 'a,1.20,2026-01-01,€UR'))

    def test_digits_invalid(self):
        with self.assertRaises(ValueError):
            parse_csv(_csv('account,amount,day,currency', 'a,1.20,2026-01-01,123'))

    def test_dashes_invalid(self):
        with self.assertRaises(ValueError):
            parse_csv(_csv('account,amount,day,currency', 'a,1.20,2026-01-01,U-S-D'))


class TestTotalsByCurrency(unittest.TestCase):
    def _entries(self):
        return [
            Entry('a', Decimal('1.20'), date(2026, 1, 1), 'posted', 'USD'),
            Entry('b', Decimal('2.30'), date(2026, 1, 2), 'pending', 'USD'),
            Entry('c', Decimal('5.00'), date(2026, 2, 1), 'posted', 'EUR'),
        ]

    def test_default_excludes_pending(self):
        self.assertEqual(totals_by_currency(self._entries()), {'USD': Decimal('1.20'), 'EUR': Decimal('5.00')})

    def test_include_pending_includes_all_statuses(self):
        self.assertEqual(
            totals_by_currency(self._entries(), include_pending=True),
            {'USD': Decimal('3.50'), 'EUR': Decimal('5.00')},
        )

    def test_start_bound_inclusive(self):
        t = totals_by_currency(self._entries(), start=date(2026, 1, 2))
        self.assertEqual(t, {'EUR': Decimal('5.00')})

    def test_end_bound_inclusive(self):
        t = totals_by_currency(self._entries(), end=date(2026, 1, 2))
        self.assertEqual(t, {'USD': Decimal('1.20')})

    def test_both_bounds_inclusive_window(self):
        t = totals_by_currency(self._entries(), start=date(2026, 1, 1), end=date(2026, 1, 2))
        self.assertEqual(t, {'USD': Decimal('1.20')})

    def test_date_strings_accepted(self):
        t = totals_by_currency(self._entries(), start='2026-01-01', end='2026-01-30')
        self.assertEqual(t, {'USD': Decimal('1.20')})

    def test_reversed_bounds_raise(self):
        with self.assertRaises(ValueError):
            totals_by_currency(self._entries(), start=date(2026, 2, 1), end=date(2026, 1, 1))

    def test_equal_bounds_allowed(self):
        t = totals_by_currency(self._entries(), start=date(2026, 1, 1), end=date(2026, 1, 1))
        self.assertEqual(t, {'USD': Decimal('1.20')})

    def test_no_entries_empty_dict(self):
        self.assertEqual(totals_by_currency([]), {})

    def test_return_type_is_dict(self):
        self.assertIsInstance(totals_by_currency(self._entries()), dict)


class TestRenderReportCurrency(unittest.TestCase):
    DATA = _csv(
        'account,amount,day,status,currency',
        'a,1.20,2026-01-01,posted,usd',
        'b,2.30,2026-01-02,pending,EUR',
        'c,5.00,2026-02-01,posted,EUR',
    )

    def test_by_currency_totals(self):
        out = json.loads(render_report(self.DATA, by_currency=True))
        self.assertEqual(out, {'totals': {'EUR': '7.30', 'USD': '1.20'}})

    def test_by_currency_with_date_filter(self):
        out = json.loads(render_report(self.DATA, by_currency=True, start='2026-01-01', end='2026-01-02'))
        self.assertEqual(out, {'totals': {'EUR': '2.30', 'USD': '1.20'}})

    def test_by_currency_excludes_outside_range(self):
        out = json.loads(render_report(self.DATA, by_currency=True, end='2026-01-01'))
        self.assertEqual(out, {'totals': {'USD': '1.20'}})

    def test_legacy_render_unchanged(self):
        out = json.loads(render_report(self.DATA))
        self.assertEqual(out, {'total': '8.50'})


if __name__ == '__main__':
    unittest.main()
