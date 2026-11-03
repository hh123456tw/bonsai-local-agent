from datetime import date
from decimal import Decimal
def total(entries):
    return sum((e.amount for e in entries),Decimal('0'))
def totals_by_currency(entries, start=None, end=None, include_pending=False):
    if start is not None and end is not None and start > end:
        raise ValueError('start must be on or before end')
    def _in_range(e):
        if start is not None and e.day < start:
            return False
        if end is not None and e.day > end:
            return False
        return True
    result = {}
    for e in entries:
        if not include_pending and e.status != 'posted':
            continue
        if not _in_range(e):
            continue
        result[e.currency] = result.get(e.currency, Decimal('0')) + e.amount
    return result
