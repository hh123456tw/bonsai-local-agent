"""Generate deterministic disposable coding tasks and external acceptance tests."""
import pathlib,json,hashlib
BASE=pathlib.Path(__file__).resolve().parents[1]/'fixtures'
TASKS={
'bug':{
'files':{
'README.md':'business_days(start, end, holidays=()) counts both endpoint dates when weekdays and not holidays. Reversed ranges must raise ValueError. Run python -m unittest discover. Do not edit test_existing.py.\n',
'schedule.py':'''from datetime import timedelta
def business_days(start, end, holidays=()):
    if start > end:
        raise ValueError('reversed range')
    blocked = set(holidays)
    result = 0
    while start < end:
        if start.weekday() < 5 and start not in blocked:
            result += 1
        start += timedelta(days=1)
    return result
''',
'test_existing.py':'''import unittest
from datetime import date
from schedule import business_days
class Tests(unittest.TestCase):
 def test_same_weekday(self): self.assertEqual(business_days(date(2026,11,2),date(2026,11,2)),1)
 def test_week(self): self.assertEqual(business_days(date(2026,11,2),date(2026,11,6)),5)
 def test_holiday(self): self.assertEqual(business_days(date(2026,11,2),date(2026,11,6),[date(2026,11,4)]),4)
 def test_reversed(self):
  with self.assertRaises(ValueError): business_days(date(2026,11,6),date(2026,11,2))
'''
},
'prompt':'Fix the bug in business_days so the documented inclusive endpoint contract is met. Read the code, make the smallest correct change, and actually run python -m unittest discover. Do not modify test_existing.py or README.md. Do not install dependencies. Report what changed and the actual test result.',
'acceptance':'''import unittest
from datetime import date,timedelta
from schedule import business_days
class Acceptance(unittest.TestCase):
 def test_inclusive(self): self.assertEqual(business_days(date(2026,11,2),date(2026,11,2)),1)
 def test_weekend(self): self.assertEqual(business_days(date(2026,11,7),date(2026,11,8)),0)
 def test_endpoint_holiday(self): self.assertEqual(business_days(date(2026,11,2),date(2026,11,6),[date(2026,11,6)]),4)
 def test_reference(self):
  for days in (0,1,7,30,90):
   start=date(2026,9,3);end=start+timedelta(days=days);holidays={date(2026,9,4),date(2026,10,5)}
   want=sum((start+timedelta(days=i)).weekday()<5 and (start+timedelta(days=i)) not in holidays for i in range(days+1))
   self.assertEqual(business_days(start,end,holidays),want)
'''
},
'feature':{
'files':{
'README.md':'Ledger processing library. Existing parse_csv, total, and render_report behavior is public. Run python -m unittest discover. Preserve test_existing.py and this README.\n',
'ledger/__init__.py':'from .parser import parse_csv\nfrom .summary import total\nfrom .cli import render_report\n',
'ledger/models.py':'''from dataclasses import dataclass
from datetime import date
from decimal import Decimal
@dataclass(frozen=True)
class Entry:
    account: str
    amount: Decimal
    day: date
    status: str = 'posted'
''',
'ledger/parser.py':'''import csv,io
from datetime import date
from decimal import Decimal
from .models import Entry
def parse_csv(text):
    return [Entry(row['account'],Decimal(row['amount']),date.fromisoformat(row['day']),row.get('status') or 'posted') for row in csv.DictReader(io.StringIO(text))]
''',
'ledger/summary.py':'''from decimal import Decimal
def total(entries):
    return sum((e.amount for e in entries),Decimal('0'))
''',
'ledger/cli.py':'''import json
from .parser import parse_csv
from .summary import total
def render_report(text):
    return json.dumps({'total':format(total(parse_csv(text)),'.2f')},sort_keys=True)
''',
'test_existing.py':'''import unittest,json
from decimal import Decimal
from ledger import parse_csv,total,render_report
DATA='account,amount,day,status\\na,1.20,2026-01-01,posted\\nb,2.30,2026-01-02,pending\\n'
class Tests(unittest.TestCase):
 def test_parse(self): self.assertEqual(len(parse_csv(DATA)),2)
 def test_total_legacy(self): self.assertEqual(total(parse_csv(DATA)),Decimal('3.50'))
 def test_report_legacy(self): self.assertEqual(json.loads(render_report(DATA)),{'total':'3.50'})
'''
},
'prompt':'''Add currency-aware reporting to the ledger project. Preserve existing public behavior of parse_csv, total and render_report(text). Add Entry.currency defaulting to USD; CSV currency is optional, normalized uppercase and must be exactly three ASCII letters (invalid codes raise ValueError). Add ledger.summary.totals_by_currency(entries, start=None, end=None, include_pending=False): sum Decimal amounts by currency, include posted entries only by default, optional inclusive datetime.date bounds, reject reversed bounds, return a dictionary; include_pending=True includes all statuses. Extend render_report(text, *, by_currency=False, start=None, end=None): old default JSON unchanged; by_currency=True returns {'totals': {'USD':'1.20', ...}} with amounts formatted to two decimals and date filters applied. Preserve legacy total including pending entries. Create test_currency.py covering new behavior and run all tests. Do not modify test_existing.py or README.md, do not install dependencies. Actually edit multiple modules and report tests.''',
'acceptance':'''import unittest,json,importlib,pathlib
from datetime import date
from decimal import Decimal
from ledger import parse_csv,total,render_report
DATA='account,amount,day,status,currency\\na,1.10,2026-01-01,posted,usd\\nb,2.20,2026-01-02,posted,EUR\\nc,4.40,2026-01-03,pending,usd\\nd,-0.10,2026-01-04,posted,USD\\n'
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
'''
},
'refactor':{
'files':{
'README.md':'Catalog library. Preserve all public signatures and behavior, Decimal ROUND_HALF_UP to cents, quantity int>=0 (bool invalid), discount 0..100, price>=0. Consolidate duplicated money logic in catalog/money.py. Preserve existing tests.\n',
'catalog/__init__.py':'from .api import checkout\n',
'catalog/models.py':'from dataclasses import dataclass\n@dataclass(frozen=True)\nclass Product:\n    sku: str\n    price: str\n',
'catalog/pricing.py':'''from decimal import Decimal,ROUND_HALF_UP
def discounted(price,percent=0):
    value=Decimal(str(price)); rate=Decimal(str(percent))
    if value<0 or not 0<=rate<=100: raise ValueError('invalid money')
    return (value*(1-rate/100)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
''',
'catalog/orders.py':'''from decimal import Decimal,ROUND_HALF_UP
def invoice_total(lines):
    result=Decimal('0.00')
    for row in lines:
        qty=row['qty'];value=Decimal(str(row['price']));rate=Decimal(str(row.get('discount',0)))
        if not isinstance(qty,int) or isinstance(qty,bool) or qty<0: raise ValueError('invalid quantity')
        if value<0 or not 0<=rate<=100: raise ValueError('invalid money')
        unit=(value*(1-rate/100)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
        result+=unit*qty
    return result.quantize(Decimal('.01'))
''',
'catalog/inventory.py':'''from decimal import Decimal,ROUND_HALF_UP
def stock_value(items):
    result=Decimal('0.00')
    for row in items:
        qty=row['qty'];value=Decimal(str(row['price']))
        if not isinstance(qty,int) or isinstance(qty,bool) or qty<0: raise ValueError('invalid quantity')
        if value<0: raise ValueError('invalid money')
        result+=value.quantize(Decimal('.01'),rounding=ROUND_HALF_UP)*qty
    return result.quantize(Decimal('.01'))
''',
'catalog/shipping.py':'''from decimal import Decimal,ROUND_HALF_UP
def quote(weight,express=False):
    weight=Decimal(str(weight))
    if weight<0:raise ValueError('invalid weight')
    return ((Decimal('5')+weight*Decimal('1.25'))*(2 if express else 1)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
''',
'catalog/reporting.py':'from .orders import invoice_total\ndef format_total(lines):\n    return "$"+format(invoice_total(lines),".2f")\n',
'catalog/api.py':'from .orders import invoice_total\nfrom .shipping import quote\ndef checkout(lines,weight,express=False):\n    subtotal=invoice_total(lines);delivery=quote(weight,express)\n    return {"subtotal":format(subtotal,".2f"),"shipping":format(delivery,".2f"),"total":format(subtotal+delivery,".2f")}\n',
'test_existing.py':'''import unittest
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
'''
},
'prompt':'''Refactor the catalog project to remove duplicated monetary calculation logic while preserving all public APIs and behavior. Add catalog/money.py exporting parse_money(value), apply_discount(price, percent=0), and line_total(price, quantity, discount=0). Money uses Decimal(str(value)), cent rounding ROUND_HALF_UP; round discounted unit price before multiplying quantity. Explicit new-helper contract: parse_money('1.005') must return Decimal('1.01'), rounded to cents; apply_discount and line_total must compute discounts from the unrounded input before rounding the unit price, so do not introduce double rounding. Nonnegative prices, discounts 0..100, integer quantity>=0 excluding bool; invalid inputs raise ValueError as before. Update pricing, orders and inventory to import and use the shared module; preserve shipping, reporting, checkout behavior and original signatures. At least these three modules must use money.py; do not just add an unused helper. Keep all eight original catalog modules. Do not change test_existing.py or README.md. You may add tests. Run the complete unittest suite and report actual results. No dependencies or GUI needed.''',
'acceptance':'''import unittest,pathlib,ast
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
'''
}}
def main():
 for name,task in TASKS.items():
  dest=BASE/name/'start';dest.mkdir(parents=True,exist_ok=True)
  for path,text in task['files'].items():
   p=dest/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
  (BASE/name/'acceptance.py').write_text(task['acceptance'],encoding='utf-8');(BASE/name/'prompt.txt').write_text(task['prompt'],encoding='utf-8')
  manifest={path:hashlib.sha256((dest/path).read_bytes()).hexdigest() for path in task['files']};(BASE/name/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 print('Prepared three disposable projects; acceptance tests stay outside agent workspace.')
if __name__=='__main__':main()
