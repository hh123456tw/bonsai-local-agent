"""Tests for the shared catalog.money module and its integration."""
import unittest
from decimal import Decimal

from catalog import checkout
from catalog.inventory import stock_value
from catalog.orders import invoice_total
from catalog.pricing import discounted
from catalog.money import apply_discount, line_total, parse_money


class ParseMoneyTests(unittest.TestCase):
    def test_half_up_rounding(self):
        self.assertEqual(parse_money('1.005'), Decimal('1.01'))

    def test_normal_values(self):
        self.assertEqual(parse_money('10'), Decimal('10.00'))
        self.assertEqual(parse_money('0.999'), Decimal('1.00'))
        self.assertEqual(parse_money(Decimal('2.5')), Decimal('2.50'))

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            parse_money('-0.01')


class ApplyDiscountTests(unittest.TestCase):
    def test_rounds_from_unrounded_input(self):
        # 1.005 * 0.9 = 0.9045 -> 0.90 (single rounding at the end)
        self.assertEqual(apply_discount('1.005', 10), Decimal('0.90'))
        self.assertEqual(apply_discount('1.005', 50), Decimal('0.50'))

    def test_percent_range(self):
        self.assertEqual(apply_discount('10.00', 0), Decimal('10.00'))
        self.assertEqual(apply_discount('10.00', 100), Decimal('0.00'))

    def test_invalid_price(self):
        with self.assertRaises(ValueError):
            apply_discount('-1.00', 10)

    def test_invalid_percent(self):
        with self.assertRaises(ValueError):
            apply_discount('10.00', 101)
        with self.assertRaises(ValueError):
            apply_discount('10.00', -1)


class LineTotalTests(unittest.TestCase):
    def test_matches_original_invoice_math(self):
        # Original: round(unit, cents) * qty, then sum
        self.assertEqual(line_total('1.005', 3), Decimal('3.03'))

    def test_with_discount(self):
        self.assertEqual(line_total('10.00', 2, 10), Decimal('18.00'))

    def test_zero_quantity(self):
        self.assertEqual(line_total('5.00', 0), Decimal('0.00'))

    def test_bool_quantity_rejected(self):
        with self.assertRaises(ValueError):
            line_total('5.00', True)
        with self.assertRaises(ValueError):
            line_total('5.00', False)

    def test_negative_quantity_rejected(self):
        with self.assertRaises(ValueError):
            line_total('5.00', -1)

    def test_float_quantity_rejected(self):
        with self.assertRaises(ValueError):
            line_total('5.00', 2.0)


class IntegrationTests(unittest.TestCase):
    def test_existing_suite_cases(self):
        self.assertEqual(invoice_total([{'price': '1.005', 'qty': 3}]), Decimal('3.03'))
        self.assertEqual(stock_value([{'price': '2.005', 'qty': 2}]), Decimal('4.02'))
        self.assertEqual(checkout([{'price': '10', 'qty': 2}], 2),
                         {'subtotal': '20.00', 'shipping': '7.50', 'total': '27.50'})

    def test_discounted_via_pricing(self):
        self.assertEqual(discounted('1.005'), Decimal('1.01'))

    def test_shipping_unchanged(self):
        from catalog.shipping import quote
        self.assertEqual(quote(2), Decimal('7.50'))
        self.assertEqual(quote(2, express=True), Decimal('15.00'))


if __name__ == '__main__':
    unittest.main()
