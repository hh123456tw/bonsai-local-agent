from decimal import Decimal, ROUND_HALF_UP

CENTS = Decimal('.01')


def _round_cents(value):
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)


def parse_money(value):
    """Parse a monetary value into a Decimal rounded to cents."""
    value = Decimal(str(value))
    if value < 0:
        raise ValueError('invalid money')
    return _round_cents(value)


def apply_discount(price, percent=0):
    """Return price reduced by percent.

    The discount is computed from the unrounded input and the result is
    rounded to cents once (no double rounding).
    """
    value = Decimal(str(price))
    if value < 0:
        raise ValueError('invalid money')
    rate = Decimal(str(percent))
    if not 0 <= rate <= 100:
        raise ValueError('invalid money')
    return _round_cents(value * (Decimal(1) - rate / 100))


def line_total(price, quantity, discount=0):
    """Total for one line: unit price after discount, then times quantity."""
    unit = apply_discount(price, discount)
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
        raise ValueError('invalid quantity')
    return _round_cents(unit * quantity)
