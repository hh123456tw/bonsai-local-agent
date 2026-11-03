"""Shared monetary helpers for the catalog.

All money is handled with ``decimal.Decimal`` and rounded to cents using
``ROUND_HALF_UP``.  Discount math is always performed on the full-precision
input and rounded only once (to the unit price), so callers never suffer
from double rounding.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENTS = Decimal("0.01")


def _as_decimal(value):
    """Convert *value* to a finite, full-precision Decimal (no rounding)."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("invalid money")
    if not amount.is_finite():
        raise ValueError("invalid money")
    return amount


def parse_money(value):
    """Parse *value* into a non-negative Decimal rounded to cents.

    Accepts numbers or numeric strings.  Raises ``ValueError`` for negative
    amounts or values that cannot be parsed.
    """
    amount = _as_decimal(value)
    if amount < 0:
        raise ValueError("invalid money")
    return amount.quantize(CENTS, rounding=ROUND_HALF_UP)


def apply_discount(price, percent=0):
    """Return *price* reduced by *percent* percent, rounded to cents.

    The discount is applied to the full-precision price (no intermediate
    rounding) and the result is rounded to cents once.  Raises ``ValueError``
    for negative prices or a percent outside 0..100.
    """
    value = _as_decimal(price)
    rate = Decimal(str(percent))
    if value < 0 or not (Decimal(0) <= rate <= Decimal(100)):
        raise ValueError("invalid money")
    return (value * (Decimal(1) - rate / Decimal(100))).quantize(
        CENTS, rounding=ROUND_HALF_UP
    )


def line_total(price, quantity, discount=0):
    """Total for one line: discounted unit price times quantity.

    The unit price is discounted and rounded to cents first, then multiplied
    by *quantity*.  Raises ``ValueError`` for invalid money, a negative or
    non-integer quantity (bools are rejected), or a discount outside 0..100.
    """
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
        raise ValueError("invalid quantity")
    unit = apply_discount(price, discount)
    return (unit * quantity).quantize(CENTS, rounding=ROUND_HALF_UP)
