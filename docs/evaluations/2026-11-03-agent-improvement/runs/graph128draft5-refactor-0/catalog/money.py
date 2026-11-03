from decimal import Decimal, ROUND_HALF_UP

CENTS = Decimal('.01')


def parse_money(value):
    """Parse a monetary value into a Decimal rounded to cents."""
    value = Decimal(str(value))
    if value < 0:
        raise ValueError('invalid money')
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)


def apply_discount(price, percent=0):
    """Return price discounted by percent (0..100), rounded to cents.

    The discount is applied to the unrounded input, then the result is
    rounded once to cents.
    """
    raw = Decimal(str(price))
    if raw < 0:
        raise ValueError('invalid money')
    rate = Decimal(str(percent))
    if not 0 <= rate <= 100:
        raise ValueError('invalid money')
    return (raw * (Decimal(1) - rate / Decimal(100))).quantize(CENTS, rounding=ROUND_HALF_UP)


def line_total(price, quantity, discount=0):
    """Return total for quantity units of price with discount, rounded to cents."""
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
        raise ValueError('invalid quantity')
    unit = apply_discount(price, percent=discount)
    return (unit * quantity).quantize(CENTS, rounding=ROUND_HALF_UP)
