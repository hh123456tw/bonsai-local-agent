from decimal import Decimal, ROUND_HALF_UP

_CENTS = Decimal("0.01")


def parse_money(value):
    amount = Decimal(str(value))
    if amount < 0:
        raise ValueError("invalid money")
    return amount.quantize(_CENTS, rounding=ROUND_HALF_UP)


def apply_discount(price, percent=0):
    value = Decimal(str(price))
    rate = Decimal(str(percent))
    if value < 0 or not (0 <= rate <= 100):
        raise ValueError("invalid money")
    return (value * (1 - rate / 100)).quantize(_CENTS, rounding=ROUND_HALF_UP)


def line_total(price, quantity, discount=0):
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
        raise ValueError("invalid quantity")
    unit = apply_discount(price, discount)
    return (unit * quantity).quantize(_CENTS, rounding=ROUND_HALF_UP)
