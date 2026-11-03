"""Shared monetary helpers for the catalog.

All money is handled with Decimal and rounded to cents using ROUND_HALF_UP.
This module is the single source of truth for money math so that pricing,
orders and inventory all behave identically.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENTS = Decimal("0.01")


def _to_decimal(value):
    """Convert a scalar to Decimal via its string form.

    Raises InvalidOperation for values that cannot be parsed, matching the
    behaviour of the original per-module implementations.
    """
    return Decimal(str(value))


def parse_money(value):
    """Return value as a Decimal rounded to the nearest cent.

    >>> parse_money('1.005')
    Decimal('1.01')
    """
    amount = _to_decimal(value)
    if amount < 0:
        raise ValueError('invalid money')
    return amount.quantize(CENTS, rounding=ROUND_HALF_UP)


def apply_discount(price, percent=0):
    """Discount price by percent (0..100) and round to cents.

    The discount is computed from the unrounded price and the result is
    rounded to cents exactly once, so callers never suffer double rounding.
    """
    value = _to_decimal(price)
    rate = _to_decimal(percent)
    if value < 0 or not 0 <= rate <= 100:
        raise ValueError('invalid money')
    return (value * (1 - rate / 100)).quantize(CENTS, rounding=ROUND_HALF_UP)


def line_total(price, quantity, discount=0):
    """Total for one line item: discounted unit price times quantity.

    The discounted unit price is rounded to cents before being multiplied by
    the quantity, matching the historical per-line behaviour.  Validation
    follows the original ordering: price and discount are parsed first, then
    the quantity is checked, then the range checks run.
    """
    value = _to_decimal(price)
    rate = _to_decimal(discount)
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
        raise ValueError('invalid quantity')
    if value < 0 or not 0 <= rate <= 100:
        raise ValueError('invalid money')
    return apply_discount(price, discount) * quantity
