"""Centralized logging setup using Rich for console output."""
from __future__ import annotations

import logging
from typing import Final

from rich.logging import RichHandler

_ROOT: Final = "getmycar"
_LEVELS: Final = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}


def get_logger(name: str) -> logging.Logger:
    """Return a logger under the ``getmycar`` namespace."""
    return logging.getLogger(name)


def configure_logging(verbosity: int = 0) -> None:
    """Configure the root ``getmycar`` logger.

    ``verbosity`` is the count of ``-v`` flags passed on the CLI: 0 -> WARNING,
    1 -> INFO, 2+ -> DEBUG. Calling repeatedly only adjusts the level — the
    Rich handler is attached at most once.
    """
    level = _LEVELS.get(verbosity, logging.DEBUG)
    root = logging.getLogger(_ROOT)
    root.setLevel(level)
    if not any(isinstance(h, RichHandler) for h in root.handlers):
        handler = RichHandler(rich_tracebacks=True, show_path=False)
        handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
        root.addHandler(handler)
    root.propagate = False
