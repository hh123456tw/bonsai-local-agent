import csv, io
from datetime import date
from decimal import Decimal
from .models import Entry


def _normalize_currency(currency):
    if currency is None:
        return 'USD'
    code = str(currency).strip().upper()
    if len(code) != 3 or not all('A' <= c <= 'Z' for c in code):
        raise ValueError('currency must be exactly three uppercase ASCII letters: %r' % (currency,))
    return code


def parse_csv(text):
    entries = []
    for row in csv.DictReader(io.StringIO(text)):
        account = row.get('account')
        amount_raw = row.get('amount')
        day_raw = row.get('day')
        if account is None or amount_raw is None or day_raw is None:
            raise ValueError('missing required CSV field: account, amount, day')
        entry = Entry(
            account=account,
            amount=Decimal(amount_raw),
            day=date.fromisoformat(day_raw),
            status=(row.get('status') or 'posted'),
            currency=_normalize_currency(row.get('currency')),
        )
        entries.append(entry)
    return entries
