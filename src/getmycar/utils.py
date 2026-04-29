"""Cross-cutting helpers shared across modules."""
from __future__ import annotations

from pathlib import Path


def ensure_dir(path: Path) -> Path:
    """Create *path* and parents if missing; return the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path
