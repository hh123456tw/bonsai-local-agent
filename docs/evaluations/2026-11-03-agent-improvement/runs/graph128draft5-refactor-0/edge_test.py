from decimal import Decimal, InvalidOperation
from catalog.money import parse_money, apply_discount, line_total
from catalog.pricing import discounted
from catalog.orders import invoice_total
from catalog.inventory import stock_value
from catalog import checkout

def chk(cond, msg):
    if not cond:
        raise AssertionError(msg)

chk(parse_money('1.005') == Decimal('1.01'), 'parse 1.005')
chk(parse_money('1.004') == Decimal('1.00'), 'parse 1.004')
chk(parse_money(2.999) == Decimal('3.00'), 'parse 2.999')
chk(parse_money('0') == Decimal('0.00'), 'parse 0')
chk(parse_money('10') == Decimal('10.00'), 'parse 10')
try:
    parse_money('-1.00'); raise AssertionError('parse neg should raise')
except ValueError: pass
try:
    parse_money('abc'); raise AssertionError('parse abc should raise InvalidOperation')
except InvalidOperation: pass

chk(apply_discount('1.005', 0) == Decimal('1.01'), 'ad 1.005 0')
chk(apply_discount('1.005', 50) == Decimal('0.50'), 'ad 1.005 50')
chk(apply_discount('1.005', 100) == Decimal('0.00'), 'ad 1.005 100')
chk(apply_discount('1.005', 33) == Decimal('0.67'), 'ad 1.005 33')
chk(apply_discount('1.005', 33.333) == Decimal('0.67'), 'ad 1.005 33.333')
chk(apply_discount('10.00', 10) == Decimal('9.00'), 'ad 10.00 10')
chk(apply_discount('10.00', 0) == Decimal('10.00'), 'ad 10.00 0')
chk(apply_discount('1.005') == Decimal('1.01'), 'ad default')
try:
    apply_discount('1.00', 101); raise AssertionError('ad 101 should raise')
except ValueError: pass
try:
    apply_discount('1.00', -1); raise AssertionError('ad neg should raise')
except ValueError: pass
try:
    apply_discount('-1.00', 0); raise AssertionError('ad neg price should raise')
except ValueError: pass

chk(line_total('1.005', 3) == Decimal('3.03'), 'lt 1.005 3')
chk(line_total('1.005', 3, 50) == Decimal('1.50'), 'lt 1.005 3 50')
chk(line_total('1.005', 0) == Decimal('0.00'), 'lt 1.005 0')
chk(line_total('1.005', 1) == Decimal('1.01'), 'lt 1.005 1')
for bad_q in [True, False, -1, 2.0, '2']:
    try:
        line_total('1.00', bad_q); raise AssertionError('lt bad qty %r should raise' % bad_q)
    except ValueError: pass
try:
    line_total('-1.00', 1); raise AssertionError('lt neg price should raise')
except ValueError: pass

chk(discounted('1.005') == Decimal('1.01'), 'discounted compat')
chk(discounted('1.005', 50) == Decimal('0.50'), 'discounted compat 50')

chk(invoice_total([{'price':'1.005','qty':3}]) == Decimal('3.03'), 'inv basic')
chk(invoice_total([{'price':'1.005','qty':3,'discount':50}]) == Decimal('1.50'), 'inv disc')
chk(invoice_total([]) == Decimal('0.00'), 'inv empty')
chk(invoice_total([{'price':'1.00','qty':2},{'price':'2.00','qty':3}]) == Decimal('8.00'), 'inv multi')
for bad in [{'price':'1.00','qty':-1},{'price':'1.00','qty':True},{'price':'-1.00','qty':1}]:
    try:
        invoice_total([bad]); raise AssertionError('inv bad %s should raise' % bad)
    except ValueError: pass

chk(stock_value([{'price':'2.005','qty':2}]) == Decimal('4.02'), 'stock basic')
chk(stock_value([{'price':'1.00','qty':3}]) == Decimal('3.00'), 'stock basic2')
chk(stock_value([]) == Decimal('0.00'), 'stock empty')
for bad in [{'price':'1.00','qty':-1},{'price':'1.00','qty':True},{'price':'-1.00','qty':1}]:
    try:
        stock_value([bad]); raise AssertionError('stock bad %s should raise' % bad)
    except ValueError: pass

chk(checkout([{'price':'10','qty':2}],2) == {'subtotal':'20.00','shipping':'7.50','total':'27.50'}, 'checkout basic')
chk(checkout([{'price':'1.00','qty':1}],0) == {'subtotal':'1.00','shipping':'5.00','total':'6.00'}, 'checkout zero wt')
chk(checkout([{'price':'1.00','qty':1}],0,express=True) == {'subtotal':'1.00','shipping':'10.00','total':'11.00'}, 'checkout express')

print('ALL CHECKS PASSED')
