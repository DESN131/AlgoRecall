from datetime import date, datetime

from app.core.config import get_settings
from app.core.timezone import (
    format_local_datetime,
    local_date_midday_to_utc_naive,
    local_date_start_to_utc_naive,
    utc_naive_to_local,
    utc_naive_to_local_date,
)


def test_utc_datetime_is_converted_to_configured_timezone(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_timezone", "Asia/Shanghai")
    utc_value = datetime(2026, 9, 10, 16, 30)
    local_value = utc_naive_to_local(utc_value)

    assert local_value.isoformat() == "2026-09-11T00:30:00+08:00"
    assert utc_naive_to_local_date(utc_value) == date(2026, 9, 11)
    assert format_local_datetime(utc_value) == "2026-09-11 00:30"


def test_local_midnight_is_converted_to_utc_for_history_filtering(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_timezone", "Asia/Shanghai")
    assert local_date_start_to_utc_naive(date(2026, 9, 10)) == datetime(2026, 9, 9, 16, 0)
    assert local_date_midday_to_utc_naive(date(2026, 9, 10)) == datetime(2026, 9, 10, 4, 0)
