from __future__ import annotations

import logging
from pathlib import Path

from stellar_daybook.paths import repo_root


def setup_logging(*, console: bool = False) -> None:
    log_dir = repo_root() / "data" / "state"
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / "agent.log"
    handlers: list[logging.Handler] = [
        logging.FileHandler(path, encoding="utf-8"),
    ]
    if console:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=handlers,
        force=True,
    )
