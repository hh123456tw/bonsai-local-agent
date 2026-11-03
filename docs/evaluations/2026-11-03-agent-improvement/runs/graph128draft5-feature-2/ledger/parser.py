import csv,io,re
from datetime import date
from decimal import Decimal
from .models import Entry

_CURRENCY_RE = re.compile(r'^[A-Z]{3}$')

def _normalize_currency(value):
    if value is None:
        return 'USD'
    code = str(value).strip().upper()
    if not _CURRENCY_RE.match(code):
        raise ValueError(f'invalid currency code: {value!r}')
    return code

def parse_csv(text):
    return [Entry(row['account'],Decimal(row['amount']),date.fromisoformat(row['day']),row.get('status') or 'posted',_normalize_currency(row.get('currency'))) for row in csv.DictReader(io.StringIO(text))]
