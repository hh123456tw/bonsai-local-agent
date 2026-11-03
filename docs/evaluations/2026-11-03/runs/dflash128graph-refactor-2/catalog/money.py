"""Shared monetary helpers for the catalog package.

All money values are Decimal-based, converted via Decimal(str(value)) and
rounded to cents with ROUND_HALF_UP. Discount math is performed on the
unrounded input and the unit price is rounded only once, before it is
multiplied by quantity.
"""
from decimal import Decimal, ROUND_HALF_UP

_CENTS = Decimal('0.01')


def parse_money(value):
    """Convert a nonnegative monetary value to a Decimal rounded to cents."""
    value = Decimal(str(value))
    if value < 0:
        raise ValueError('invalid money')
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP)


def apply_discount(price, percent=0):
    """Return price reduced by percent, rounded to cents.

    The discount is computed from the unrounded input and the unit price
    is rounded only once, after the discount is applied.
    """
    value = Decimal(str(price))
    rate = Decimal(str(percent))
    if value < 0 or not 0 <= rate <= 100:
        raise ValueError('invalid money')
    return (value * (Decimal(1) - rate / Decimal(100))).quantize(
        _CENTS, rounding=ROUND_HALF_UP
    )


def line_total(price, quantity, discount=0):
    """Total for one line: discounted unit price times quantity.

    The unit price is rounded to cents before being multiplied by quantity.
    """
    unit = apply_discount(price, discount)
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
        raise ValueError('invalid quantity')
    return (unit * quantity).quantize(_CENTS, rounding=ROUND_HALF_UP)
