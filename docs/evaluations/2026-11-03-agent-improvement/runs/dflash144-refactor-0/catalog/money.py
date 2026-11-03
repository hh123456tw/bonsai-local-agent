"""Shared monetary helpers: parse, discount, and line totals with ROUND_HALF_UP cents."""
from decimal import Decimal, ROUND_HALF_UP

CENTS = Decimal('0.01')


def parse_money(value):
    """Parse a monetary value into a Decimal rounded to cents (ROUND_HALF_UP)."""
    value = Decimal(str(value))
    if value < 0:
        raise ValueError('invalid money')
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)


def apply_discount(price, percent=0):
    """Return the discounted unit price, rounded to cents (ROUND_HALF_UP)."""
    price = Decimal(str(price))
    rate = Decimal(str(percent))
    if price < 0 or not 0 <= rate <= 100:
        raise ValueError('invalid money')
    return (price * (1 - rate / 100)).quantize(CENTS, rounding=ROUND_HALF_UP)


def line_total(price, quantity, discount=0):
    """Total for one line: discounted unit price (rounded to cents) times quantity."""
    qty = quantity
    if not isinstance(qty, int) or isinstance(qty, bool) or qty < 0:
        raise ValueError('invalid quantity')
    unit = apply_discount(price, discount)
    return (unit * qty).quantize(CENTS, rounding=ROUND_HALF_UP)
