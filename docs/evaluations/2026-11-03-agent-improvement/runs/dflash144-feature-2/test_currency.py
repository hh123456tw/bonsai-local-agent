import unittest
from datetime import date
from decimal import Decimal
from ledger import parse_csv, render_report, total
from ledger.models import Entry
from ledger.summary import totals_by_currency

DATA = ('account,amount,day,status,currency\n'
        'a,1.20,2026-01-01,posted,usd\n'
        'b,2.30,2026-01-02,pending,EUR\n'
        'c,5.00,2026-01-03,posted,\n')

class EntryCurrencyTests(unittest.TestCase):
    def test_entry_currency_defaults_to_usd(self):
        self.assertEqual(Entry('x', Decimal('1'), date(2026, 1, 1)).currency, 'USD')

    def test_parse_default_usd_when_column_missing(self):
        entries = parse_csv(DATA)
        self.assertEqual(entries[2].currency, 'USD')

    def test_parse_normalizes_lowercase_and_mixed_case(self):
        entries = parse_csv(DATA)
        self.assertEqual(entries[0].currency, 'USD')
        self.assertEqual(entries[1].currency, 'EUR')

    def test_parse_invalid_currency_raises_value_error(self):
        for bad in ('US', 'USDA', 'U$D', 'u1d', 'USDX'):
            with self.assertRaises(ValueError):
                parse_csv('account,amount,day,status,currency\na,1.00,2026-01-01,posted,' + bad + '\n')

    def test_parse_empty_currency_falls_back_to_usd(self):
        entries = parse_csv('account,amount,day,status,currency\na,1.00,2026-01-01,posted,\n')
        self.assertEqual(entries[0].currency, 'USD')

class TotalsByCurrencyTests(unittest.TestCase):
    def setUp(self):
        self.entries = parse_csv(DATA)

    def test_sums_per_currency_posted_only_by_default(self):
        result = totals_by_currency(self.entries)
        self.assertEqual(result.get('USD'), Decimal('6.20'))
        self.assertEqual(len(result), 1)

    def test_include_pending_includes_all_statuses(self):
        result = totals_by_currency(self.entries, include_pending=True)
        self.assertEqual(result.get('USD'), Decimal('6.20'))
        self.assertEqual(result.get('EUR'), Decimal('2.30'))

    def test_date_bounds_inclusive(self):
        r1 = totals_by_currency(self.entries, start=date(2026, 1, 1), end=date(2026, 1, 2))
        self.assertEqual(r1.get('USD'), Decimal('1.20'))
        r2 = totals_by_currency(self.entries, start=None, end=date(2026, 1, 3))
        self.assertEqual(r2.get('USD'), Decimal('6.20'))
        r3 = totals_by_currency(self.entries, start=date(2026, 1, 2))
        self.assertEqual(r3.get('USD'), Decimal('5.00'))

    def test_reversed_bounds_raise_value_error(self):
        with self.assertRaises(ValueError):
            totals_by_currency(self.entries, start=date(2026, 1, 2), end=date(2026, 1, 1))

    def test_no_matching_entries_returns_empty_dict(self):
        self.assertEqual(totals_by_currency(self.entries, start=date(2027, 1, 1)), {})

class RenderReportCurrencyTests(unittest.TestCase):
    def test_legacy_unchanged(self):
        import json
        parsed = json.loads(render_report(DATA))
        self.assertEqual(parsed['total'], '8.50')

    def test_by_currency_true_formats_two_decimals(self):
        import json
        report = render_report(DATA, by_currency=True)
        parsed = json.loads(report)
        self.assertEqual(parsed['totals']['USD'], '6.20')

    def test_by_currency_multi_currency_two_decimals(self):
        import json
        text = ('account,amount,day,status,currency\n'
                'a,1.20,2026-01-01,posted,usd\n'
                'b,2.30,2026-01-02,posted,EUR\n')
        parsed = json.loads(render_report(text, by_currency=True))
        self.assertEqual(parsed['totals']['USD'], '1.20')
        self.assertEqual(parsed['totals']['EUR'], '2.30')

    def test_by_currency_applies_date_filter(self):
        import json
        report = render_report(DATA, by_currency=True, start=date(2026, 1, 1), end=date(2026, 1, 2))
        parsed = json.loads(report)
        self.assertEqual(parsed['totals']['USD'], '1.20')

    def test_by_currency_excludes_pending_by_default(self):
        import json
        report = render_report(DATA, by_currency=True)
        parsed = json.loads(report)
        self.assertNotIn('EUR', parsed['totals'])

if __name__ == '__main__':
    unittest.main()
