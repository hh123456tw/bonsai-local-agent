from decimal import Decimal,ROUND_HALF_UP
from .money import parse_money

_CENTS = Decimal('.01')

def stock_value(items):
    result=Decimal('0.00')
    for row in items:
        qty=row['qty'];value=parse_money(row['price'])
        if not isinstance(qty,int) or isinstance(qty,bool) or qty<0: raise ValueError('invalid quantity')
        if value<0: raise ValueError('invalid money')
        result+=value.quantize(_CENTS,rounding=ROUND_HALF_UP)*qty
    return result.quantize(_CENTS,rounding=ROUND_HALF_UP)
