from decimal import Decimal, ROUND_HALF_UP

_CENTS = Decimal('0.01')


def parse_money(value):
    """Parse a monetary value to a Decimal rounded to cents."""
    parsed = Decimal(str(value))
    if parsed < 0:
        raise ValueError('invalid money')
    return parsed.quantize(_CENTS, rounding=ROUND_HALF_UP)


def apply_discount(price, percent=0):
    """Return the discounted unit price, rounded to cents.

    The discount is applied to the unrounded input before the unit
    price is rounded, so no double rounding occurs.
    """
    value = Decimal(str(price))
    rate = Decimal(str(percent))
    if value < 0 or not 0 <= rate <= 100:
        raise ValueError('invalid money')
    return (value * (Decimal(1) - rate / Decimal(100))).quantize(
        _CENTS, rounding=ROUND_HALF_UP
    )


def line_total(price, quantity, discount=0):
    """Return the total for a line item: discounted unit price times quantity."""
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
        raise ValueError('invalid quantity')
    unit = apply_discount(price, discount)
    return (unit * quantity).quantize(_CENTS, rounding=ROUND_HALF_UP)
