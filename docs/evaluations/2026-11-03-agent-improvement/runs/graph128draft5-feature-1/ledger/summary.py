from __future__ import annotations

from datetime import date
from decimal import Decimal


def total(entries):
    return sum((e.amount for e in entries), Decimal('0'))


def _filter(entries, start, end, include_pending):
    out = []
    for e in entries:
        if not include_pending and e.status != 'posted':
            continue
        if start is not None and e.day < start:
            continue
        if end is not None and e.day > end:
            continue
        out.append(e)
    return out


def totals_by_currency(entries, start=None, end=None, include_pending=False):
    """Sum ``Entry.amount`` per currency.

    By default only ``posted`` entries are included. When ``include_pending``
    is True, every status is counted. Optional inclusive ``start``/``end``
    bounds (both :class:`datetime.date`) filter by entry date; a reversed
    bound pair (``start`` after ``end``) raises :class:`ValueError`.
    Returns a dict mapping currency code to its :class:`decimal.Decimal` total.
    """
    if start is not None and end is not None and start > end:
        raise ValueError("start must not be after end")
    result = {}
    for e in _filter(entries, start, end, include_pending):
        result[e.currency] = result.get(e.currency, Decimal('0')) + e.amount
    return result
