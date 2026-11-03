from decimal import Decimal, ROUND_HALF_UP
from catalog.inventory import stock_value
def orig_stock(items):
    result=Decimal("0.00")
    for row in items:
        qty=row["qty"];value=Decimal(str(row["price"]))
        if not isinstance(qty,int) or isinstance(qty,bool) or qty<0: raise ValueError("invalid quantity")
        if value<0: raise ValueError("invalid money")
        result+=value.quantize(Decimal(".01"),rounding=ROUND_HALF_UP)*qty
    return result.quantize(Decimal(".01"))
def run(name, fn, *a):
    try:
        print(name, "->", repr(fn(*a)))
    except Exception as e:
        print(name, "->", type(e).__name__, repr(e.args[0]) if e.args else "")
for a in [[{"price":"2.005","qty":2}],[{"price":"abc","qty":True}],[{"price":"-1","qty":True}],[{"price":"1.00","qty":True}],[{"price":"abc","qty":1}],[{"price":"-1","qty":1}]]:
    run("new", stock_value, a)
    run("orig", orig_stock, a)
