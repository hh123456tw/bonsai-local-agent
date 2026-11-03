from decimal import Decimal,ROUND_HALF_UP
def discounted(price,percent=0):
    value=Decimal(str(price)); rate=Decimal(str(percent))
    if value<0 or not 0<=rate<=100: raise ValueError('invalid money')
    return (value*(1-rate/100)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
