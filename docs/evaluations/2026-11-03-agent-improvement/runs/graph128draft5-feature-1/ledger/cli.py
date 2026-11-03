import json

from .parser import parse_csv
from .summary import total, totals_by_currency


def render_report(text, *, by_currency=False, start=None, end=None):
    if by_currency:
        totals = totals_by_currency(
            parse_csv(text), start=start, end=end, include_pending=False
        )
        return json.dumps(
            {"totals": {code: format(amount, ".2f") for code, amount in totals.items()}},
            sort_keys=True,
        )
    return json.dumps({"total": format(total(parse_csv(text)), ".2f")}, sort_keys=True)
