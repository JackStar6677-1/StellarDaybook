from __future__ import annotations

import ctypes
import logging
import sys
from ctypes import wintypes

import psutil

logger = logging.getLogger(__name__)

user32 = ctypes.windll.user32


def _get_foreground_hwnd() -> int | None:
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None
    return int(hwnd)


def _window_title(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(wintypes.HWND(hwnd), buf, 512)
    return buf.value or ""


def get_foreground_process_info() -> tuple[str | None, str | None, str | None]:
    """
    Retorna (exe_basename, exe_full, ventana_titulo) o Nones si no aplica.
    Solo Windows.
    """
    if sys.platform != "win32":
        return None, None, None
    try:
        hwnd = _get_foreground_hwnd()
        if not hwnd:
            return None, None, None
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
        if not pid.value:
            return None, None, None
        title = _window_title(hwnd)
        try:
            p = psutil.Process(int(pid.value))
            exe = p.exe()
            name = p.name()
            return name, exe, title
        except (psutil.Error, OSError):
            return None, None, title
    except Exception:
        logger.exception("foreground")
        return None, None, None
