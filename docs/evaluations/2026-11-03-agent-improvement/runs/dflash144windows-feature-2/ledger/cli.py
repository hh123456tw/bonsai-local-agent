import json
from datetime import date, datetime
from .parser import parse_csv
from .summary import total, totals_by_currency

def _as_date(value):
    """Accept datetime.date (or ISO string) values for date bounds."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise TypeError(f'expected datetime.date or ISO string, got {type(value).__name__}')

def render_report(text, *, by_currency=False, start=None, end=None):
    if by_currency:
        entries = parse_csv(text)
        totals = totals_by_currency(entries, _as_date(start), _as_date(end))
        return json.dumps({'totals': {c: format(t, '.2f') for c, t in sorted(totals.items())}}, sort_keys=True)
    return json.dumps({'total':format(total(parse_csv(text)),'.2f')},sort_keys=True)
