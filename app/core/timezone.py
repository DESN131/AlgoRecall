from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def local_today() -> date:
    return datetime.now(ZoneInfo(get_settings().app_timezone)).date()


def utc_naive_to_local(value: datetime) -> datetime:
    """Convert a UTC-naive database datetime to the configured local timezone."""
    utc_value = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return utc_value.astimezone(ZoneInfo(get_settings().app_timezone))


def utc_naive_to_local_date(value: datetime) -> date:
    """Convert a UTC-naive database datetime to its application-local date."""
    return utc_naive_to_local(value).date()


def local_date_start_to_utc_naive(value: date) -> datetime:
    """Return local midnight converted to the UTC-naive database convention."""
    local_value = datetime.combine(value, time.min, tzinfo=ZoneInfo(get_settings().app_timezone))
    return local_value.astimezone(UTC).replace(tzinfo=None)


def local_date_midday_to_utc_naive(value: date) -> datetime:
    """Represent a date-only historical event as local noon in UTC storage."""
    local_value = datetime.combine(value, time(hour=12), tzinfo=ZoneInfo(get_settings().app_timezone))
    return local_value.astimezone(UTC).replace(tzinfo=None)


def format_local_datetime(value: datetime | None, pattern: str = "%Y-%m-%d %H:%M") -> str:
    return utc_naive_to_local(value).strftime(pattern) if value else "—"
