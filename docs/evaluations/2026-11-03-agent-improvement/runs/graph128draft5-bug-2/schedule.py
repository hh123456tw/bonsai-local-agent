from datetime import timedelta
def business_days(start, end, holidays=()):
    if start > end:
        raise ValueError('reversed range')
    blocked = set(holidays)
    result = 0
    while start <= end:
        if start.weekday() < 5 and start not in blocked:
            result += 1
        start += timedelta(days=1)
    return result
