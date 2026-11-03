import csv,io
from datetime import date
from decimal import Decimal
from .models import Entry, normalize_currency
def parse_csv(text):
    return [Entry(row['account'],Decimal(row['amount']),date.fromisoformat(row['day']),row.get('status') or 'posted',normalize_currency(row.get('currency'))) for row in csv.DictReader(io.StringIO(text))]
