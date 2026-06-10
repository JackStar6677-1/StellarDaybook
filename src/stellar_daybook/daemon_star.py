"""Demonio headless para Star (Linux) — reemplaza tray.py en servidores sin GUI."""
from __future__ import annotations

import logging
import signal
import threading
from datetime import datetime
from typing import Any

from stellar_daybook import git_ops
from stellar_daybook.capture_star import snapshot_star
from stellar_daybook.config import load_config
from stellar_daybook.logging_util import setup_logging
from stellar_daybook.paths import repo_root
from stellar_daybook.report_star import write_star_report
from stellar_daybook.state_store import DayState, load_state, rollover_if_needed, save_state
from stellar_daybook.timeutil import is_friday, now_local, tz_from_config
from stellar_daybook.weather import fetch_weather
from stellar_daybook.work_hours import work_label_at

logger = logging.getLogger(__name__)


class StarDaemon:
    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        self.root = repo_root()
        self._lock = threading.Lock()
        self._state = load_state()
        self._last_snap: dict[str, Any] | None = None

    def machine_name(self) -> str:
        return str((self.cfg.get("machine") or {}).get("name") or "Star")

    def _today_iso(self) -> str:
        return now_local(self.cfg).date().isoformat()

    def _ensure_day(self) -> None:
        today = self._today_iso()

        def flush_prev(prev: DayState) -> None:
            write_star_report(self.root, prev, self.cfg, self._last_snap)
            logger.info("Cierre de día %s — informe local guardado.", prev.day)

        with self._lock:
            self._state = rollover_if_needed(self._state, today, flush_prev)
            save_state(self._state)

    def _slot_key(self, slot: str) -> str:
        return f"{self._state.day}:{slot}"

    def _already_fired(self, slot: str) -> bool:
        return self._slot_key(slot) in self._state.slots_fired

    def _mark_fired(self, slot: str) -> None:
        sk = self._slot_key(slot)
        if sk not in self._state.slots_fired:
            self._state.slots_fired.append(sk)

    def _in_lunch_window(self, n: datetime) -> bool:
        return n.hour == 13 and 30 <= n.minute <= 34

    def _in_evening_window(self, n: datetime) -> bool:
        if is_friday(n.date()):
            return n.hour == 16 and 25 <= n.minute <= 29
        return n.hour == 17 and 20 <= n.minute <= 24

    def _should_attempt(self, slot: str) -> bool:
        tz = tz_from_config(self.cfg)
        n = now_local(self.cfg).astimezone(tz)
        if self._already_fired(slot):
            return False
        if slot == "lunch":
            return self._in_lunch_window(n)
        if slot == "evening":
            return self._in_evening_window(n)
        return False

    def do_push(self, slot: str, *, force: bool = False) -> None:
        self._ensure_day()
        tz = tz_from_config(self.cfg)
        when = now_local(self.cfg).astimezone(tz)
        wl = work_label_at(when, self.cfg)
        wx = fetch_weather(self.cfg)
        snap_data = snapshot_star(self.cfg)
        snap_data.update({
            "slot": slot,
            "when_iso": when.isoformat(),
            "work_label": wl,
            "weather": wx,
            "skip_reason": None,
        })
        self._last_snap = snap_data

        with self._lock:
            self._state.push_snapshots.append(snap_data)
            save_state(self._state)

        write_star_report(self.root, self._state, self.cfg, snap_data)
        msg = f"chore(daybook): {self._state.day} {slot} [{self.machine_name()}]"
        ok = git_ops.commit_and_push(self.root, msg)
        if ok:
            if slot != "manual":
                with self._lock:
                    self._mark_fired(slot)
                    save_state(self._state)
            logger.info("Push completado (%s).", slot)
        else:
            # Retirar instantánea para reintentar en el siguiente ciclo
            with self._lock:
                if self._state.push_snapshots:
                    self._state.push_snapshots.pop()
                save_state(self._state)
            write_star_report(self.root, self._state, self.cfg, snap_data)
            logger.warning("Commit/push falló — instantánea retirada para reintento.")

    def scheduler_tick(self) -> None:
        self._ensure_day()
        for slot in ("lunch", "evening"):
            if self._should_attempt(slot):
                self.do_push(slot, force=False)
                return

    def run_scheduler_loop(self, stop: threading.Event) -> None:
        while not stop.is_set():
            try:
                self.scheduler_tick()
            except Exception:
                logger.exception("scheduler_tick")
            stop.wait(30)


def run_daemon(*, console: bool = False) -> None:
    setup_logging(console=console)
    cfg = load_config()
    daemon = StarDaemon(cfg)
    stop = threading.Event()

    def _handle(sig, _frame) -> None:
        logger.info("Señal %s — deteniendo daemon.", sig)
        stop.set()

    signal.signal(signal.SIGTERM, _handle)
    signal.signal(signal.SIGINT, _handle)

    logger.info("StellarDaybook Star iniciado — máquina: %s", daemon.machine_name())
    t = threading.Thread(target=daemon.run_scheduler_loop, args=(stop,), daemon=True, name="scheduler")
    t.start()
    stop.wait()
    logger.info("StellarDaybook Star detenido.")


def run_once(slot: str = "manual") -> None:
    setup_logging(console=True)
    cfg = load_config()
    daemon = StarDaemon(cfg)
    daemon.do_push(slot, force=True)
