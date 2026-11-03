import csv,io
from datetime import date
from decimal import Decimal
from .models import Entry

def _normalize_currency(value):
    """Normalize an optional CSV currency value to a 3-letter uppercase code."""
    if value is None:
        return 'USD'
    code = str(value).strip().upper()
    if not (len(code) == 3 and code.isascii() and code.isalpha()):
        raise ValueError(f'invalid currency code: {value!r}')
    return code

def parse_csv(text):
    reader = csv.DictReader(io.StringIO(text))
    entries = []
    for row in reader:
        entries.append(Entry(
            row['account'],
            Decimal(row['amount']),
            date.fromisoformat(row['day']),
            row.get('status') or 'posted',
            _normalize_currency(row.get('currency')),
        ))
    return entries
