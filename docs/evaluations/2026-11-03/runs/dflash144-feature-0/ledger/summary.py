from datetime import date
from decimal import Decimal
def total(entries):
    return sum((e.amount for e in entries),Decimal('0'))
def _filter_entries(entries, start, end, include_pending):
    if start is not None and end is not None and start > end:
        raise ValueError(f'invalid date range: {start} > {end}')
    result = []
    for e in entries:
        if start is not None and e.day < start:
            continue
        if end is not None and e.day > end:
            continue
        if not include_pending and e.status != 'posted':
            continue
        result.append(e)
    return result
def totals_by_currency(entries, start=None, end=None, include_pending=False):
    out = {}
    for e in _filter_entries(entries, start, end, include_pending):
        out[e.currency] = out.get(e.currency, Decimal('0')) + e.amount
    return out
