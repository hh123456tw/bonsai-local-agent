import json
from .parser import parse_csv
from .summary import total, totals_by_currency
def render_report(text, *, by_currency=False, start=None, end=None):
    entries = parse_csv(text)
    if by_currency:
        return json.dumps({'totals': {c: format(a, '.2f') for c, a in sorted(totals_by_currency(entries, start, end).items())}}, sort_keys=True)
    return json.dumps({'total':format(total(parse_csv(text)),'.2f')},sort_keys=True)
