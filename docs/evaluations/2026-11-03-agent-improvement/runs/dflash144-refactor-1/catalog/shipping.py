from decimal import Decimal,ROUND_HALF_UP
def quote(weight,express=False):
    weight=Decimal(str(weight))
    if weight<0:raise ValueError('invalid weight')
    return ((Decimal('5')+weight*Decimal('1.25'))*(2 if express else 1)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
