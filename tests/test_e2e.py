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


@pytest.fixture
def search_html() -> str:
    return (_FIXTURES / "search_results.html").read_text(encoding="utf-8")


@responses.activate
def test_full_flow_search_then_favorite_then_compare(
    tmp_path: Path, search_html: str
) -> None:
    responses.add(
        responses.GET, "https://www.carsensor.net/robots.txt", body=_ROBOTS_OK
    )
    # match any usedcar/search.php URL — the search command builds query params dynamically
    responses.add(
        responses.GET,
        "https://www.carsensor.net/usedcar/search.php",
        body=search_html,
        match_querystring=False,
    )

    runner = CliRunner()
    obj = {
        "config": Config(),
        "data_dir": tmp_path,
        "scraper_factory": _default_scraper_factory,
    }

    # 1. search the upstream and persist last_search.json
    result = runner.invoke(cli, ["search", "プリウス"], obj=obj)
    assert result.exit_code == 0, result.output
    assert "V001" in result.output

    # 2. add two favorites by id
    for vid in ("V001", "V002"):
        add = runner.invoke(cli, ["favorites", "add", vid], obj=obj)
        assert add.exit_code == 0, add.output

    # 3. compare them
    cmp = runner.invoke(cli, ["favorites", "compare", "V001", "V002"], obj=obj)
    assert cmp.exit_code == 0, cmp.output
    assert "V001" in cmp.output and "V002" in cmp.output

    # 4. favorites file is on disk
    favorites_json = (tmp_path / "favorites.json").read_text(encoding="utf-8")
    assert "V001" in favorites_json
    assert "V002" in favorites_json
