from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

CENTS = Decimal('0.01')


def parse_money(value):
    """Parse a monetary value into a Decimal rounded to cents."""
    try:
        return Decimal(str(value)).quantize(CENTS, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        raise ValueError('invalid money')


def apply_discount(price, percent=0):
    """Return the discounted unit price, rounded to cents (ROUND_HALF_UP).

    The discount is computed from the unrounded input to avoid double rounding.
    """
    try:
        value = Decimal(str(price))
        rate = Decimal(str(percent))
    except (InvalidOperation, ValueError):
        raise ValueError('invalid money')
    if value < 0 or not 0 <= rate <= 100:
        raise ValueError('invalid money')
    return (value * (1 - rate / 100)).quantize(CENTS, rounding=ROUND_HALF_UP)


def line_total(price, quantity, discount=0):
    """Return the discounted unit price times quantity.

    The discount is applied to the unrounded price before the unit price is
    rounded to cents, so no double rounding occurs.
    """
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
        raise ValueError('invalid quantity')
    unit = apply_discount(price, discount)
    return unit * quantity
