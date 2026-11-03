from decimal import Decimal
from .money import line_total


def invoice_total(lines):
    result = Decimal('0.00')
    for row in lines:
        qty = row['qty']
        value = Decimal(str(row['price']))
        if not isinstance(qty, int) or isinstance(qty, bool) or qty < 0:
            raise ValueError('invalid quantity')
        if value < 0:
            raise ValueError('invalid money')
        result += line_total(value, qty, discount=row.get('discount', 0))
    return result.quantize(Decimal('.00'))
