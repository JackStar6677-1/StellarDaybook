from __future__ import annotations

import logging
import re
import subprocess
import sys

import psutil

logger = logging.getLogger(__name__)


def _ssid_windows() -> str | None:
    if sys.platform != "win32":
        return None
    try:
        r = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
        )
        if r.returncode != 0:
            return None
        for line in r.stdout.splitlines():
            line = line.strip()
            m = re.match(r"SSID\s*:\s*(.+)$", line, re.I)
            if m:
                return m.group(1).strip()
    except Exception:
        logger.debug("ssid", exc_info=True)
    return None


def _local_ipv4() -> str | None:
    try:
        for _, addrs in psutil.net_if_addrs().items():
            for a in addrs:
                if a.family.name == "AF_INET" and a.address and not a.address.startswith("127."):
                    return a.address
    except Exception:
        logger.debug("ipv4", exc_info=True)
    return None


def collect_network(cfg: dict) -> dict[str, str | None]:
    net = cfg.get("network") or {}
    out: dict[str, str | None] = {}
    if net.get("include_ssid", True):
        out["ssid"] = _ssid_windows()
    if net.get("include_local_ipv4", True):
        out["local_ipv4"] = _local_ipv4()
    return out
