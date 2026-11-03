import unittest
from decimal import Decimal, ROUND_HALF_UP
from catalog.pricing import discounted
from catalog.orders import invoice_total
from catalog.inventory import stock_value
from catalog import checkout
from catalog.money import parse_money, apply_discount, line_total

def orig_discounted(p, pct=0):
    v=Decimal(str(p)); r=Decimal(str(pct))
    if v<0 or not 0<=r<=100: raise ValueError("invalid money")
    return (v*(1-r/100)).quantize(Decimal(".01"),rounding=ROUND_HALF_UP)

def orig_invoice(lines):
    res=Decimal("0.00")
    for row in lines:
        q=row["qty"]; v=Decimal(str(row["price"])); r=Decimal(str(row.get("discount",0)))
        if not isinstance(q,int) or isinstance(q,bool) or q<0: raise ValueError("invalid quantity")
        if v<0 or not 0<=r<=100: raise ValueError("invalid money")
        u=(v*(1-r/100)).quantize(Decimal(".01"),rounding=ROUND_HALF_UP)
        res+=u*q
    return res.quantize(Decimal(".01"))

def orig_stock(items):
    res=Decimal("0.00")
    for row in items:
        q=row["qty"]; v=Decimal(str(row["price"]))
        if not isinstance(q,int) or isinstance(q,bool) or q<0: raise ValueError("invalid quantity")
        if v<0: raise ValueError("invalid money")
        res+=(v.quantize(Decimal(".01"),rounding=ROUND_HALF_UP))*q
    return res.quantize(Decimal(".01"))

class Eq(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_money("1.005"), Decimal("1.01"))
        self.assertEqual(parse_money("1.004"), Decimal("1.00"))
        self.assertEqual(parse_money("0.005"), Decimal("0.01"))
        self.assertEqual(parse_money("0"), Decimal("0.00"))
        self.assertEqual(parse_money(Decimal("2.5")), Decimal("2.50"))
        for bad in ["abc","1.2.3","","None"]:
            with self.assertRaises(ValueError): parse_money(bad)
    def test_apply_discount_contract(self):
        self.assertEqual(apply_discount("1.005"), Decimal("1.01"))
        self.assertEqual(apply_discount("1.005",10), Decimal("0.90"))
        self.assertEqual(apply_discount("1.005",50), Decimal("0.50"))
        self.assertEqual(apply_discount("1.005",33.33), Decimal("0.67"))
        self.assertEqual(apply_discount("0.005",0), Decimal("0.01"))
        self.assertEqual(apply_discount("0.004",0), Decimal("0.00"))
        self.assertEqual(apply_discount("99.999",33.33), Decimal("66.67"))
        for bad in (-1, 100.001):
            with self.assertRaises(ValueError): apply_discount("1.00",bad)
        with self.assertRaises(ValueError): apply_discount("-0.01")
        self.assertEqual(apply_discount("1.00",100), Decimal("0.00"))
        self.assertEqual(apply_discount("1.00",0), Decimal("1.00"))
    def test_line_total_contract(self):
        self.assertEqual(line_total("1.005",3), Decimal("3.03"))
        self.assertEqual(line_total("1.005",3,10), Decimal("2.70"))
        self.assertEqual(line_total("1.005",0), Decimal("0.00"))
        for bad_q in [True, False, -1, 1.5, "2"]:
            with self.assertRaises(ValueError): line_total("1.00",bad_q)
        for bad_p in ["abc","-1.00"]:
            with self.assertRaises(ValueError): line_total(bad_p,2)
        for bad_d in [-1,101]:
            with self.assertRaises(ValueError): line_total("1.00",2,bad_d)
    def test_equivalence_discounted(self):
        for i in range(0,20000):
            p = Decimal(i)/1000
            for r in [0,1,5,10,15,25,33.33,50,66.67,75,99,100]:
                self.assertEqual(discounted(str(p),r), orig_discounted(str(p),r))
    def test_equivalence_invoice(self):
        import itertools
        prices=["1.005","0.005","2.005","99.999","0.004","0.006","10","0.01"]
        rows=[]
        for p in prices:
            for q in range(0,4):
                rows.append({"price":p,"qty":q})
                rows.append({"price":p,"qty":q,"discount":10})
                rows.append({"price":p,"qty":q,"discount":50})
        for n in range(1,4):
            for combo in itertools.product(rows, repeat=n):
                self.assertEqual(invoice_total(list(combo)), orig_invoice(list(combo)))
    def test_equivalence_stock(self):
        for i in range(0,20000):
            p=Decimal(i)/1000
            for q in range(0,5):
                item=[{"price":str(p),"qty":q}]
                self.assertEqual(stock_value(item), orig_stock(item))
    def test_checkout(self):
        self.assertEqual(checkout([{"price":"10","qty":2}],2),{"subtotal":"20.00","shipping":"7.50","total":"27.50"})
        self.assertEqual(checkout([{"price":"1.005","qty":3}],0.5),{"subtotal":"3.03","shipping":"5.63","total":"8.66"})
        self.assertEqual(checkout([{"price":"1.005","qty":3}],0.5,express=True),{"subtotal":"3.03","shipping":"11.25","total":"14.28"})
if __name__=="__main__":
    unittest.main(argv=[],exit=False,verbosity=2)
