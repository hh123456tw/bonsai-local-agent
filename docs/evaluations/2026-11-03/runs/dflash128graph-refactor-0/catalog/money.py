from decimal import Decimal, ROUND_HALF_UP

CENTS = Decimal('0.01')


def parse_money(value):
    """Parse a monetary value into a Decimal.

    Accepts numbers and strings; booleans are rejected.
    """
    if isinstance(value, bool):
        raise ValueError('invalid money')
    return Decimal(str(value))


def apply_discount(price, percent=0):
    """Return price reduced by percent (0..100), rounded to cents."""
    value = parse_money(price)
    rate = Decimal(str(percent))
    if value < 0 or not 0 <= rate <= 100:
        raise ValueError('invalid money')
    return (value * (1 - rate / 100)).quantize(CENTS, rounding=ROUND_HALF_UP)


def line_total(price, quantity, discount=0):
    """Total for one line: discounted unit price (rounded to cents) times qty."""
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
        raise ValueError('invalid quantity')
    return apply_discount(price, discount) * quantity
