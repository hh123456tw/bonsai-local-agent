from __future__ import annotations


def normalize_currency(value):
    """Normalize a currency code to uppercase ASCII.

    ``None`` (an absent/optional CSV column) defaults to ``"USD"``.
    Any other value must be exactly three ASCII letters after stripping
    whitespace and uppercasing; otherwise a :class:`ValueError` is raised.
    """
    if value is None:
        return "USD"
    code = str(value).strip().upper()
    if len(code) != 3 or not all(c.isascii() and c.isalpha() for c in code):
        raise ValueError("invalid currency code: %r" % value)
    return code
