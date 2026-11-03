import csv,io
from datetime import date
from decimal import Decimal
from .models import Entry
def parse_csv(text):
    return [Entry(row['account'],Decimal(row['amount']),date.fromisoformat(row['day']),row.get('status') or 'posted') for row in csv.DictReader(io.StringIO(text))]
