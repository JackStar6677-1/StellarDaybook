"""Punto de entrada: agente en bandeja o un push manual de prueba."""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    p = argparse.ArgumentParser(description="StellarDaybook — bitácora diaria")
    p.add_argument(
        "--once",
        action="store_true",
        help="Un solo informe + push (manual, ignora mínimo de seguimiento).",
    )
    p.add_argument("--slot", default="manual", help="Nombre del slot con --once (default: manual).")
    p.add_argument(
        "--console",
        action="store_true",
        help="Escribir logs también en consola (útil al depurar).",
    )
    a = p.parse_args()

    if sys.platform != "win32":
        # Perfil Star — demonio headless para servidor Linux
        if a.once:
            from stellar_daybook.daemon_star import run_once
            run_once(a.slot)
        else:
            from stellar_daybook.daemon_star import run_daemon
            run_daemon(console=a.console)
        return

    # Perfil Windows — Nova / Nexus (bandeja de sistema)
    if a.once:
        from stellar_daybook.app import run_once_push
        run_once_push(a.slot, console=True)
        return

    from stellar_daybook.app import run_foreground
    run_foreground(console=a.console)


if __name__ == "__main__":
    main()
