import unittest
from decimal import Decimal
from catalog.pricing import discounted
from catalog.orders import invoice_total
from catalog.inventory import stock_value
from catalog import checkout
class Tests(unittest.TestCase):
 def test_discount(self): self.assertEqual(discounted('1.005'),Decimal('1.01'))
 def test_invoice(self):self.assertEqual(invoice_total([{'price':'1.005','qty':3}]),Decimal('3.03'))
 def test_stock(self):self.assertEqual(stock_value([{'price':'2.005','qty':2}]),Decimal('4.02'))
 def test_checkout(self):self.assertEqual(checkout([{'price':'10','qty':2}],2),{'subtotal':'20.00','shipping':'7.50','total':'27.50'})
