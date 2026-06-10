"""Captura de estado del servidor Linux — reemplaza foreground_win + resources_win en el perfil Star."""
from __future__ import annotations

import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psutil

logger = logging.getLogger(__name__)


def _run(cmd: list[str]) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.stdout.strip()
    except Exception:
        logger.debug("capture_star._run %s", cmd, exc_info=True)
        return ""


def collect_docker() -> list[dict[str, str]]:
    """Lista de containers: nombre, estado, imagen, tiempo activo."""
    out = _run(["docker", "ps", "-a", "--format", "{{.Names}}|{{.Status}}|{{.Image}}|{{.RunningFor}}"])
    containers = []
    for line in out.splitlines():
        parts = line.split("|")
        if len(parts) >= 4:
            containers.append({
                "name": parts[0],
                "status": parts[1],
                "image": parts[2],
                "running_for": parts[3],
            })
    return containers


def collect_services(names: list[str] | None = None) -> dict[str, str]:
    """Estado activo/inactivo de servicios systemd clave."""
    if names is None:
        names = ["nginx", "cloudflared", "dnsmasq", "fail2ban", "tailscaled", "ssh"]
    result: dict[str, str] = {}
    for svc in names:
        out = _run(["systemctl", "is-active", svc])
        result[svc] = out or "unknown"
    return result


def collect_ssh_sessions() -> list[str]:
    """Usuarios conectados por SSH en este momento."""
    out = _run(["who"])
    sessions = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 4:
            sessions.append(f"{parts[0]}@{parts[-1]}")
        elif parts:
            sessions.append(line.strip())
    return sessions


def collect_resources() -> dict[str, Any]:
    """CPU, RAM y discos."""
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk_root = psutil.disk_usage("/")
        disks: dict[str, dict] = {
            "/ (nvme)": {
                "total_gb": round(disk_root.total / 1e9, 1),
                "used_pct": disk_root.percent,
            }
        }
        # Disco secundario: /home y /opt/stacks suelen estar en sata separado
        for mount_path, label in [("/home", "/home (sata)"), ("/opt/stacks", "/opt/stacks (sata)")]:
            try:
                du = psutil.disk_usage(mount_path)
                if du.total != disk_root.total:
                    disks[label] = {
                        "total_gb": round(du.total / 1e9, 1),
                        "used_pct": du.percent,
                    }
                    break
            except Exception:
                pass
        return {
            "cpu_percent": cpu,
            "ram_used_percent": ram.percent,
            "ram_used_gb": round(ram.used / 1e9, 2),
            "ram_total_gb": round(ram.total / 1e9, 2),
            "disks": disks,
        }
    except Exception:
        logger.debug("collect_resources", exc_info=True)
        return {}


def collect_network_io() -> dict[str, Any]:
    """Bytes enviados/recibidos desde boot en las interfaces principales."""
    try:
        counters = psutil.net_io_counters(pernic=True)
        result: dict[str, dict] = {}
        for iface in ("enp37s0", "tailscale0"):
            c = counters.get(iface)
            if c:
                result[iface] = {
                    "bytes_sent_mb": round(c.bytes_sent / 1e6, 1),
                    "bytes_recv_mb": round(c.bytes_recv / 1e6, 1),
                }
        return result
    except Exception:
        return {}


def collect_dhcp_leases() -> int:
    """Número de leases activos en dnsmasq."""
    leases_file = Path("/var/lib/misc/dnsmasq.leases")
    if not leases_file.exists():
        return 0
    try:
        return len([ln for ln in leases_file.read_text().splitlines() if ln.strip()])
    except Exception:
        return 0


def collect_uptime() -> str:
    """Uptime del sistema formateado."""
    try:
        secs = int(datetime.now(timezone.utc).timestamp() - psutil.boot_time())
        days, rem = divmod(secs, 86400)
        hrs, rem = divmod(rem, 3600)
        mins = rem // 60
        return f"{days}d {hrs}h {mins}m"
    except Exception:
        return "desconocido"


def snapshot_star(cfg: dict) -> dict[str, Any]:
    """Snapshot completo del estado del servidor para una instantánea de push."""
    return {
        "docker": collect_docker(),
        "services": collect_services(
            (cfg.get("star") or {}).get("monitored_services") or None
        ),
        "ssh_sessions": collect_ssh_sessions(),
        "resources": collect_resources(),
        "network_io": collect_network_io(),
        "dhcp_leases": collect_dhcp_leases(),
        "uptime": collect_uptime(),
    }
