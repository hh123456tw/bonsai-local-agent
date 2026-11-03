"""Prove external graders reject baselines and accept independent reference implementations."""
import pathlib,shutil,subprocess,sys,json
from lab import LAB,dump
def check(task,reference):
 base=LAB/'fixtures'/task/'start';dest=LAB/'calibration'/task
 if dest.exists():raise RuntimeError('Calibration already exists; use a fresh evaluation directory')
 shutil.copytree(base,dest,ignore=shutil.ignore_patterns('__pycache__'))
 baseline=subprocess.run([sys.executable,str(LAB/'scripts/accept.py'),str(base),str(LAB/'fixtures'/task/'acceptance.py')],cwd=base,capture_output=True,text=True)
 for path,text in reference.items():(dest/path).write_text(text,encoding='utf-8')
 result=subprocess.run([sys.executable,str(LAB/'scripts/accept.py'),str(dest),str(LAB/'fixtures'/task/'acceptance.py')],cwd=dest,capture_output=True,text=True)
 (LAB/'logs'/f'calibration-{task}.txt').write_text('BASELINE\n'+baseline.stdout+baseline.stderr+'\nREFERENCE\n'+result.stdout+result.stderr,encoding='utf-8')
 assert baseline.returncode!=0,task+' grader did not reject baseline'
 assert result.returncode==0,task+' reference failed: '+result.stderr
 return {'task':task,'baseline_rejected':True,'reference_passed':True,'acceptance':json.loads(result.stdout.strip().splitlines()[-1])}
if __name__=='__main__':
 rows=[]
 bug=(LAB/'fixtures/bug/start/schedule.py').read_text().replace('while start < end:','while start <= end:');rows.append(check('bug',{'schedule.py':bug}))
 models=(LAB/'fixtures/feature/start/ledger/models.py').read_text()+"    currency: str = 'USD'\n"
 parser="""import csv,io,re
from datetime import date
from decimal import Decimal
from .models import Entry
def parse_csv(text):
 result=[]
 for row in csv.DictReader(io.StringIO(text)):
  currency=(row.get('currency') or 'USD').upper()
  if not re.fullmatch('[A-Z]{3}',currency):raise ValueError('invalid currency')
  result.append(Entry(row['account'],Decimal(row['amount']),date.fromisoformat(row['day']),row.get('status') or 'posted',currency))
 return result
"""
 summary=(LAB/'fixtures/feature/start/ledger/summary.py').read_text()+"""
def totals_by_currency(entries,start=None,end=None,include_pending=False):
 if start is not None and end is not None and start>end:raise ValueError('reversed bounds')
 result={}
 for e in entries:
  if not include_pending and e.status!='posted':continue
  if start is not None and e.day<start:continue
  if end is not None and e.day>end:continue
  result[e.currency]=result.get(e.currency,Decimal('0'))+e.amount
 return dict(sorted(result.items()))
"""
 cli="""import json
from .parser import parse_csv
from .summary import total,totals_by_currency
def render_report(text,*,by_currency=False,start=None,end=None):
 rows=parse_csv(text)
 if by_currency:return json.dumps({'totals':{k:format(v,'.2f') for k,v in totals_by_currency(rows,start,end).items()}},sort_keys=True)
 return json.dumps({'total':format(total(rows),'.2f')},sort_keys=True)
"""
 tests="""import unittest
from ledger import parse_csv
from ledger.models import Entry
from decimal import Decimal
from datetime import date
class Tests(unittest.TestCase):
 def test_default(self):self.assertEqual(Entry('a',Decimal('1'),date(2026,1,1)).currency,'USD')
 def test_normalization(self):self.assertEqual(parse_csv('account,amount,day,currency\\na,1,2026-01-01,eur\\n')[0].currency,'EUR')
 def test_invalid(self):
  with self.assertRaises(ValueError):parse_csv('account,amount,day,currency\\na,1,2026-01-01,U1D\\n')
"""
 rows.append(check('feature',{'ledger/models.py':models,'ledger/parser.py':parser,'ledger/summary.py':summary,'ledger/cli.py':cli,'test_currency.py':tests}))
 money="""from decimal import Decimal,ROUND_HALF_UP
def parse_money(value):
 value=Decimal(str(value))
 if value<0:raise ValueError('invalid money')
 return value.quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
def apply_discount(price,percent=0):
 value=Decimal(str(price));rate=Decimal(str(percent))
 if value<0 or not 0<=rate<=100:raise ValueError('invalid money')
 return (value*(1-rate/100)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
def line_total(price,quantity,discount=0):
 if not isinstance(quantity,int) or isinstance(quantity,bool) or quantity<0:raise ValueError('invalid quantity')
 return (apply_discount(price,discount)*quantity).quantize(Decimal('.01'))
"""
 rows.append(check('refactor',{'catalog/money.py':money,'catalog/pricing.py':'from .money import apply_discount\ndef discounted(price,percent=0):return apply_discount(price,percent)\n','catalog/orders.py':"from decimal import Decimal\nfrom .money import line_total\ndef invoice_total(lines):return sum((line_total(r['price'],r['qty'],r.get('discount',0)) for r in lines),Decimal('0.00'))\n",'catalog/inventory.py':"from decimal import Decimal\nfrom .money import line_total\ndef stock_value(items):return sum((line_total(r['price'],r['qty']) for r in items),Decimal('0.00'))\n"}))
 dump(LAB/'grader-calibration.json',rows);print(json.dumps(rows))
