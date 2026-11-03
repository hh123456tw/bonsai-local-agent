from decimal import Decimal, ROUND_HALF_UP
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
run("stock 2.005x2", orig_stock, [{"price":"2.005","qty":2}])
run("stock badprice+badqty", orig_stock, [{"price":"abc","qty":True}])
run("stock negprice+badqty", orig_stock, [{"price":"-1","qty":True}])
run("stock badqty only", orig_stock, [{"price":"1.00","qty":True}])
run("stock badprice only", orig_stock, [{"price":"abc","qty":1}])
run("stock negprice only", orig_stock, [{"price":"-1","qty":1}])
