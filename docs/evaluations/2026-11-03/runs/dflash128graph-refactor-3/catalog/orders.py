from decimal import Decimal, ROUND_HALF_UP
from .money import line_total


def invoice_total(lines):
    result = Decimal('0.00')
    for row in lines:
        qty = row['qty']
        value = Decimal(str(row['price']))
        rate = Decimal(str(row.get('discount', 0)))
        if not isinstance(qty, int) or isinstance(qty, bool) or qty < 0:
            raise ValueError('invalid quantity')
        if value < 0 or not 0 <= rate <= 100:
            raise ValueError('invalid money')
        result += line_total(row['price'], qty, row.get('discount', 0))
    return result.quantize(Decimal('.01'))
