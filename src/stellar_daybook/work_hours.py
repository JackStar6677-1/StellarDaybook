from __future__ import annotations

from datetime import datetime, time

from stellar_daybook.timeutil import is_friday, is_weekend, parse_hhmm, tz_from_config


def work_label_at(dt: datetime, cfg: dict) -> str:
    """Etiqueta legible de jornada para el instante dado."""
    if is_weekend(dt.date()):
        return "Fin de semana (fuera de jornada habitual)"
    work = cfg.get("work") or {}
    mt = work.get("monday_thursday") or {}
    fri = work.get("friday") or {}
    if is_friday(dt.date()):
        start = parse_hhmm(str(fri.get("start", "07:55")))
        end = parse_hhmm(str(fri.get("end", "16:35")))
    else:
        start = parse_hhmm(str(mt.get("start", "07:55")))
        end = parse_hhmm(str(mt.get("end", "17:30")))
    tz = tz_from_config(cfg)
    clock = dt.astimezone(tz).time()
    if time(start.hour, start.minute) <= clock <= time(end.hour, end.minute):
        return "En jornada laboral"
    return "En casa / fuera de jornada"
