import unittest
from decimal import Decimal

from catalog.money import parse_money, apply_discount, line_total


class MoneyTests(unittest.TestCase):
    def test_parse_money_rounds_to_cents(self):
        self.assertEqual(parse_money('1.005'), Decimal('1.01'))
        self.assertEqual(parse_money('1.004'), Decimal('1.00'))
        self.assertEqual(parse_money(10), Decimal('10.00'))
        self.assertEqual(parse_money('0'), Decimal('0.00'))

    def test_parse_money_negative_raises(self):
        with self.assertRaises(ValueError):
            parse_money('-1')

    def test_apply_discount_from_unrounded_input(self):
        # 1.005 * 0.5 = 0.5025 -> 0.50 (no double rounding)
        self.assertEqual(apply_discount('1.005', 50), Decimal('0.50'))
        self.assertEqual(apply_discount('1.005', 0), Decimal('1.01'))
        self.assertEqual(apply_discount('1.005', 100), Decimal('0.00'))

    def test_apply_discount_invalid(self):
        with self.assertRaises(ValueError):
            apply_discount('-1')
        with self.assertRaises(ValueError):
            apply_discount('1.00', 101)
        with self.assertRaises(ValueError):
            apply_discount('1.00', -1)

    def test_line_total_rounds_unit_price_before_qty(self):
        # unit 1.01 * 3 = 3.03
        self.assertEqual(line_total('1.005', 3, 0), Decimal('3.03'))
        # unit 0.50 * 3 = 1.50
        self.assertEqual(line_total('1.005', 3, 50), Decimal('1.50'))
        self.assertEqual(line_total('1.005', 0), Decimal('0.00'))

    def test_line_total_invalid_quantity(self):
        for bad in (-1, True, False):
            with self.assertRaises(ValueError):
                line_total('1.00', bad)


if __name__ == '__main__':
    unittest.main()
