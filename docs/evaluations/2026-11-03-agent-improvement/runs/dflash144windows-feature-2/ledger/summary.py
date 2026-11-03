from datetime import date
from decimal import Decimal

def total(entries):
    return sum((e.amount for e in entries),Decimal('0'))

def totals_by_currency(entries, start=None, end=None, include_pending=False):
    """Sum Decimal amounts by currency.

    Only posted entries are included by default; include_pending=True also
    includes entries with any other status. Optional inclusive date bounds
    (start/end) filter entries by day. Reversed bounds raise ValueError.
    Returns a dict mapping currency code to its Decimal total.
    """
    if start is not None and end is not None and start > end:
        raise ValueError('start must be on or before end')
    totals = {}
    for entry in entries:
        if not include_pending and entry.status != 'posted':
            continue
        if start is not None and entry.day < start:
            continue
        if end is not None and entry.day > end:
            continue
        totals[entry.currency] = totals.get(entry.currency, Decimal('0')) + entry.amount
    return totals
