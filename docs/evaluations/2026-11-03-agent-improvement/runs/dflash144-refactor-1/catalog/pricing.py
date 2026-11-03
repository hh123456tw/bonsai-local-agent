from .money import apply_discount


def discounted(price, percent=0):
    """Return the discounted unit price, rounded to cents (ROUND_HALF_UP)."""
    return apply_discount(price, percent)
