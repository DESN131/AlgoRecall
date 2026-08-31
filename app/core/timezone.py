from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def local_today() -> date:
    return datetime.now(ZoneInfo(get_settings().app_timezone)).date()

