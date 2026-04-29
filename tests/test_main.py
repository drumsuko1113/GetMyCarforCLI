from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from getmycar.config import Config
from getmycar.main import cli
from getmycar.parser import Vehicle


class _FakeScraper:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def get(self, url: str) -> bytes:  # noqa: ARG002
        return self._body


_SEARCH_HTML = (Path(__file__).parent / "fixtures" / "search_results.html").read_text(
    encoding="utf-8"
)


@pytest.fixture
def base_obj(tmp_path: Path) -> dict[str, object]:
    return {
        "config": Config(),
        "data_dir": tmp_path,
        "scraper_factory": lambda cfg, dd: _FakeScraper(_SEARCH_HTML.encode("utf-8")),
    }


def test_help_runs() -> None:
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "search" in result.output
    assert "favorites" in result.output


def test_search_renders_and_persists_last_results(
    base_obj: dict[str, object], tmp_path: Path
) -> None:
    result = CliRunner().invoke(cli, ["search", "プリウス"], obj=base_obj)
    assert result.exit_code == 0, result.output
    assert "プリウス" in result.output
    last = json.loads((tmp_path / "last_search.json").read_text(encoding="utf-8"))
    assert any(item["id"] == "V001" for item in last)


def test_favorites_add_then_list(base_obj: dict[str, object]) -> None:
    runner = CliRunner()
    runner.invoke(cli, ["search", "プリウス"], obj=base_obj)
    add = runner.invoke(cli, ["favorites", "add", "V001"], obj=base_obj)
    assert add.exit_code == 0, add.output
    listing = runner.invoke(cli, ["favorites", "list"], obj=base_obj)
    assert "V001" in listing.output


def test_favorites_add_unknown_id_errors(base_obj: dict[str, object]) -> None:
    result = CliRunner().invoke(cli, ["favorites", "add", "XYZ"], obj=base_obj)
    assert result.exit_code != 0
    assert "not found" in result.output


def test_favorites_remove(base_obj: dict[str, object]) -> None:
    runner = CliRunner()
    runner.invoke(cli, ["search", "x"], obj=base_obj)
    runner.invoke(cli, ["favorites", "add", "V001"], obj=base_obj)
    runner.invoke(cli, ["favorites", "remove", "V001"], obj=base_obj)
    listing = runner.invoke(cli, ["favorites", "list"], obj=base_obj)
    assert "V001" not in listing.output


def test_favorites_compare(base_obj: dict[str, object]) -> None:
    runner = CliRunner()
    runner.invoke(cli, ["search", "x"], obj=base_obj)
    runner.invoke(cli, ["favorites", "add", "V001"], obj=base_obj)
    runner.invoke(cli, ["favorites", "add", "V002"], obj=base_obj)
    result = runner.invoke(
        cli, ["favorites", "compare", "V001", "V002"], obj=base_obj
    )
    assert result.exit_code == 0, result.output
    assert "V001" in result.output and "V002" in result.output


def test_favorites_compare_unknown_id_errors(base_obj: dict[str, object]) -> None:
    result = CliRunner().invoke(
        cli, ["favorites", "compare", "ZZZ"], obj=base_obj
    )
    assert result.exit_code != 0


def test_preset_save_and_list(base_obj: dict[str, object]) -> None:
    runner = CliRunner()
    save = runner.invoke(
        cli,
        ["preset", "save", "cheap", "プリウス", "--price-max", "200"],
        obj=base_obj,
    )
    assert save.exit_code == 0, save.output
    listing = runner.invoke(cli, ["preset", "list"], obj=base_obj)
    assert "cheap" in listing.output


def test_preset_load_emits_url(base_obj: dict[str, object]) -> None:
    runner = CliRunner()
    runner.invoke(
        cli,
        ["preset", "save", "cheap", "プリウス", "--price-max", "200"],
        obj=base_obj,
    )
    result = runner.invoke(cli, ["preset", "load", "cheap"], obj=base_obj)
    assert result.exit_code == 0
    assert "PRICE_MAX=200" in result.output


def test_cache_clear_does_not_error(base_obj: dict[str, object]) -> None:
    result = CliRunner().invoke(cli, ["cache", "clear"], obj=base_obj)
    assert result.exit_code == 0


def test_unused_vehicle_object_is_typed(base_obj: dict[str, object]) -> None:
    # sanity that Vehicle is importable in this test module
    assert Vehicle(id="x", title="t", url="u").id == "x"
