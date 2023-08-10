from datetime import datetime


def next_month(current_time: datetime) -> (datetime, datetime):
    next_month_year = current_time.year
    if current_time.month == 12:
        next_month_year += 1
        next_month_number = 1
    else:
        next_month_number = current_time.month + 1
    return current_time, datetime(next_month_year, next_month_number, current_time.day + 1)


def next_week(current_time: datetime) -> (datetime, datetime):
    pass
