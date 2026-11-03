from decimal import Decimal

from .money import parse_money


def stock_value(items):
    """Total value of inventory, each line rounded to cents then summed."""
    result = Decimal('0.00')
    for row in items:
        qty = row['qty']
        price = row['price']
        value = parse_money(price)
        if not isinstance(qty, int) or isinstance(qty, bool) or qty < 0:
            raise ValueError('invalid quantity')
        result += value * qty
    return result.quantize(Decimal('.01'))
