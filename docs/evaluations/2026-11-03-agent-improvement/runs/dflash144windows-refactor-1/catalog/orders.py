from decimal import Decimal

from .money import line_total


def invoice_total(lines):
    """Total for an order, computed from each line item."""
    result = Decimal('0.00')
    for row in lines:
        qty = row['qty']
        price = row['price']
        discount = row.get('discount', 0)
        result += line_total(price, qty, discount)
    return result.quantize(Decimal('.01'))
