from datetime import date
from decimal import Decimal

def total(entries):
    return sum((e.amount for e in entries),Decimal('0'))

def totals_by_currency(entries, start=None, end=None, include_pending=False):
    if start is not None and end is not None and start > end:
        raise ValueError(f'invalid date range: {start} > {end}')
    out = {}
    for e in entries:
        if not include_pending and e.status != 'posted':
            continue
        if start is not None and e.day < start:
            continue
        if end is not None and e.day > end:
            continue
        out[e.currency] = out.get(e.currency, Decimal('0')) + e.amount
    return out
