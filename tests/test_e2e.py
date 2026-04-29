"""End-to-end smoke test: search -> favorites add -> favorites compare.

Uses ``responses`` to stub out HTTP so no real network access happens.
This wires every layer (scraper, parser, repos, display, CLI) together.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import responses
from click.testing import CliRunner

from getmycar.config import Config
from getmycar.main import _default_scraper_factory, cli

_FIXTURES = Path(__file__).parent / "fixtures"
_ROBOTS_OK = "User-agent: *\nAllow: /\n"
_ID_A = "AU6877255381"
_ID_B = "AU6869806001"


@pytest.fixture
def search_html() -> str:
    return (_FIXTURES / "carsensor_search.html").read_text(encoding="utf-8")


@responses.activate
def test_full_flow_search_then_favorite_then_compare(tmp_path: Path, search_html: str) -> None:
    responses.add(responses.GET, "https://www.carsensor.net/robots.txt", body=_ROBOTS_OK)
    responses.add(
        responses.GET,
        "https://www.carsensor.net/usedcar/index.html",
        body=search_html,
        match_querystring=False,
    )

    runner = CliRunner()
    obj = {
        "config": Config(),
        "data_dir": tmp_path,
        "scraper_factory": _default_scraper_factory,
    }

    result = runner.invoke(cli, ["search", "プリウス"], obj=obj)
    assert result.exit_code == 0, result.output
    assert _ID_A in result.output

    for vid in (_ID_A, _ID_B):
        add = runner.invoke(cli, ["favorites", "add", vid], obj=obj)
        assert add.exit_code == 0, add.output

    cmp = runner.invoke(cli, ["favorites", "compare", _ID_A, _ID_B], obj=obj)
    assert cmp.exit_code == 0, cmp.output
    assert _ID_A in cmp.output and _ID_B in cmp.output

    favorites_json = (tmp_path / "favorites.json").read_text(encoding="utf-8")
    assert _ID_A in favorites_json
    assert _ID_B in favorites_json
