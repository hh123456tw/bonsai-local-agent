from .money import apply_discount


def discounted(price, percent=0):
    """Public API: discount *price* by *percent* percent, rounded to cents."""
    return apply_discount(price, percent)
