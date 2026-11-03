from decimal import Decimal
from .money import parse_money

def stock_value(items):
    result=Decimal('0.00')
    for row in items:
        qty=row['qty']
        if not isinstance(qty,int) or isinstance(qty,bool) or qty<0: raise ValueError('invalid quantity')
        value=parse_money(row['price'])
        if value<0: raise ValueError('invalid money')
        result+=value*qty
    return result.quantize(Decimal('.01'))
