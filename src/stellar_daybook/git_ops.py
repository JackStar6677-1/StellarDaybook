from __future__ import annotations

import logging
import os
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


def _git_config_value(root: Path, key: str) -> str:
    r = _run(["git", "config", "--get", key], root)
    if r.returncode != 0:
        return ""
    return (r.stdout or "").strip()


def _ensure_git_identity(root: Path) -> None:
    name = _git_config_value(root, "user.name")
    email = _git_config_value(root, "user.email")

    if not name:
        name = os.environ.get("GIT_AUTHOR_NAME") or os.environ.get("USERNAME") or "StellarDaybook"
        r = _run(["git", "config", "user.name", name], root)
        if r.returncode != 0:
            logger.warning("No se pudo fijar git user.name local: %s", r.stderr)
        else:
            logger.info("Git identity: user.name=%s", name)

    if not email:
        user = os.environ.get("GIT_AUTHOR_EMAIL_USER") or os.environ.get("USERNAME") or "stellar-daybook"
        host = (os.environ.get("COMPUTERNAME") or "local").lower()
        email = f"{user}@{host}.local"
        r = _run(["git", "config", "user.email", email], root)
        if r.returncode != 0:
            logger.warning("No se pudo fijar git user.email local: %s", r.stderr)
        else:
            logger.info("Git identity: user.email configurado localmente")


def commit_and_push(root: Path, message: str) -> bool:
    if not is_git_repo(root):
        logger.error("No hay .git en %s — ejecuta scripts/init-repo.bat", root)
        return False
    _ensure_git_identity(root)
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
