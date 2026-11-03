from decimal import Decimal

from .money import line_total


def invoice_total(lines):
    """Public API: sum of per-line totals for an order."""
    total = Decimal("0.00")
    for row in lines:
        total += line_total(row["price"], row["qty"], row.get("discount", 0))
    return total.quantize(Decimal(".01"))
