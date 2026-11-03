from decimal import Decimal
def total(entries):
    return sum((e.amount for e in entries),Decimal('0'))
def totals_by_currency(entries, start=None, end=None, include_pending=False):
    if start is not None and end is not None and start > end:
        raise ValueError('start must not be after end')
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
