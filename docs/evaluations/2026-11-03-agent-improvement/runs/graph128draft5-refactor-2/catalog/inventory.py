from decimal import Decimal
from .money import line_total


def stock_value(items):
    result = Decimal("0.00")
    for row in items:
        result += line_total(row["price"], row["qty"])
    return result.quantize(Decimal(".01"))
