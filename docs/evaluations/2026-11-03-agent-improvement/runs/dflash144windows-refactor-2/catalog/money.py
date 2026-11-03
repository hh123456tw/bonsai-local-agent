"""Shared monetary helpers for the catalog.

All money math uses Decimal(str(value)) and rounds to cents with
ROUND_HALF_UP. Discounted unit prices are rounded once, before being
multiplied by quantity, so no double rounding occurs.
"""
from decimal import Decimal, ROUND_HALF_UP

_CENTS = Decimal(".01")


def parse_money(value):
    """Parse a money value into a Decimal using Decimal(str(value))."""
    return Decimal(str(value))


def apply_discount(price, percent=0):
    """Return price discounted by percent (0..100), rounded to cents.

    The discount is applied to the unrounded price before the single
    cent rounding, so no double rounding occurs.
    """
    value = parse_money(price)
    rate = Decimal(str(percent))
    if value < 0 or not 0 <= rate <= 100:
        raise ValueError('invalid money')
    return (value * (1 - rate / 100)).quantize(_CENTS, rounding=ROUND_HALF_UP)


def line_total(price, quantity, discount=0):
    """Total for one line: discounted unit price times quantity.

    The unit price is discounted and rounded to cents first, then
    multiplied by quantity (no intermediate double rounding).
    """
    value = parse_money(price)
    rate = Decimal(str(discount))
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
        raise ValueError('invalid quantity')
    if value < 0 or not 0 <= rate <= 100:
        raise ValueError('invalid money')
    unit = (value * (1 - rate / 100)).quantize(_CENTS, rounding=ROUND_HALF_UP)
    return (unit * quantity).quantize(_CENTS, rounding=ROUND_HALF_UP)
