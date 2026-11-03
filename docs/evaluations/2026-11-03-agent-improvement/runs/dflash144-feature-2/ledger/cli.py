import json
from .parser import parse_csv
from .summary import total, totals_by_currency
def render_report(text, *, by_currency=False, start=None, end=None):
    if not by_currency:
        return json.dumps({'total':format(total(parse_csv(text)),'.2f')},sort_keys=True)
    entries = parse_csv(text)
    grouped = totals_by_currency(entries, start=start, end=end, include_pending=False)
    return json.dumps({'totals':{c:format(v,'.2f') for c,v in sorted(grouped.items())}},sort_keys=True)
