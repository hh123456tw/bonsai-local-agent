"""Shared monetary helpers for the catalog package.

All money is handled as :class:`decimal.Decimal` built from ``str(value)``
and rounded to cents with ``ROUND_HALF_UP``.  Discount math is performed on
the unrounded input so that no intermediate rounding is applied twice.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

_CENTS = Decimal("0.01")


def _to_decimal(value):
    """Convert a scalar to Decimal via ``str(value)``.

    Rejects booleans and anything that cannot be parsed as a finite decimal.
    """
    if isinstance(value, bool):
        raise ValueError("invalid money")
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("invalid money")


def _validate_price(value):
    """Return a non-negative Decimal for ``value``."""
    value = _to_decimal(value)
    if value < 0:
        raise ValueError("invalid money")
    return value


def _validate_percent(percent):
    """Return a Decimal in the inclusive range [0, 100]."""
    percent = _to_decimal(percent)
    if not 0 <= percent <= 100:
        raise ValueError("invalid money")
    return percent


def _validate_quantity(quantity):
    """Return an integer quantity >= 0 (bool rejected)."""
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise ValueError("invalid quantity")
    if quantity < 0:
        raise ValueError("invalid quantity")
    return quantity


def parse_money(value):
    """Parse ``value`` into a money Decimal rounded to cents.

    >>> parse_money('1.005')
    Decimal('1.01')
    """
    return _validate_price(value).quantize(_CENTS, rounding=ROUND_HALF_UP)


def apply_discount(price, percent=0):
    """Discount ``price`` by ``percent`` and round the unit price to cents.

    The discount is computed from the unrounded input, then the resulting
    unit price is rounded to cents (no double rounding).
    """
    value = _validate_price(price)
    rate = _validate_percent(percent)
    return (value * (Decimal(1) - rate / 100)).quantize(
        _CENTS, rounding=ROUND_HALF_UP
    )


def line_total(price, quantity, discount=0):
    """Total for one line: discounted unit price (cents) times quantity.

    The discounted unit price is rounded to cents before being multiplied by
    the quantity.
    """
    quantity = _validate_quantity(quantity)
    unit = apply_discount(price, discount)
    return unit * quantity
