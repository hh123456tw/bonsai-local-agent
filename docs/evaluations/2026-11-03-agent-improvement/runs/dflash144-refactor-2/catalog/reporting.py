from .orders import invoice_total
def format_total(lines):
    return "$"+format(invoice_total(lines),".2f")
