"""Persistence for the favorites list and the saved search presets."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from getmycar.exceptions import RepositoryError
from getmycar.filters import SearchCriteria, Sort
from getmycar.parser import Vehicle
from getmycar.utils import ensure_dir


def _read_json(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise RepositoryError(f"failed to read {path}: {e}") from e


def _write_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    try:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as e:
        raise RepositoryError(f"failed to write {path}: {e}") from e


class FavoritesRepository:
    """JSON-backed list of favorite vehicles, keyed by vehicle id."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def list(self) -> list[Vehicle]:
        raw = _read_json(self._path) or []
        if not isinstance(raw, list):  # pragma: no cover - defensive
            raise RepositoryError(f"{self._path} did not contain a list")
        return [Vehicle(**item) for item in raw]

    def add(self, vehicle: Vehicle) -> None:
        items = self.list()
        if any(v.id == vehicle.id for v in items):
            return
        items.append(vehicle)
        _write_json(self._path, [asdict(v) for v in items])

    def remove(self, vehicle_id: str) -> None:
        items = [v for v in self.list() if v.id != vehicle_id]
        _write_json(self._path, [asdict(v) for v in items])


class PresetsRepository:
    """JSON-backed dict of saved SearchCriteria presets, keyed by name."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def _read_all(self) -> dict[str, dict[str, Any]]:
        raw = _read_json(self._path) or {}
        if not isinstance(raw, dict):  # pragma: no cover - defensive
            raise RepositoryError(f"{self._path} did not contain an object")
        return raw

    def list(self) -> list[str]:
        return list(self._read_all().keys())

    def save(self, name: str, criteria: SearchCriteria) -> None:
        all_presets = self._read_all()
        all_presets[name] = _criteria_to_dict(criteria)
        _write_json(self._path, all_presets)

    def load(self, name: str) -> SearchCriteria:
        all_presets = self._read_all()
        if name not in all_presets:
            raise RepositoryError(f"preset '{name}' not found")
        return _criteria_from_dict(all_presets[name])


def _criteria_to_dict(c: SearchCriteria) -> dict[str, Any]:
    data = asdict(c)
    data["sort"] = c.sort.value
    return data


def _criteria_from_dict(data: dict[str, Any]) -> SearchCriteria:
    payload = {**data, "sort": Sort(data.get("sort", Sort.NEWEST.value))}
    return SearchCriteria(**payload)
