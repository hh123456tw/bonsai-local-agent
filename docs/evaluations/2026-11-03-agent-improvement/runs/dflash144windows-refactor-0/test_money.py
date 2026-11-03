import unittest
from decimal import Decimal

from catalog.money import parse_money, apply_discount, line_total


class TestParseMoney(unittest.TestCase):
    def test_rounds_half_up_to_cents(self):
        self.assertEqual(parse_money('1.005'), Decimal('1.01'))

    def test_truncates_down(self):
        self.assertEqual(parse_money('1.004'), Decimal('1.00'))

    def test_accepts_int_and_float(self):
        self.assertEqual(parse_money(2), Decimal('2.00'))
        self.assertEqual(parse_money(1.999), Decimal('2.00'))

    def test_zero(self):
        self.assertEqual(parse_money('0'), Decimal('0.00'))

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            parse_money('-0.01')


class TestApplyDiscount(unittest.TestCase):
    def test_no_double_rounding(self):
        # 1.005 * 0.9 = 0.9045 -> 0.90 (NOT 0.91 from pre-rounding)
        self.assertEqual(apply_discount('1.005', 10), Decimal('0.90'))

    def test_zero_percent(self):
        self.assertEqual(apply_discount('1.005', 0), Decimal('1.01'))

    def test_full_discount(self):
        self.assertEqual(apply_discount('1.005', 100), Decimal('0.00'))

    def test_percent_range(self):
        self.assertEqual(apply_discount('10', 50), Decimal('5.00'))

    def test_negative_price_raises(self):
        with self.assertRaises(ValueError):
            apply_discount('-1', 0)

    def test_percent_out_of_range(self):
        with self.assertRaises(ValueError):
            apply_discount('1', 101)
        with self.assertRaises(ValueError):
            apply_discount('1', -1)


class TestLineTotal(unittest.TestCase):
    def test_unit_rounded_then_multiplied(self):
        self.assertEqual(line_total('1.005', 3), Decimal('3.03'))

    def test_with_discount(self):
        self.assertEqual(line_total('1.005', 3, 10), Decimal('2.70'))

    def test_integer_quantity(self):
        self.assertEqual(line_total('10', 2), Decimal('20.00'))

    def test_bool_quantity_rejected(self):
        with self.assertRaises(ValueError):
            line_total('1', True)

    def test_negative_quantity_rejected(self):
        with self.assertRaises(ValueError):
            line_total('1', -1)

    def test_float_quantity_rejected(self):
        with self.assertRaises(ValueError):
            line_total('1', 1.5)


if __name__ == '__main__':
    unittest.main()
