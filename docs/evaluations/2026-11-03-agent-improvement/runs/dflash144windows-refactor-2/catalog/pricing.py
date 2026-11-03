from .money import apply_discount

def discounted(price, percent=0):
    """Discount a price by percent (0..100), rounded to cents.

    Kept as the public API; delegates to the shared money module so all
    monetary math lives in one place.
    """
    return apply_discount(price, percent)
