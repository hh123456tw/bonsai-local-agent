from datetime import date
from decimal import Decimal
def total(entries):
    return sum((e.amount for e in entries),Decimal('0'))
def _validate_bounds(start, end):
    if start is not None and end is not None and start > end:
        raise ValueError(f'invalid date range: {start} after {end}')
def _filter(entries, start, end):
    out = []
    for e in entries:
        if start is not None and e.day < start:
            continue
        if end is not None and e.day > end:
            continue
        out.append(e)
    return out
def totals_by_currency(entries, start=None, end=None, include_pending=False):
    _validate_bounds(start, end)
    selected = [e for e in _filter(entries, start, end) if include_pending or e.status == 'posted']
    by_currency = {}
    for e in selected:
        by_currency[e.currency] = by_currency.get(e.currency, Decimal('0')) + e.amount
    return by_currency
