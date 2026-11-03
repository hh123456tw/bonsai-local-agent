import json
from datetime import date
from .parser import parse_csv
from .summary import total, totals_by_currency

def _parse_date(value):
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)

def render_report(text, *, by_currency=False, start=None, end=None):
    entries = parse_csv(text)
    if by_currency:
        totals = totals_by_currency(entries, _parse_date(start), _parse_date(end))
        return json.dumps({'totals': {c: format(t, '.2f') for c, t in sorted(totals.items())}}, sort_keys=True)
    return json.dumps({'total':format(total(parse_csv(text)),'.2f')},sort_keys=True)
