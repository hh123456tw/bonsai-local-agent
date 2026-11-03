from decimal import Decimal

from .money import parse_money


def stock_value(items):
    """Public API: total value of all stocked items, rounded to cents."""
    total = Decimal("0.00")
    for item in items:
        qty = item["qty"]
        if not isinstance(qty, int) or isinstance(qty, bool) or qty < 0:
            raise ValueError("invalid quantity")
        total += parse_money(item["price"]) * qty
    return total.quantize(Decimal("0.01"))
