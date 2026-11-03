from decimal import Decimal

from .money import line_total


def invoice_total(lines):
    result = Decimal("0.00")
    for row in lines:
        qty = row["qty"]
        value = row["price"]
        discount = row.get("discount", 0)
        unit = line_total(value, qty, discount)
        result += unit
    return result.quantize(Decimal(".01"))