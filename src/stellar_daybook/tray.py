from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
from pathlib import Path

from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


def _icon_image() -> Image.Image:
    img = Image.new("RGBA", (64, 64), (26, 26, 46, 255))
    d = ImageDraw.Draw(img)
    d.ellipse((12, 12, 52, 52), outline=(255, 214, 10, 255), width=3)
    d.ellipse((22, 22, 42, 42), fill=(255, 214, 10, 230))
    return img


def _open_repo_folder(root: Path) -> None:
    if sys.platform == "win32":
        os.startfile(str(root))  # noqa: S606
    else:
        subprocess.Popen(["xdg-open", str(root)])  # noqa: S603,S607


def run_tray(app: object, stop: threading.Event) -> None:
    import pystray
    from pystray import Menu, MenuItem

    root: Path = app.root  # type: ignore[attr-defined]
    cfg: dict = app.cfg  # type: ignore[attr-defined]

    presets = list(cfg.get("pause_presets_minutes") or [10, 15, 20, 30])
    presets = sorted({*presets, 60})

    def make_pause(minutes: int):
        def _cb(icon: object, item: object) -> None:
            app.pause_for(minutes)  # type: ignore[attr-defined]

        return _cb

    pause_items = [MenuItem(f"Pausar {m} min", make_pause(m)) for m in presets]

    def on_force(icon: object, item: object) -> None:
        threading.Thread(
            target=lambda: app.do_push("manual", force=True),  # type: ignore[attr-defined]
            daemon=True,
        ).start()

    def on_folder(icon: object, item: object) -> None:
        _open_repo_folder(root)

    def on_exit(icon: object, item: object) -> None:
        stop.set()
        icon.stop()

    menu = Menu(
        MenuItem("Informe + push ahora", on_force),
        MenuItem("Pausar registro", Menu(*pause_items)),
        MenuItem("Abrir carpeta del repo", on_folder),
        MenuItem("Salir", on_exit),
    )

    icon = pystray.Icon(
        "stellar_daybook",
        _icon_image(),
        "StellarDaybook",
        menu,
    )
    logger.info("Bandeja lista (área de notificación / iconos ocultos).")
    icon.run()
