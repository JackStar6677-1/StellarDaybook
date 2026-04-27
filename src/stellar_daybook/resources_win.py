from __future__ import annotations

import logging
import sys

import psutil

logger = logging.getLogger(__name__)


def snapshot_resources() -> dict[str, float | int | str | None]:
    """CPU y RAM al instante (sin GPU para mantener dependencias mínimas)."""
    if sys.platform != "win32":
        return {}
    try:
        cpu = psutil.cpu_percent(interval=0.15)
        vm = psutil.virtual_memory()
        return {
            "cpu_percent": round(cpu, 1),
            "ram_used_percent": round(vm.percent, 1),
            "ram_total_gb": round(vm.total / (1024**3), 2),
        }
    except Exception:
        logger.debug("resources", exc_info=True)
        return {}
