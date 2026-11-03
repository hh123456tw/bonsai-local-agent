import unittest
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
