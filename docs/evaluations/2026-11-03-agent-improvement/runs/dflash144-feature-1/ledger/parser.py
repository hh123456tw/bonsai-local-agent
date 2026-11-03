import csv, io, re
from datetime import date
from decimal import Decimal
from .models import Entry

_CURRENCY_RE = re.compile(r'[A-Z]{3}\Z')

def _normalize_currency(value):
    if value is None:
        return 'USD'
    code = value.upper()
    if not _CURRENCY_RE.match(code):
        raise ValueError('Invalid currency code: %r' % value)
    return code

def parse_csv(text):
    rows = []
    for row in csv.DictReader(io.StringIO(text)):
        rows.append(Entry(row['account'], Decimal(row['amount']), date.fromisoformat(row['day']), row.get('status') or 'posted', _normalize_currency(row.get('currency'))))
    return rows