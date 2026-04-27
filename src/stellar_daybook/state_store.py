from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Any

from stellar_daybook.paths import repo_root

logger = logging.getLogger(__name__)


@dataclass
class DayState:
    day: str  # YYYY-MM-DD
    exe_seconds: dict[str, int] = field(default_factory=dict)
    push_snapshots: list[dict[str, Any]] = field(default_factory=list)
    slots_fired: list[str] = field(default_factory=list)
    active_tracking_seconds: int = 0

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, d: dict[str, Any]) -> DayState:
        return cls(
            day=str(d.get("day", "")),
            exe_seconds={str(k): int(v) for k, v in (d.get("exe_seconds") or {}).items()},
            push_snapshots=list(d.get("push_snapshots") or []),
            slots_fired=list(d.get("slots_fired") or []),
            active_tracking_seconds=int(d.get("active_tracking_seconds") or 0),
        )


def state_path() -> Path:
    return repo_root() / "data" / "state" / "day_state.json"


def _default_today_iso() -> str:
    return datetime.now(ZoneInfo("America/Santiago")).date().isoformat()


def load_state() -> DayState:
    path = state_path()
    if not path.exists():
        return DayState(day=_default_today_iso())
    try:
        with path.open(encoding="utf-8") as f:
            d = json.load(f)
        st = DayState.from_json(d)
        if not st.day:
            st.day = _default_today_iso()
        return st
    except Exception:
        logger.exception("load_state")
        return DayState(day=_default_today_iso())


def save_state(st: DayState) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(st.to_json(), f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def rollover_if_needed(st: DayState, today: str, on_flush_previous) -> DayState:
    """Si cambió el día calendario, escribe informe del día anterior y reinicia."""
    if st.day == today:
        return st
    try:
        on_flush_previous(st)
    except Exception:
        logger.exception("on_flush_previous")
    return DayState(day=today, exe_seconds={}, push_snapshots=[], slots_fired=[], active_tracking_seconds=0)
