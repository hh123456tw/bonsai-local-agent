"""Shared monetary helpers for the catalog.

All money is handled as :class:`decimal.Decimal` and rounded to the nearest
cent using ``ROUND_HALF_UP``.  The single point of conversion is
``parse_money``, which always builds the Decimal from ``str(value)`` so that
floats and numeric strings behave identically.
"""

from decimal import Decimal, ROUND_HALF_UP

_CENTS = Decimal("0.01")


def _to_decimal(value):
    """Coerce ``value`` to a Decimal via ``str`` without any rounding."""
    return Decimal(str(value))


def parse_money(value):
    """Parse ``value`` into a Decimal money amount rounded to cents.

    The value is coerced via ``Decimal(str(value))`` and then rounded to two
    decimal places with ``ROUND_HALF_UP``.  Negative amounts are rejected with
    ``ValueError``.
    """
    value = _to_decimal(value)
    if value < 0:
        raise ValueError("invalid money")
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP)


def apply_discount(price, percent=0):
    """Return the discounted unit price, rounded to cents.

    The discount is applied to the *unrounded* price and only the resulting
    unit price is rounded, so no double rounding occurs.  ``percent`` must be
    in the range 0..100.
    """
    price = _to_decimal(price)
    if price < 0:
        raise ValueError("invalid money")
    rate = _to_decimal(percent)
    if not 0 <= rate <= 100:
        raise ValueError("invalid money")
    return (price * (1 - rate / 100)).quantize(_CENTS, rounding=ROUND_HALF_UP)


def line_total(price, quantity, discount=0):
    """Return the total for a line item.

    The discounted unit price is rounded to cents first, then multiplied by
    the (non-negative integer) quantity.  This mirrors the original
    ``orders.invoice_total`` per-line behaviour.
    """
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
        raise ValueError("invalid quantity")
    unit = apply_discount(price, discount)
    return unit * quantity
