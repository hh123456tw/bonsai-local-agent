"""Shared monetary calculations for the catalog.

All money is handled as Decimal with ROUND_HALF_UP rounding to cents.
Discounts are computed from the unrounded input price before the unit
price is rounded to cents, so no double rounding occurs.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENTS = Decimal('0.01')


def _to_decimal(value):
    """Convert a value to an unrounded Decimal, validating it.

    Raises ValueError for booleans, non-numeric values, or negative amounts.
    """
    if isinstance(value, bool):
        raise ValueError('invalid money')
    try:
        value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError('invalid money')
    if value < 0:
        raise ValueError('invalid money')
    return value


def parse_money(value):
    """Parse a money value into a Decimal rounded to cents.

    Accepts numbers and strings (e.g. '1.005', 2.5). Booleans and non-numeric
    values raise ValueError.
    """
    return _to_decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)


def apply_discount(price, percent=0):
    """Return the discounted unit price, rounded to cents.

    The discount is applied to the unrounded input price before the unit
    price is quantized to cents, so there is no double rounding.
    """
    price = _to_decimal(price)
    try:
        rate = Decimal(str(percent))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError('invalid money')
    if not 0 <= rate <= 100:
        raise ValueError('invalid money')
    return (price * (Decimal('1') - rate / Decimal('100'))).quantize(
        CENTS, rounding=ROUND_HALF_UP
    )


def line_total(price, quantity, discount=0):
    """Total for one line item: discounted unit price times quantity.

    The unit price is discounted and rounded to cents first (via
    apply_discount), then multiplied by the integer quantity.
    """
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
        raise ValueError('invalid quantity')
    return apply_discount(price, discount) * quantity
