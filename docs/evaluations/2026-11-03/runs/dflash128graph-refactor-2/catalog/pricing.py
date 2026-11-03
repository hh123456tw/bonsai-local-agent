from .money import apply_discount


def discounted(price, percent=0):
    """Return price reduced by percent, rounded to cents."""
    return apply_discount(price, percent)
