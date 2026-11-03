"""Shared monetary calculations for the catalog package.

All money is handled as Decimal with ROUND_HALF_UP to cents.  Discount
rates are applied to the unrounded input value so that no double
rounding occurs; each helper rounds its result to cents once.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENTS = Decimal('0.01')


def parse_money(value):
    """Parse a money value into a Decimal rounded to cents."""
    try:
        value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError('invalid money')
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)


def apply_discount(price, percent=0):
    """Return the discounted unit price, rounded to cents.

    The discount is computed from the unrounded input value so that the
    result matches the original single-rounding behavior.
    """
    try:
        value = Decimal(str(price))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError('invalid money')
    rate = Decimal(str(percent))
    if value < 0 or not 0 <= rate <= 100:
        raise ValueError('invalid money')
    return (value * (1 - rate / 100)).quantize(CENTS, rounding=ROUND_HALF_UP)


def line_total(price, quantity, discount=0):
    """Total for one line: discounted unit price times quantity."""
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
        raise ValueError('invalid quantity')
    unit = apply_discount(price, discount)
    return (unit * quantity).quantize(CENTS, rounding=ROUND_HALF_UP)
