from decimal import Decimal,ROUND_HALF_UP
def invoice_total(lines):
    result=Decimal('0.00')
    for row in lines:
        qty=row['qty'];value=Decimal(str(row['price']));rate=Decimal(str(row.get('discount',0)))
        if not isinstance(qty,int) or isinstance(qty,bool) or qty<0: raise ValueError('invalid quantity')
        if value<0 or not 0<=rate<=100: raise ValueError('invalid money')
        unit=(value*(1-rate/100)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
        result+=unit*qty
    return result.quantize(Decimal('.01'))
