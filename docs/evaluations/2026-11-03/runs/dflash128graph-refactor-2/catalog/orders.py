from decimal import Decimal

from .money import line_total


def invoice_total(lines):
    """Sum the discounted line totals for an order."""
    result = Decimal('0.00')
    for row in lines:
        result += line_total(row['price'], row['qty'], row.get('discount', 0))
    return result.quantize(Decimal('0.01'))
