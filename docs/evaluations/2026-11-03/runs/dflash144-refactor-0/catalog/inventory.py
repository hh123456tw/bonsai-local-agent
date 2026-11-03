from decimal import Decimal

from .money import parse_money


def stock_value(items):
    result = Decimal("0.00")
    for row in items:
        qty = row["qty"]
        value = parse_money(row["price"])
        result += value * qty
    return result.quantize(Decimal(".01"))