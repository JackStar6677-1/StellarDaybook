"""Renderiza el informe diario Markdown para el perfil Star (servidor Linux)."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from stellar_daybook.state_store import DayState

logger = logging.getLogger(__name__)

_STATUS_ICON: dict[str, str] = {
    "active": "🟢",
    "inactive": "🔴",
    "failed": "🔴",
    "activating": "🟡",
    "unknown": "⚪",
}


def _svc_icon(status: str) -> str:
    return _STATUS_ICON.get(status.lower().split()[0], "⚪")


def _docker_table(containers: list[dict], restarts: dict[str, int] | None = None) -> str:
    if not containers:
        return "_Docker no disponible o sin containers._\n"
    restarts = restarts or {}
    lines = [
        "| Container | Estado | Imagen | Activo por | Reinicios |",
        "|---|---|---|---|---:|",
    ]
    for c in containers:
        icon = "🟢" if c["status"].lower().startswith("up") else "🔴"
        r = restarts.get(c["name"], 0)
        r_str = f"⚠️ {r}" if r > 0 else "0"
        lines.append(
            f"| `{c['name']}` | {icon} {c['status']} | `{c['image']}` | {c['running_for']} | {r_str} |"
        )
    return "\n".join(lines) + "\n"


def _fail2ban_block(fb: dict) -> str:
    if not fb or not fb.get("jails"):
        return "- Sin datos de fail2ban (¿requiere sudo?)\n"
    lines = [f"- **IPs baneadas actualmente:** {fb.get('total_banned', 0)}"]
    for jail, stats in fb["jails"].items():
        lines.append(
            f"  - `{jail}`: {stats.get('banned', 0)} baneadas, "
            f"{stats.get('total_failed', 0)} intentos fallidos totales"
        )
    return "\n".join(lines) + "\n"


def _services_table(services: dict[str, str]) -> str:
    if not services:
        return "_Sin datos de servicios._\n"
    lines = ["| Servicio | Estado |", "|---|---|"]
    for svc, st in services.items():
        lines.append(f"| `{svc}` | {_svc_icon(st)} {st} |")
    return "\n".join(lines) + "\n"


def _resources_block(res: dict) -> str:
    if not res:
        return "- Sin datos de recursos.\n"
    lines = [
        f"- **CPU:** {res.get('cpu_percent', '?')} %",
        f"- **RAM:** {res.get('ram_used_gb', '?')} / {res.get('ram_total_gb', '?')} GB  "
        f"({res.get('ram_used_percent', '?')} %)",
    ]
    for disk, info in (res.get("disks") or {}).items():
        lines.append(f"- **Disco {disk}:** {info.get('used_pct', '?')} % de {info.get('total_gb', '?')} GB")
    return "\n".join(lines) + "\n"


def _net_block(net_io: dict) -> str:
    if not net_io:
        return "_Sin datos de red._\n"
    lines = []
    for iface, data in net_io.items():
        lines.append(
            f"- **{iface}:** ↑ {data.get('bytes_sent_mb')} MB  ↓ {data.get('bytes_recv_mb')} MB (desde boot)"
        )
    return "\n".join(lines) + "\n"


def _snap_table(snapshots: list[dict]) -> str:
    if not snapshots:
        return "_Sin instantáneas aún._\n"
    lines = [
        "| Slot | Instante | CPU % | RAM % | DHCP | SSH | Uptime | Nota |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for s in snapshots:
        res = s.get("resources") or {}
        lines.append(
            "| {slot} | {when} | {cpu} | {ram} | {leases} | {ssh} | {up} | {note} |".format(
                slot=s.get("slot", ""),
                when=(s.get("when_iso") or "")[:19],
                cpu=res.get("cpu_percent", "—"),
                ram=res.get("ram_used_percent", "—"),
                leases=s.get("dhcp_leases", "—"),
                ssh=len(s.get("ssh_sessions") or []),
                up=s.get("uptime", "—"),
                note=(s.get("skip_reason") or "").replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def render_star_markdown(
    st: DayState,
    cfg: dict,
    last_snap: dict[str, Any] | None = None,
) -> str:
    machine = str((cfg.get("machine") or {}).get("name") or "Star")
    snap = last_snap or {}
    if not snap and st.push_snapshots:
        snap = st.push_snapshots[-1]

    docker_data: list[dict] = snap.get("docker") or []
    docker_restarts: dict = snap.get("docker_restarts") or {}
    services_data: dict = snap.get("services") or {}
    resources_data: dict = snap.get("resources") or {}
    uptime: str = snap.get("uptime", "desconocido")
    leases: Any = snap.get("dhcp_leases", "?")
    ssh: list = snap.get("ssh_sessions") or []
    net_io: dict = snap.get("network_io") or {}
    fail2ban_data: dict = snap.get("fail2ban") or {}
    nginx_reqs: int = snap.get("nginx_requests_today", 0)
    wx: dict | None = snap.get("weather")

    wx_line = ""
    if wx:
        wx_line = (
            f"- **Clima ({wx.get('label', '')}):** {wx.get('temperature_c')} °C, "
            f"humedad {wx.get('relative_humidity')} %, "
            f"precipitación {wx.get('precipitation_mm')} mm, "
            f"viento ~{wx.get('wind_speed_kmh')} km/h"
        )

    ssh_detail = f" ({', '.join(ssh)})" if ssh else ""

    sections = [
        f"# StellarDaybook — {st.day} — {machine}",
        "",
        f"- **Zona horaria:** {cfg.get('timezone', 'America/Santiago')}",
        f"- **Uptime del servidor:** {uptime}",
        f"- **Leases DHCP activos:** {leases}",
        f"- **Sesiones SSH activas:** {len(ssh)}{ssh_detail}",
    ]
    if wx_line:
        sections.append(wx_line)

    sections += [
        "",
        "## Containers Docker",
        _docker_table(docker_data, docker_restarts),
        "## Servicios del sistema",
        _services_table(services_data),
        "## Recursos del servidor",
        _resources_block(resources_data),
        "## Tráfico de red (desde boot)",
        _net_block(net_io),
        "## Seguridad",
        f"- **Requests nginx hoy:** {nginx_reqs}",
        _fail2ban_block(fail2ban_data),
        "## Instantáneas por push",
        _snap_table(st.push_snapshots),
        "## Notas manuales",
        "Edita archivos en `notes/`; el agente los incluye en los commits de informe.",
        "",
    ]
    return "\n".join(sections)


def write_star_report(
    root: Path,
    st: DayState,
    cfg: dict,
    last_snap: dict[str, Any] | None = None,
) -> Path:
    machine = str((cfg.get("machine") or {}).get("name") or "Star")
    slug = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in machine.strip()) or "Star"
    out = root / "reports" / f"{st.day}_{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_star_markdown(st, cfg, last_snap), encoding="utf-8")
    logger.info("Informe Star escrito: %s", out)
    return out
