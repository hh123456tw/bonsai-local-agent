import json
from .parser import parse_csv
from .summary import total
def render_report(text):
    return json.dumps({'total':format(total(parse_csv(text)),'.2f')},sort_keys=True)
