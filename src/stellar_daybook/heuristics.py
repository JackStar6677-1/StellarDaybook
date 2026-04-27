from __future__ import annotations

import logging
from typing import Iterable

import psutil

logger = logging.getLogger(__name__)

OBS_NAMES = {"obs64", "obs32", "obs"}
MC_NAMES = {
    "minecraft",
    "javaw",
    "java",
    "minecraftlauncher",
    "curseforge",
    "curse",
    "prismlauncher",
    "multimc",
    "gdlauncher",
}


def _running_names() -> set[str]:
    out: set[str] = set()
    try:
        for p in psutil.process_iter(["name"]):
            n = p.info.get("name")
            if n:
                out.add(n.lower())
    except Exception:
        logger.debug("process_iter", exc_info=True)
    return out


def _stem(s: str) -> str:
    s = s.lower().strip()
    return s[:-4] if s.endswith(".exe") else s


def infer_tags(exe_keys: Iterable[str]) -> list[str]:
    """Etiquetas contextuales a partir de ejecutables acumulados y procesos en ejecución."""
    tags: list[str] = []
    keys_l = {_stem(k) for k in exe_keys}
    running = {_stem(x) for x in _running_names()}

    if keys_l & OBS_NAMES or running & OBS_NAMES:
        tags.append("OBS en uso o reciente: posible grabación, transmisión o ajustes.")

    mcish = bool(keys_l & MC_NAMES or running & MC_NAMES)
    curse = any("curse" in k for k in keys_l) or any("curse" in r for r in running)
    if mcish or curse:
        tags.append(
            "Minecraft / launcher / CurseForge detectado: probable trabajo DrakesCraft / "
            "DrakesLab (Slimefun) — heurística, no certeza."
        )

    dev_hints = ("cursor", "code", "devenv", "rider", "idea", "windowsterminal", "pwsh", "powershell")
    if any(h in k for h in dev_hints for k in keys_l):
        tags.append("IDE / terminal / editor presente en la ventana activa acumulada.")

    return tags
