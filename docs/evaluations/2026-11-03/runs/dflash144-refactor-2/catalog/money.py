"""Shared monetary helpers for the catalog.

All money is represented as decimal.Decimal and rounded to cents
using ROUND_HALF_UP. Discount calculations are performed on the unrounded
input before the unit price is rounded, so no double rounding is introduced.
"""
from decimal import Decimal, ROUND_HALF_UP

_CENTS = Decimal('0.01')


def parse_money(value):
    value = Decimal(str(value))
    if value < 0:
        raise ValueError('invalid money')
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP)


def apply_discount(price, percent=0):
    value = Decimal(str(price))
    rate = Decimal(str(percent))
    if value < 0 or not 0 <= rate <= 100:
        raise ValueError('invalid money')
    return (value * (1 - rate / 100)).quantize(_CENTS, rounding=ROUND_HALF_UP)


def line_total(price, quantity, discount=0):
    qty = quantity
    if not isinstance(qty, int) or isinstance(qty, bool) or qty < 0:
        raise ValueError('invalid quantity')
    return apply_discount(price, discount) * qty
