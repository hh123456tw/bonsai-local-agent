"""Pricing helpers built on the shared money module."""

from .money import apply_discount


def discounted(price, percent=0):
    """Return price after applying a percentage discount, rounded to cents."""
    return apply_discount(price, percent)
