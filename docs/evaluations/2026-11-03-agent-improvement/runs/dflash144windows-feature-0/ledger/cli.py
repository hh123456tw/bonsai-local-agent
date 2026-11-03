import json
from .parser import parse_csv
from .summary import total,totals_by_currency
def render_report(text,*,by_currency=False,start=None,end=None):
    if by_currency:
        totals=totals_by_currency(parse_csv(text),start=start,end=end)
        return json.dumps({'totals':{c:format(v,'.2f') for c,v in sorted(totals.items())}},sort_keys=True)
    return json.dumps({'total':format(total(parse_csv(text)),'.2f')},sort_keys=True)
