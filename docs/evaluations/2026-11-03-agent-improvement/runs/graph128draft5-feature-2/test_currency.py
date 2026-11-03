import unittest
from datetime import date
from decimal import Decimal
from ledger import parse_csv, total, render_report
from ledger.models import Entry
from ledger.summary import totals_by_currency


class CurrencyEntry(unittest.TestCase):
    def make(self, **kw):
        base = dict(account='a', amount=Decimal('1.00'), day=date(2026, 1, 1), status='posted')
        base.update(kw)
        return Entry(**base)

    def test_entry_currency_defaults_to_usd(self):
        e = Entry('a', Decimal('1.00'), date(2026, 1, 1))
        self.assertEqual(e.currency, 'USD')

    def test_parse_csv_default_currency_is_usd(self):
        data = 'account,amount,day
b,2.00,2026-01-02
'
        entries = parse_csv(data)
        self.assertEqual([e.currency for e in entries], ['USD'])

    def test_parse_csv_currency_normalized_uppercase(self):
        data = 'account,amount,day,currency
a,1.00,2026-01-01,eur
b,2.00,2026-01-02,EUR
'
        entries = parse_csv(data)
        self.assertEqual(entries[0].currency, 'EUR')
        self.assertEqual(entries[1].currency, 'EUR')

    def test_parse_csv_invalid_code_too_short(self):
        with self.assertRaises(ValueError):
            parse_csv('account,amount,day,currency
a,1.00,2026-01-01,EU
')

    def test_parse_csv_invalid_code_too_long(self):
        with self.assertRaises(ValueError):
            parse_csv('account,amount,day,currency
a,1.00,2026-01-01,EURO
')

    def test_parse_csv_invalid_code_non_alpha(self):
        with self.assertRaises(ValueError):
            parse_csv('account,amount,day,currency
a,1.00,2026-01-01,US1
')

    def test_parse_csv_invalid_code_empty(self):
        with self.assertRaises(ValueError):
            parse_csv('account,amount,day,currency
a,1.00,2026-01-01,
')

    def test_parse_csv_invalid_code_mixed(self):
        with self.assertRaises(ValueError):
            parse_csv('account,amount,day,currency
a,1.00,2026-01-01,usd1
')

    def test_totals_by_currency_sums_by_currency(self):
        entries = [
            Entry('a', Decimal('1.00'), date(2026, 1, 1)),
            Entry('b', Decimal('2.00'), date(2026, 1, 1), currency='EUR'),
            Entry('c', Decimal('3.00'), date(2026, 1, 1), currency='USD'),
        ]
        res = totals_by_currency(entries)
        self.assertEqual(res['USD'], Decimal('4.00'))
        self.assertEqual(res['EUR'], Decimal('2.00'))

    def test_totals_by_currency_default_excludes_pending(self):
        entries = [
            Entry('a', Decimal('1.00'), date(2026, 1, 1), status='posted'),
            Entry('b', Decimal('2.00'), date(2026, 1, 1), status='pending'),
        ]
        res = totals_by_currency(entries)
        self.assertEqual(res['USD'], Decimal('1.00'))

    def test_totals_by_currency_include_pending_true(self):
        entries = [
            Entry('a', Decimal('1.00'), date(2026, 1, 1), status='posted'),
            Entry('b', Decimal('2.00'), date(2026, 1, 1), status='pending'),
        ]
        res = totals_by_currency(entries, include_pending=True)
        self.assertEqual(res['USD'], Decimal('3.00'))

    def test_totals_by_currency_inclusive_date_bounds(self):
        entries = [
            Entry('a', Decimal('1.00'), date(2026, 1, 1)),
            Entry('b', Decimal('2.00'), date(2026, 1, 2)),
            Entry('c', Decimal('3.00'), date(2026, 1, 3)),
        ]
        res = totals_by_currency(entries, start=date(2026, 1, 1), end=date(2026, 1, 2))
        self.assertEqual(res['USD'], Decimal('3.00'))

    def test_totals_by_currency_start_only(self):
        entries = [
            Entry('a', Decimal('1.00'), date(2026, 1, 1)),
            Entry('b', Decimal('2.00'), date(2026, 1, 2)),
        ]
        res = totals_by_currency(entries, start=date(2026, 1, 2))
        self.assertEqual(res['USD'], Decimal('2.00'))

    def test_totals_by_currency_end_only(self):
        entries = [
            Entry('a', Decimal('1.00'), date(2026, 1, 1)),
            Entry('b', Decimal('2.00'), date(2026, 1, 2)),
        ]
        res = totals_by_currency(entries, end=date(2026, 1, 1))
        self.assertEqual(res['USD'], Decimal('1.00'))

    def test_totals_by_currency_reversed_bounds(self):
        entries = [Entry('a', Decimal('1.00'), date(2026, 1, 1))]
        with self.assertRaises(ValueError):
            totals_by_currency(entries, start=date(2026, 1, 2), end=date(2026, 1, 1))

    def test_totals_by_currency_returns_dict(self):
        entries = [Entry('a', Decimal('1.00'), date(2026, 1, 1))]
        res = totals_by_currency(entries)
        self.assertIsInstance(res, dict)

    def test_totals_by_currency_empty(self):
        res = totals_by_currency([])
        self.assertEqual(res, {})

    def test_render_report_legacy_unchanged(self):
        data = 'account,amount,day,status
a,1.20,2026-01-01,posted
b,2.30,2026-01-02,pending
'
        self.assertEqual(render_report(data), '{"total": "3.50"}')

    def test_render_report_by_currency(self):
        data = 'account,amount,day,currency
a,1.00,2026-01-01,USD
b,2.00,2026-01-01,EUR
'
        out = render_report(data, by_currency=True)
        import json
        self.assertEqual(json.loads(out), {'totals': {'EUR': '2.00', 'USD': '1.00'}})

    def test_render_report_by_currency_filters_dates(self):
        data = 'account,amount,day,currency
a,1.00,2026-01-01,USD
b,2.00,2026-01-02,USD
c,3.00,2026-01-03,USD
'
        out = render_report(data, by_currency=True, start=date(2026, 1, 2), end=date(2026, 1, 3))
        import json
        self.assertEqual(json.loads(out), {'totals': {'USD': '5.00'}})

    def test_render_report_by_currency_formats_two_decimals(self):
        data = 'account,amount,day,currency
a,1.234,2026-01-01,USD
'
        out = render_report(data, by_currency=True)
        import json
        self.assertEqual(json.loads(out)['totals']['USD'], '1.23')

    def test_render_report_by_currency_includes_pending(self):
        data = 'account,amount,day,currency,status
a,1.00,2026-01-01,USD,posted
b,2.00,2026-01-01,USD,pending
'
        out = render_report(data, by_currency=True)
        import json
        self.assertEqual(json.loads(out), {'totals': {'USD': '3.00'}})

    def test_render_report_by_currency_reversed_bounds(self):
        data = 'account,amount,day,currency
a,1.00,2026-01-01,USD
'
        with self.assertRaises(ValueError):
            render_report(data, by_currency=True, start=date(2026, 1, 2), end=date(2026, 1, 1))

    def test_legacy_total_includes_pending(self):
        data = 'account,amount,day,status
a,1.20,2026-01-01,posted
b,2.30,2026-01-02,pending
'
        self.assertEqual(total(parse_csv(data)), Decimal('3.50'))


if __name__ == '__main__':
    unittest.main()
