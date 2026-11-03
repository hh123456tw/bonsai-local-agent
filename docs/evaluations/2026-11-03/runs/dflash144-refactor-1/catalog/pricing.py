from .money import apply_discount


def discounted(price, percent=0):
    return apply_discount(price, percent)
