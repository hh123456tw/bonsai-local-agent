import unittest,json,importlib,pathlib
from datetime import date
from decimal import Decimal
from ledger import parse_csv,total,render_report
DATA='account,amount,day,status,currency\na,1.10,2026-01-01,posted,usd\nb,2.20,2026-01-02,posted,EUR\nc,4.40,2026-01-03,pending,usd\nd,-0.10,2026-01-04,posted,USD\n'
class Acceptance(unittest.TestCase):
 def test_defaults(self):
  from ledger.models import Entry
  self.assertEqual(Entry('a',Decimal('1'),date(2026,1,1)).currency,'USD')
 def test_parse(self): self.assertEqual(parse_csv(DATA)[0].currency,'USD')
 def test_sum(self):
  f=importlib.import_module('ledger.summary').totals_by_currency
  self.assertEqual(f(parse_csv(DATA)),{'USD':Decimal('1.00'),'EUR':Decimal('2.20')})
 def test_bounds(self):
  f=importlib.import_module('ledger.summary').totals_by_currency
  self.assertEqual(f(parse_csv(DATA),date(2026,1,2),date(2026,1,3)),{'EUR':Decimal('2.20')})
  with self.assertRaises(ValueError):f(parse_csv(DATA),date(2026,1,3),date(2026,1,2))
 def test_pending(self):
  f=importlib.import_module('ledger.summary').totals_by_currency
  self.assertEqual(f(parse_csv(DATA),include_pending=True)['USD'],Decimal('5.40'))
 def test_invalid(self):
  for value in ('US','U1D','ＥＵＲ','USDD'):
   with self.assertRaises(ValueError): parse_csv(DATA.replace(',usd',','+value))
 def test_report(self): self.assertEqual(json.loads(render_report(DATA,by_currency=True)),{'totals':{'EUR':'2.20','USD':'1.00'}})
 def test_legacy(self): self.assertEqual(json.loads(render_report(DATA)),{'total':'7.60'})
 def test_authored_tests(self):
  import ast
  p=pathlib.Path('test_currency.py');self.assertTrue(p.is_file())
  self.assertGreaterEqual(sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_') for n in ast.walk(ast.parse(p.read_text(encoding='utf-8')))),3)
