import json
from datetime import date
from .parser import parse_csv
from .summary import total, totals_by_currency

def _as_date(value):
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))

def render_report(text, *, by_currency=False, start=None, end=None):
    if by_currency:
        entries = parse_csv(text)
        totals = totals_by_currency(entries, start=_as_date(start), end=_as_date(end))
        return json.dumps({'totals': {c: format(v, '.2f') for c, v in sorted(totals.items())}}, sort_keys=True)
    return json.dumps({'total':format(total(parse_csv(text)),'.2f')},sort_keys=True)
