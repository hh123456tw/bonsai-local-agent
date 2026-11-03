import json
from .parser import parse_csv
from .summary import total, totals_by_currency
def render_report(text, *, by_currency=False, start=None, end=None):
    if by_currency:
        data = totals_by_currency(parse_csv(text), start=start, end=end, include_pending=True)
        return json.dumps({'totals': {c: format(a, '.2f') for c, a in sorted(data.items())}}, sort_keys=True)
    return json.dumps({'total':format(total(parse_csv(text)),'.2f')},sort_keys=True)
