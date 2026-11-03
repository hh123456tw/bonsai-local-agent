from decimal import Decimal

from .money import parse_money


def stock_value(items):
    """Return the total value of inventory, rounded to cents."""
    result = Decimal("0.00")
    for row in items:
        qty = row["qty"]
        if not isinstance(qty, int) or isinstance(qty, bool) or qty < 0:
            raise ValueError("invalid quantity")
        result += parse_money(row["price"]) * qty
    return result.quantize(Decimal("0.01"))
