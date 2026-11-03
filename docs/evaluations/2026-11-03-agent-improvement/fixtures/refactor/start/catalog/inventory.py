from decimal import Decimal,ROUND_HALF_UP
def stock_value(items):
    result=Decimal('0.00')
    for row in items:
        qty=row['qty'];value=Decimal(str(row['price']))
        if not isinstance(qty,int) or isinstance(qty,bool) or qty<0: raise ValueError('invalid quantity')
        if value<0: raise ValueError('invalid money')
        result+=value.quantize(Decimal('.01'),rounding=ROUND_HALF_UP)*qty
    return result.quantize(Decimal('.01'))
