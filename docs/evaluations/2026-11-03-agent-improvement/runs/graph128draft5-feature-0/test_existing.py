import unittest,json
from decimal import Decimal
from ledger import parse_csv,total,render_report
DATA='account,amount,day,status\na,1.20,2026-01-01,posted\nb,2.30,2026-01-02,pending\n'
class Tests(unittest.TestCase):
 def test_parse(self): self.assertEqual(len(parse_csv(DATA)),2)
 def test_total_legacy(self): self.assertEqual(total(parse_csv(DATA)),Decimal('3.50'))
 def test_report_legacy(self): self.assertEqual(json.loads(render_report(DATA)),{'total':'3.50'})
