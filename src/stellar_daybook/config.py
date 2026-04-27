from __future__ import annotations

import copy
import logging
from pathlib import Path
from typing import Any

import yaml

from stellar_daybook.paths import repo_root

logger = logging.getLogger(__name__)


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in overlay.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_config() -> dict[str, Any]:
    root = repo_root()
    example = root / "config.example.yaml"
    local = root / "config.local.yaml"
    if not example.exists():
        raise FileNotFoundError(f"No se encontró {example}")
    with example.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    if local.exists():
        with local.open(encoding="utf-8") as f:
            loc = yaml.safe_load(f) or {}
        cfg = _deep_merge(cfg, loc)
        logger.info("Config: usando %s sobre config.example.yaml", local.name)
    else:
        logger.warning(
            "No hay config.local.yaml; usando solo config.example.yaml "
            "(copia a config.local.yaml y pon machine.name Nova/Nexus)."
        )
    return cfg
