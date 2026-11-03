from dataclasses import dataclass
from datetime import date
from decimal import Decimal


def normalize_currency(code):
    if code is None or code == '':
        return 'USD'
    code = str(code).upper()
    if len(code) != 3 or not all('A' <= c <= 'Z' for c in code):
        raise ValueError('invalid currency code: %r' % code)
    return code


@dataclass(frozen=True)
class Entry:
    account: str
    amount: Decimal
    day: date
    status: str = 'posted'
    currency: str = 'USD'
