import unittest
from datetime import date
from schedule import business_days
class Tests(unittest.TestCase):
 def test_same_weekday(self): self.assertEqual(business_days(date(2026,11,2),date(2026,11,2)),1)
 def test_week(self): self.assertEqual(business_days(date(2026,11,2),date(2026,11,6)),5)
 def test_holiday(self): self.assertEqual(business_days(date(2026,11,2),date(2026,11,6),[date(2026,11,4)]),4)
 def test_reversed(self):
  with self.assertRaises(ValueError): business_days(date(2026,11,6),date(2026,11,2))
