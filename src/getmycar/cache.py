"""On-disk response cache with TTL semantics."""
from __future__ import annotations

import hashlib
import os
import time
from datetime import timedelta
from pathlib import Path
from typing import Protocol

from getmycar.exceptions import CacheError
from getmycar.logging import get_logger
from getmycar.utils import ensure_dir

_log = get_logger(__name__)


class CacheProtocol(Protocol):
    def get(self, key: str) -> bytes | None: ...
    def set(self, key: str, value: bytes) -> None: ...
    def clear(self) -> None: ...


class FileCache:
    """Filesystem-backed cache. Each entry is a single file named by SHA-256(key)."""

    _SUFFIX = ".bin"

    def __init__(self, root: Path, ttl: timedelta) -> None:
        self._root = ensure_dir(root)
        self._ttl_seconds = ttl.total_seconds()

    def get(self, key: str) -> bytes | None:
        path = self._path(key)
        if not path.is_file():
            return None
        # mtime is set to the wall-clock time of the write so age is measured
        # against the same clock — keeps tests deterministic with freezegun.
        age = time.time() - path.stat().st_mtime
        if age >= self._ttl_seconds:
            _log.debug("cache miss (expired): %s", key)
            return None
        try:
            return path.read_bytes()
        except OSError as e:
            raise CacheError(f"failed to read cache entry {path}") from e

    def set(self, key: str, value: bytes) -> None:
        path = self._path(key)
        try:
            path.write_bytes(value)
            now = time.time()
            os.utime(path, (now, now))
        except OSError as e:
            raise CacheError(f"failed to write cache entry {path}") from e

    def clear(self) -> None:
        for entry in self._root.glob(f"*{self._SUFFIX}"):
            try:
                entry.unlink()
            except OSError as e:  # pragma: no cover - rare
                raise CacheError(f"failed to remove {entry}") from e

    def _path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self._root / f"{digest}{self._SUFFIX}"
