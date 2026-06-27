from __future__ import annotations

import calendar
from datetime import datetime, time


def _parse_date(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.strptime(value, "%Y-%m-%d")


def _month_bounds(work_month: str) -> tuple[datetime, datetime]:
    year, month = [int(part) for part in work_month.split("-")]
    last_day = calendar.monthrange(year, month)[1]
    start = datetime(year, month, 1, 0, 0, 0)
    end = datetime.combine(datetime(year, month, last_day).date(), time.max)
    return start, end


def resolve_date_range(
    start_date: str | None = None,
    end_date: str | None = None,
    work_month: str | None = None,
) -> tuple[datetime, datetime, str]:
    if start_date is not None or end_date is not None:
        today = datetime.today()
        start = _parse_date(start_date) or datetime(today.year, today.month, 1)
        end_base = _parse_date(end_date) or today
        end = datetime.combine(end_base.date(), time.max)
        return start, end, f"{start.date().isoformat()} ~ {end.date().isoformat()}"

    if work_month is not None:
        start, end = _month_bounds(work_month)
        return start, end, work_month

    today = datetime.today()
    start = datetime(today.year, today.month, 1, 0, 0, 0)
    end = datetime.combine(today.date(), time.max)
    return start, end, f"{today.year:04d}-{today.month:02d}"
