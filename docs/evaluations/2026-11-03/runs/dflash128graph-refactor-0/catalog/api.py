from .orders import invoice_total
from .shipping import quote
def checkout(lines,weight,express=False):
    subtotal=invoice_total(lines);delivery=quote(weight,express)
    return {"subtotal":format(subtotal,".2f"),"shipping":format(delivery,".2f"),"total":format(subtotal+delivery,".2f")}
