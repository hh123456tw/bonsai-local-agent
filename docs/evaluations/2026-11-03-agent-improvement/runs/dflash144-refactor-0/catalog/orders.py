"""Order invoice totals built on the shared money module."""
from decimal import Decimal
from .money import line_total


def invoice_total(lines):
    result = Decimal('0.00')
    for row in lines:
        result += line_total(row['price'], row['qty'], row.get('discount', 0))
    return result.quantize(Decimal('0.01'))
