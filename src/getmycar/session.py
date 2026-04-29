"""Persists the most recent search results so favorites can reference them by id."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from getmycar.exceptions import RepositoryError
from getmycar.parser import Vehicle
from getmycar.utils import ensure_dir


class LastSearchStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def save(self, vehicles: list[Vehicle]) -> None:
        ensure_dir(self._path.parent)
        try:
            self._path.write_text(
                json.dumps([asdict(v) for v in vehicles], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as e:
            raise RepositoryError(f"failed to write {self._path}") from e

    def load(self) -> list[Vehicle]:
        if not self._path.is_file():
            return []
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            raise RepositoryError(f"failed to read {self._path}") from e
        return [Vehicle(**item) for item in raw]

    def find(self, vehicle_id: str) -> Vehicle | None:
        for v in self.load():
            if v.id == vehicle_id:
                return v
        return None
