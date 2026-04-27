from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Raíz del repo (donde está pyproject.toml / config)."""
    here = Path(__file__).resolve()
    for p in [here.parents[i] for i in range(2, 6)]:
        if (p / "pyproject.toml").exists() or (p / "config.example.yaml").exists():
            return p
    return here.parents[2]
