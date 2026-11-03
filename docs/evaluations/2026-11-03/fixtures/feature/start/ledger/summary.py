from decimal import Decimal
def total(entries):
    return sum((e.amount for e in entries),Decimal('0'))
