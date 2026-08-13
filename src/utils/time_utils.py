from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta


def calculate_new_unix_expiry_time_month(first_unix_time: int, month_ahead: int) -> int:
    if first_unix_time > 9999999999:
        first_unix_time = first_unix_time // 1000

    first_dt_time = datetime.fromtimestamp(first_unix_time, tz=timezone.utc)
    next_month_dt = first_dt_time + relativedelta(months=month_ahead)

    return int(next_month_dt.timestamp())


def calculate_new_unix_expiry_time_days(first_unix_time: int, days_ahead: int) -> int:
    if first_unix_time > 9999999999:
        first_unix_time = first_unix_time // 1000

    first_dt_time = datetime.fromtimestamp(first_unix_time, tz=timezone.utc)
    next_month_dt = first_dt_time + relativedelta(days=days_ahead)

    return int(next_month_dt.timestamp())

