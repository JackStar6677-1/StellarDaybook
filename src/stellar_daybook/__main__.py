"""Punto de entrada: agente en bandeja o un push manual de prueba."""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    if sys.platform != "win32":
        print("StellarDaybook: solo Windows (foreground Win32, bandeja).")
        raise SystemExit(2)

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

    if a.once:
        from stellar_daybook.app import run_once_push

        # --once suele ser prueba: siempre log en consola además del archivo.
        run_once_push(a.slot, console=True)
        return

    from stellar_daybook.app import run_foreground

    run_foreground(console=a.console)


if __name__ == "__main__":
    main()
