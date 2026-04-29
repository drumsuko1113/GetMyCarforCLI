from __future__ import annotations

from pathlib import Path

import pytest

from getmycar.exceptions import RepositoryError
from getmycar.favorites import FavoritesRepository, PresetsRepository
from getmycar.filters import SearchCriteria, Sort
from getmycar.parser import Vehicle


def _make_vehicle(vid: str = "V1", title: str = "プリウス") -> Vehicle:
    return Vehicle(
        id=vid,
        title=title,
        url=f"https://example.com/{vid}",
        price_man=120,
        year=2018,
        mileage_km=50000,
        location="東京都",
    )


def test_favorites_add_then_list(tmp_path: Path) -> None:
    repo = FavoritesRepository(tmp_path / "favorites.json")
    v = _make_vehicle()
    repo.add(v)
    assert repo.list() == [v]


def test_favorites_persist_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "favorites.json"
    FavoritesRepository(path).add(_make_vehicle("V1"))
    FavoritesRepository(path).add(_make_vehicle("V2"))
    ids = sorted(v.id for v in FavoritesRepository(path).list())
    assert ids == ["V1", "V2"]


def test_favorites_add_is_idempotent(tmp_path: Path) -> None:
    repo = FavoritesRepository(tmp_path / "favorites.json")
    repo.add(_make_vehicle("V1"))
    repo.add(_make_vehicle("V1", title="updated"))  # same id -> no-op
    favorites = repo.list()
    assert len(favorites) == 1
    assert favorites[0].title == "プリウス"


def test_favorites_remove(tmp_path: Path) -> None:
    repo = FavoritesRepository(tmp_path / "favorites.json")
    repo.add(_make_vehicle("V1"))
    repo.add(_make_vehicle("V2"))
    repo.remove("V1")
    assert [v.id for v in repo.list()] == ["V2"]


def test_favorites_remove_unknown_is_no_op(tmp_path: Path) -> None:
    repo = FavoritesRepository(tmp_path / "favorites.json")
    repo.remove("missing")
    assert repo.list() == []


def test_favorites_corrupt_file_raises(tmp_path: Path) -> None:
    path = tmp_path / "favorites.json"
    path.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(RepositoryError):
        FavoritesRepository(path).list()


def test_presets_save_and_load_roundtrip(tmp_path: Path) -> None:
    repo = PresetsRepository(tmp_path / "presets.json")
    criteria = SearchCriteria(
        keyword="プリウス",
        price_max=200,
        year_min=2018,
        sort=Sort.PRICE_ASC,
        page=2,
        per_page=30,
    )
    repo.save("cheap-prius", criteria)
    loaded = repo.load("cheap-prius")
    assert loaded == criteria


def test_presets_list_returns_names(tmp_path: Path) -> None:
    repo = PresetsRepository(tmp_path / "presets.json")
    repo.save("a", SearchCriteria(keyword="a"))
    repo.save("b", SearchCriteria(keyword="b"))
    assert sorted(repo.list()) == ["a", "b"]


def test_presets_load_unknown_raises(tmp_path: Path) -> None:
    repo = PresetsRepository(tmp_path / "presets.json")
    with pytest.raises(RepositoryError):
        repo.load("missing")
