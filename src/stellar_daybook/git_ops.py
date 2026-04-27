from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    logger.info("git: %s", " ".join(args))
    return subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def is_git_repo(root: Path) -> bool:
    return (root / ".git").is_dir()


def commit_and_push(root: Path, message: str) -> bool:
    if not is_git_repo(root):
        logger.error("No hay .git en %s — ejecuta scripts/init-repo.bat", root)
        return False
    r = _run(["git", "add", "reports", "notes"], root)
    if r.returncode != 0:
        logger.error("git add falló: %s", r.stderr)
        return False
    r = _run(["git", "status", "--porcelain"], root)
    if r.returncode != 0:
        return False
    if not (r.stdout or "").strip():
        logger.info("Nada que commitear.")
        return True
    r = _run(["git", "commit", "-m", message], root)
    if r.returncode != 0:
        logger.warning("git commit falló: %s", r.stderr)
        return False
    r = _run(["git", "push"], root)
    if r.returncode != 0:
        logger.warning("git push falló; reintenta más tarde: %s", r.stderr)
        return False
    return True
