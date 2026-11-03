"""Tests for the shared catalog.money helpers."""
import unittest
from decimal import Decimal

from catalog.money import parse_money, apply_discount, line_total


class ParseMoneyTests(unittest.TestCase):
    def test_rounds_to_cents(self):
        self.assertEqual(parse_money("1.005"), Decimal("1.01"))

    def test_accepts_numbers(self):
        self.assertEqual(parse_money(2.005), Decimal("2.01"))
        self.assertEqual(parse_money(3), Decimal("3.00"))

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            parse_money("-1")

    def test_non_numeric_raises(self):
        for bad in ("abc", None, "nan"):
            with self.assertRaises(ValueError):
                parse_money(bad)


class ApplyDiscountTests(unittest.TestCase):
    def test_default_percent_zero(self):
        self.assertEqual(apply_discount("2.005"), Decimal("2.01"))

    def test_discounted(self):
        self.assertEqual(apply_discount("1.005", 10), Decimal("0.90"))

    def test_no_double_rounding(self):
        # Full-precision price is discounted first, then rounded once.
        # Rounding the price to 1.01 first would give 0.91 instead of 0.90.
        self.assertEqual(apply_discount("1.005", 10), Decimal("0.90"))

    def test_invalid_price(self):
        for bad in ("-1", "abc"):
            with self.assertRaises(ValueError):
                apply_discount(bad, 10)

    def test_invalid_rate(self):
        for bad in (-5, 100.5, 101):
            with self.assertRaises(ValueError):
                apply_discount("1", bad)

    def test_full_discount(self):
        self.assertEqual(apply_discount("5.00", 100), Decimal("0.00"))


class LineTotalTests(unittest.TestCase):
    def test_unit_price_rounded_before_multiply(self):
        # unit = round(1.005 * 0.9) = 0.90; total = 0.90 * 3 = 2.70
        self.assertEqual(line_total("1.005", 3, 10), Decimal("2.70"))

    def test_no_discount(self):
        self.assertEqual(line_total("2.005", 2), Decimal("4.02"))

    def test_zero_quantity(self):
        self.assertEqual(line_total("5.00", 0), Decimal("0.00"))

    def test_bool_quantity_rejected(self):
        with self.assertRaises(ValueError):
            line_total("1", True)

    def test_negative_quantity_rejected(self):
        with self.assertRaises(ValueError):
            line_total("1", -1)

    def test_float_quantity_rejected(self):
        with self.assertRaises(ValueError):
            line_total("1", 1.5)


if __name__ == "__main__":
    unittest.main()
