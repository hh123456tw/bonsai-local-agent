import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

_CURRENCY_RE = re.compile(r'^[A-Z]{3}$')


def normalize_currency(value):
    if value is None:
        return 'USD'
    code = str(value).strip().upper()
    if not _CURRENCY_RE.match(code):
        raise ValueError(f'invalid currency code: {value!r}')
    return code
@dataclass(frozen=True)
class Entry:
    account: str
    amount: Decimal
    day: date
    status: str = 'posted'
    currency: str = 'USD'
