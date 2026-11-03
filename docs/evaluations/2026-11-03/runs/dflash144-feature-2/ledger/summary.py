from decimal import Decimal
from datetime import date
from .models import Entry

def total(entries):
    return sum((e.amount for e in entries),Decimal('0'))

def totals_by_currency(entries, start=None, end=None, include_pending=False):
    if start is not None and end is not None and start > end:
        raise ValueError('start must be on or before end')
    out = {}
    for e in entries:
        if e.status != 'posted' and not include_pending:
            continue
        if start is not None and e.day < start:
            continue
        if end is not None and e.day > end:
            continue
        out[e.currency] = out.get(e.currency, Decimal('0')) + e.amount
    return out
