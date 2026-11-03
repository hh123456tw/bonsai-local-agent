import json
from datetime import date
from .parser import parse_csv
from .summary import total, totals_by_currency
def render_report(text, *, by_currency=False, start=None, end=None):
    if by_currency:
        entries = parse_csv(text)
        totals = totals_by_currency(entries, start=start, end=end)
        return json.dumps({'totals': {currency: format(amount, '.2f') for currency, amount in sorted(totals.items())}}, sort_keys=True)
    return json.dumps({'total':format(total(parse_csv(text)),'.2f')},sort_keys=True)
