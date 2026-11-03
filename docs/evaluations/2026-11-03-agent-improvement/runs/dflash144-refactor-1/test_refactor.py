import unittest
from decimal import Decimal
from catalog.money import parse_money, apply_discount, line_total
from catalog.pricing import discounted
from catalog.orders import invoice_total
from catalog.inventory import stock_value
from catalog import checkout

class TestMoney(unittest.TestCase):
    def test_parse_money(self):
        self.assertEqual(parse_money('1.005'), Decimal('1.01'))
        self.assertEqual(parse_money('1.00'), Decimal('1.00'))
        self.assertEqual(parse_money(1.5), Decimal('1.50'))
        self.assertEqual(parse_money('10'), Decimal('10.00'))

    def test_parse_money_invalid(self):
        with self.assertRaises(ValueError):
            parse_money('abc')
        with self.assertRaises(ValueError):
            parse_money(None)

    def test_apply_discount_basic(self):
        self.assertEqual(apply_discount('10.00', 10), Decimal('9.00'))
        self.assertEqual(apply_discount('10.00', 0), Decimal('10.00'))
        self.assertEqual(apply_discount('10.00', 100), Decimal('0.00'))
        self.assertEqual(apply_discount('10.00'), Decimal('10.00'))

    def test_apply_discount_rounding(self):
        self.assertEqual(apply_discount('1.005', 10), Decimal('0.90'))
        self.assertEqual(apply_discount('1.005', 50), Decimal('0.50'))
        self.assertEqual(apply_discount('1.005', 33), Decimal('0.67'))

    def test_apply_discount_invalid(self):
        with self.assertRaises(ValueError):
            apply_discount('-1.00', 10)
        with self.assertRaises(ValueError):
            apply_discount('1.00', -1)
        with self.assertRaises(ValueError):
            apply_discount('1.00', 101)
        with self.assertRaises(ValueError):
            apply_discount('abc', 10)

    def test_line_total_basic(self):
        self.assertEqual(line_total('10.00', 3), Decimal('30.00'))
        self.assertEqual(line_total('10.00', 0), Decimal('0.00'))
        self.assertEqual(line_total('10.00', 3, 10), Decimal('27.00'))

    def test_line_total_no_double_rounding(self):
        self.assertEqual(line_total('1.005', 3, 10), Decimal('2.70'))

    def test_line_total_quantity_validation(self):
        with self.assertRaises(ValueError):
            line_total('1.00', -1)
        with self.assertRaises(ValueError):
            line_total('1.00', True)
        with self.assertRaises(ValueError):
            line_total('1.00', False)
        with self.assertRaises(ValueError):
            line_total('1.00', 1.5)
        with self.assertRaises(ValueError):
            line_total('1.00', '3')

    def test_line_total_price_validation(self):
        with self.assertRaises(ValueError):
            line_total('-1.00', 3)
        with self.assertRaises(ValueError):
            line_total('abc', 3)

    def test_line_total_discount_validation(self):
        with self.assertRaises(ValueError):
            line_total('1.00', 3, -1)
        with self.assertRaises(ValueError):
            line_total('1.00', 3, 101)

    def test_discounted_api(self):
        self.assertEqual(discounted('1.005'), Decimal('1.01'))
        self.assertEqual(discounted('10.00', 50), Decimal('5.00'))

    def test_invoice_total(self):
        self.assertEqual(invoice_total([{'price': '1.005', 'qty': 3}]), Decimal('3.03'))
        self.assertEqual(invoice_total([{'price': '10.00', 'qty': 2, 'discount': 10}]), Decimal('18.00'))
        self.assertEqual(invoice_total([]), Decimal('0.00'))

    def test_stock_value(self):
        self.assertEqual(stock_value([{'price': '2.005', 'qty': 2}]), Decimal('4.02'))
        self.assertEqual(stock_value([]), Decimal('0.00'))

    def test_checkout(self):
        result = checkout([{'price': '10', 'qty': 2}], 2)
        self.assertEqual(result, {'subtotal': '20.00', 'shipping': '7.50', 'total': '27.50'})

if __name__ == '__main__':
    unittest.main()
