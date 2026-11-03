import unittest,pathlib,ast
from decimal import Decimal
from catalog.pricing import discounted
from catalog.orders import invoice_total
from catalog.inventory import stock_value
from catalog.reporting import format_total
from catalog.shipping import quote
from catalog import checkout
class Acceptance(unittest.TestCase):
 def test_money_api(self):
  from catalog.money import parse_money,apply_discount,line_total
  self.assertEqual(parse_money('1.005'),Decimal('1.01'));self.assertEqual(apply_discount('10',25),Decimal('7.50'));self.assertEqual(line_total('1.005',3),Decimal('3.03'))
 def test_edges(self):
  self.assertEqual(discounted('0.05',10),Decimal('0.05'));self.assertEqual(discounted('12.34',100),Decimal('0.00'))
 def test_invalid(self):
  for row in ({'price':1,'qty':True},{'price':1,'qty':-1},{'price':1,'qty':1.5},{'price':-1,'qty':1},{'price':1,'qty':1,'discount':101}):
   with self.assertRaises(ValueError):invoice_total([row])
 def test_empty(self):self.assertEqual(invoice_total([]),Decimal('0.00'));self.assertEqual(stock_value([]),Decimal('0.00'))
 def test_reporting(self):self.assertEqual(format_total([{'price':'3.335','qty':2}]),'$6.68')
 def test_discount_reference(self):
  from decimal import ROUND_HALF_UP
  for price in ('1.005','3.335','110.005'):
   for rate in ('0','7.5','10','50'):
    want=(Decimal(price)*(1-Decimal(rate)/100)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
    self.assertEqual(discounted(price,rate),want)
 def test_shipping(self):self.assertEqual(quote('2',True),Decimal('15.00'))
 def test_api(self):self.assertEqual(checkout([{'price':'5','qty':2,'discount':10}],0)['total'],'14.00')
 def test_real_refactor(self):
  for name in ('pricing','orders','inventory'):
   tree=ast.parse(pathlib.Path('catalog',name+'.py').read_text(encoding='utf-8'))
   direct=set();modules=set()
   for n in ast.walk(tree):
    if isinstance(n,ast.ImportFrom) and 'money' in (n.module or ''):direct.update(x.asname or x.name for x in n.names)
    if isinstance(n,ast.ImportFrom):modules.update(x.asname or x.name for x in n.names if x.name=='money')
    if isinstance(n,ast.Import):modules.update(x.asname or x.name.split('.')[-1] for x in n.names if x.name.endswith('money'))
   used=any(isinstance(n,ast.Call) and ((isinstance(n.func,ast.Name) and n.func.id in direct) or (isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id in modules)) for n in ast.walk(tree))
   self.assertTrue(used,name)
 def test_modules_preserved(self):
  for name in ('__init__','models','pricing','orders','inventory','shipping','reporting','api'):self.assertTrue(pathlib.Path('catalog',name+'.py').is_file())
