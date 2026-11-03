from dataclasses import dataclass
from datetime import date
from decimal import Decimal
@dataclass(frozen=True)
class Entry:
    account: str
    amount: Decimal
    day: date
    status: str = 'posted'
    currency: str = 'USD'
