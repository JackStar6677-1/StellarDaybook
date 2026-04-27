from __future__ import annotations

import logging
import sys
import threading
from datetime import datetime, timedelta

from stellar_daybook import git_ops
from stellar_daybook.config import load_config
from stellar_daybook.foreground_win import get_foreground_process_info
from stellar_daybook.logging_util import setup_logging
from stellar_daybook.network_info import collect_network
from stellar_daybook.paths import repo_root
from stellar_daybook.privacy import should_skip_sample
from stellar_daybook.report_md import write_day_report
from stellar_daybook.resources_win import snapshot_resources
from stellar_daybook.state_store import DayState, load_state, rollover_if_needed, save_state
from stellar_daybook.timeutil import is_friday, now_local, tz_from_config
from stellar_daybook.weather import fetch_weather
from stellar_daybook.work_hours import work_label_at

logger = logging.getLogger(__name__)


class StellarDaybookApp:
    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        self.root = repo_root()
        self._lock = threading.Lock()
        self._pause_until: datetime | None = None
        self._state = load_state()
        self._poll = int((cfg.get("agent") or {}).get("foreground_poll_seconds") or 20)
        self._min_track = int((cfg.get("agent") or {}).get("min_uptime_minutes_before_push") or 12) * 60

    def machine_name(self) -> str:
        return str((self.cfg.get("machine") or {}).get("name") or "Nova")

    def pause_for(self, minutes: int) -> None:
        with self._lock:
            self._pause_until = now_local(self.cfg) + timedelta(minutes=minutes)
        logger.info("Pausa %s min hasta %s", minutes, self._pause_until)

    def _paused(self) -> bool:
        with self._lock:
            if self._pause_until is None:
                return False
            if now_local(self.cfg) >= self._pause_until:
                self._pause_until = None
                return False
            return True

    def _today_iso(self) -> str:
        return now_local(self.cfg).date().isoformat()

    def _ensure_day(self) -> None:
        today = self._today_iso()

        def flush_prev(prev: DayState) -> None:
            write_day_report(self.root, prev, self.machine_name(), self.cfg)
            logger.info("Cierre de día %s (informe local, sin push).", prev.day)

        with self._lock:
            self._state = rollover_if_needed(self._state, today, flush_prev)
            save_state(self._state)

    def tick_sampler(self) -> None:
        if sys.platform != "win32":
            return
        self._ensure_day()
        if self._paused():
            return
        name, _exe, title = get_foreground_process_info()
        if should_skip_sample(name, title, self.cfg):
            return
        key = name or "(sin nombre)"
        with self._lock:
            self._state.exe_seconds[key] = int(self._state.exe_seconds.get(key, 0)) + self._poll
            self._state.active_tracking_seconds += self._poll
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
        net = collect_network(self.cfg)
        wx = fetch_weather(self.cfg)
        res = snapshot_resources()
        snap: dict = {
            "slot": slot,
            "when_iso": when.isoformat(),
            "work_label": wl,
            "weather": wx,
            "network": net,
            "resources": res,
            "skip_reason": None,
        }

        valid = force or self._state.active_tracking_seconds >= self._min_track
        if not valid:
            snap["skip_reason"] = (
                f"Seguimiento activo insuficiente ({self._state.active_tracking_seconds}s "
                f"< {self._min_track}s) — sin commit/push."
            )
            with self._lock:
                self._state.push_snapshots.append(snap)
                self._mark_fired(slot)
                save_state(self._state)
            write_day_report(self.root, self._state, self.machine_name(), self.cfg)
            logger.info("Push omitido: %s", snap["skip_reason"])
            return

        with self._lock:
            self._state.push_snapshots.append(snap)
            save_state(self._state)

        write_day_report(self.root, self._state, self.machine_name(), self.cfg)
        msg = f"chore(daybook): {self._state.day} {slot} [{self.machine_name()}]"
        ok = git_ops.commit_and_push(self.root, msg)
        if ok:
            if slot != "manual":
                with self._lock:
                    self._mark_fired(slot)
                    save_state(self._state)
            logger.info("Push completado (%s).", slot)
        else:
            with self._lock:
                if self._state.push_snapshots:
                    self._state.push_snapshots.pop()
                save_state(self._state)
            write_day_report(self.root, self._state, self.machine_name(), self.cfg)
            logger.warning("Commit/push falló; instantánea retirada para reintentar.")

    def scheduler_tick(self) -> None:
        self._ensure_day()
        for slot in ("lunch", "evening"):
            if self._should_attempt(slot):
                self.do_push(slot, force=False)
                return

    def run_sampler_loop(self, stop: threading.Event) -> None:
        while not stop.is_set():
            try:
                self.tick_sampler()
            except Exception:
                logger.exception("sampler")
            stop.wait(self._poll)

    def run_scheduler_loop(self, stop: threading.Event) -> None:
        while not stop.is_set():
            try:
                self.scheduler_tick()
            except Exception:
                logger.exception("scheduler")
            stop.wait(15)


def run_foreground(*, console: bool = False) -> None:
    setup_logging(console=console)
    cfg = load_config()
    app = StellarDaybookApp(cfg)
    stop = threading.Event()
    t1 = threading.Thread(target=app.run_sampler_loop, args=(stop,), daemon=True, name="sampler")
    t2 = threading.Thread(target=app.run_scheduler_loop, args=(stop,), daemon=True, name="scheduler")
    t1.start()
    t2.start()
    from stellar_daybook import tray as tray_mod

    tray_mod.run_tray(app, stop)


def run_once_push(slot: str = "manual", *, console: bool = True) -> None:
    setup_logging(console=console)
    cfg = load_config()
    app = StellarDaybookApp(cfg)
    app.do_push(slot, force=True)
