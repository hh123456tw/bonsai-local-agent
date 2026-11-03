import csv,io,re
from datetime import date
from decimal import Decimal
from .models import Entry
_CURRENCY_RE = re.compile(r'^[A-Za-z]{3}$')
def _normalize_currency(raw):
    if raw is None:
        return 'USD'
    code = str(raw).strip()
    if not code:
        return 'USD'
    if not _CURRENCY_RE.match(code):
        raise ValueError(f'invalid currency code: {code!r}')
    return code.upper()
def parse_csv(text):
    return [Entry(row['account'],Decimal(row['amount']),date.fromisoformat(row['day']),row.get('status') or 'posted',_normalize_currency(row.get('currency'))) for row in csv.DictReader(io.StringIO(text))]
