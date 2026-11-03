from decimal import Decimal
from .money import line_total


def invoice_total(lines):
    result = Decimal('0.00')
    for row in lines:
        qty = row['qty']
        if not isinstance(qty, int) or isinstance(qty, bool) or qty < 0:
            raise ValueError('invalid quantity')
        result += line_total(row['price'], qty, row.get('discount', 0))
    return result.quantize(Decimal('.01'))
