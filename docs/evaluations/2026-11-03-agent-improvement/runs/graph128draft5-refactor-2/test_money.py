import unittest
from decimal import Decimal
from catalog.money import parse_money, apply_discount, line_total
from catalog.pricing import discounted
from catalog.orders import invoice_total
from catalog.inventory import stock_value
from catalog import checkout


class TestParseMoney(unittest.TestCase):
    def test_rounds_to_cents(self):
        self.assertEqual(parse_money('1.005'), Decimal('1.01'))
    def test_rounds_down(self):
        self.assertEqual(parse_money('1.004'), Decimal('1.00'))
    def test_exact(self):
        self.assertEqual(parse_money('12.34'), Decimal('12.34'))
    def test_zero(self):
        self.assertEqual(parse_money('0'), Decimal('0.00'))
    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            parse_money('-1.00')


class TestApplyDiscount(unittest.TestCase):
    def test_no_discount(self):
        self.assertEqual(apply_discount('1.005', 0), Decimal('1.01'))
    def test_full_discount(self):
        self.assertEqual(apply_discount('1.005', 100), Decimal('0.00'))
    def test_half(self):
        self.assertEqual(apply_discount('1.005', 50), Decimal('0.50'))
    def test_no_double_rounding(self):
        self.assertEqual(apply_discount('1.005', 10), Decimal('0.90'))
    def test_percent_out_of_range(self):
        with self.assertRaises(ValueError):
            apply_discount('1.00', 101)
        with self.assertRaises(ValueError):
            apply_discount('1.00', -1)
    def test_negative_price(self):
        with self.assertRaises(ValueError):
            apply_discount('-1.00', 0)


class TestLineTotal(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(line_total('1.005', 3, 0), Decimal('3.03'))
    def test_with_discount(self):
        self.assertEqual(line_total('1.005', 3, 10), Decimal('2.70'))
    def test_zero_qty(self):
        self.assertEqual(line_total('1.005', 0, 0), Decimal('0.00'))
    def test_invalid_qty_bool(self):
        with self.assertRaises(ValueError):
            line_total('1.00', True)
        with self.assertRaises(ValueError):
            line_total('1.00', False)
    def test_negative_qty(self):
        with self.assertRaises(ValueError):
            line_total('1.00', -1)
    def test_float_qty(self):
        with self.assertRaises(ValueError):
            line_total('1.00', 2.5)


class TestPublicAPI(unittest.TestCase):
    def test_discounted_wrapper(self):
        self.assertEqual(discounted('1.005'), Decimal('1.01'))
    def test_invoice_total(self):
        self.assertEqual(invoice_total([{'price':'1.005','qty':3}]), Decimal('3.03'))
    def test_stock_value(self):
        self.assertEqual(stock_value([{'price':'2.005','qty':2}]), Decimal('4.02'))
    def test_checkout(self):
        self.assertEqual(checkout([{'price':'10','qty':2}], 2),
                         {'subtotal':'20.00','shipping':'7.50','total':'27.50'})


if __name__ == '__main__':
    unittest.main()
