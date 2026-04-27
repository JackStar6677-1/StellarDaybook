from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo


def tz_from_config(cfg: dict) -> ZoneInfo:
    name = cfg.get("timezone") or "America/Santiago"
    return ZoneInfo(name)


def now_local(cfg: dict) -> datetime:
    return datetime.now(tz_from_config(cfg))


def parse_hhmm(s: str) -> time:
    h, m = s.strip().split(":")
    return time(int(h), int(m))


def is_friday(d: date) -> bool:
    return d.weekday() == 4


def is_weekend(d: date) -> bool:
    return d.weekday() >= 5
