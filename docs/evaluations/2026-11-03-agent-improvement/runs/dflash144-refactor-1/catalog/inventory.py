from decimal import Decimal, ROUND_HALF_UP
from .money import line_total


def stock_value(items):
    result = Decimal('0.00')
    for row in items:
        qty = row['qty']
        if not isinstance(qty, int) or isinstance(qty, bool) or qty < 0:
            raise ValueError('invalid quantity')
        result += line_total(row['price'], qty)
    return result.quantize(Decimal('.01'))
