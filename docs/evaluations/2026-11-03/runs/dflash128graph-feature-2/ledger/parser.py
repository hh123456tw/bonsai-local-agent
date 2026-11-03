import csv,io
from datetime import date
from decimal import Decimal
from .models import Entry, normalize_currency
def parse_csv(text):
    entries = []
    for row in csv.DictReader(io.StringIO(text)):
        currency = row.get('currency')
        if currency is None or currency == '':
            currency = 'USD'
        else:
            currency = normalize_currency(currency)
        entries.append(Entry(row['account'],Decimal(row['amount']),date.fromisoformat(row['day']),row.get('status') or 'posted',currency))
    return entries
