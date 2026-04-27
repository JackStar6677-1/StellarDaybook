from __future__ import annotations

import logging
from pathlib import Path

from stellar_daybook.heuristics import infer_tags
from stellar_daybook.state_store import DayState

logger = logging.getLogger(__name__)


def _fmt_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{m}m{s}s"
    h, m = divmod(m, 60)
    return f"{h}h{m}m"


def _weather_lines(w: dict | None) -> list[str]:
    if not w:
        return ["- Clima: (sin datos Open-Meteo)"]
    return [
        f"- Clima ({w.get('label', '')}): {w.get('temperature_c')} °C, "
        f"humedad {w.get('relative_humidity')} %, precipitación {w.get('precipitation_mm')} mm, "
        f"código tiempo WMO {w.get('weather_code')}, viento ~{w.get('wind_speed_kmh')} km/h · "
        f"instante API `{w.get('time')}`",
    ]


def _snap_table(snapshots: list[dict]) -> str:
    if not snapshots:
        return "_Sin snapshots aún._\n"
    lines = ["| Instantánea | Slot | Jornada | CPU % | RAM % | Red | Nota |", "|---|---|---|---:|---:|---|---|"]
    for s in snapshots:
        net = s.get("network") or {}
        red = ", ".join(
            f"{k}={v}" for k, v in net.items() if v
        ) or "—"
        res = s.get("resources") or {}
        lines.append(
            "| {when} | {slot} | {wl} | {cpu} | {ram} | {red} | {note} |".format(
                when=s.get("when_iso", "")[:19],
                slot=s.get("slot", ""),
                wl=s.get("work_label", ""),
                cpu=res.get("cpu_percent", "—"),
                ram=res.get("ram_used_percent", "—"),
                red=red[:80],
                note=(s.get("skip_reason") or "").replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def render_day_markdown(st: DayState, machine: str, cfg: dict) -> str:
    tags = infer_tags(st.exe_seconds.keys())
    tags_block = "\n".join(f"- {t}" for t in tags) or "- _(sin heurísticas destacadas)_"

    rows = sorted(st.exe_seconds.items(), key=lambda x: -x[1])
    table = ["| Aplicación (ejecutable) | Tiempo aprox. |", "|---|---|"]
    for exe, sec in rows[:40]:
        table.append(f"| `{exe}` | {_fmt_duration(int(sec))} |")
    if not rows:
        table.append("| — | sin muestreo aún |")

    body = "\n".join(
        [
            f"# StellarDaybook — {st.day}",
            "",
            f"- **Máquina:** {machine}",
            f"- **Zona:** {cfg.get('timezone', 'America/Santiago')}",
            f"- **Seguimiento activo acumulado (hoy):** ~{st.active_tracking_seconds // 60} min",
            "",
            "## Tiempos por aplicación (ventana en primer plano)",
            "\n".join(table),
            "",
            "## Heurísticas",
            tags_block,
            "",
            "## Instantáneas por push",
            _snap_table(st.push_snapshots),
            "",
            "## Notas manuales",
            "Edita archivos en `notes/`; el agente los incluye en los commits de informe.",
            "",
        ]
    )
    return body


def write_day_report(root: Path, st: DayState, machine: str, cfg: dict) -> Path:
    out = root / "reports" / f"{st.day}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    text = render_day_markdown(st, machine, cfg)
    out.write_text(text, encoding="utf-8")
    logger.info("Informe escrito: %s", out)
    return out
