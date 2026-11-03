from datetime import date
from decimal import Decimal


def total(entries):
    return sum((e.amount for e in entries), Decimal('0'))


def _filter_entries(entries, start, end):
    if start is not None and end is not None and start > end:
        raise ValueError('start must be on or before end')
    result = []
    for entry in entries:
        if start is not None and entry.day < start:
            continue
        if end is not None and entry.day > end:
            continue
        result.append(entry)
    return result


def totals_by_currency(entries, start=None, end=None, include_pending=False):
    if include_pending:
        selected = list(entries)
    else:
        selected = [e for e in entries if e.status == 'posted']
    selected = _filter_entries(selected, start, end)
    totals = {}
    for entry in selected:
        totals[entry.currency] = (totals.get(entry.currency, Decimal('0')) + entry.amount)
    return totals
