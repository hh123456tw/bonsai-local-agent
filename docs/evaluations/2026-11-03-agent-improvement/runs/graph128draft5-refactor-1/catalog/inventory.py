from .money import parse_money

from decimal import Decimal


def stock_value(items):
    result = Decimal('0.00')
    for row in items:
        qty = row['qty']
        if not isinstance(qty, int) or isinstance(qty, bool) or qty < 0:
            raise ValueError('invalid quantity')
        price = parse_money(row['price'])
        result += price * qty
    return result.quantize(Decimal('.01'))
