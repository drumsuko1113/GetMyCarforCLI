from __future__ import annotations

from pathlib import Path

import pytest

from getmycar.exceptions import ParseError
from getmycar.parser import Vehicle, parse_detail, parse_search_results

_FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def search_html() -> str:
    return (_FIXTURES / "carsensor_search.html").read_text(encoding="utf-8")


@pytest.fixture
def detail_html() -> str:
    return (_FIXTURES / "carsensor_detail.html").read_text(encoding="utf-8")


def test_parse_search_results_returns_vehicles(search_html: str) -> None:
    vehicles = parse_search_results(search_html)
    assert len(vehicles) >= 2
    for v in vehicles:
        assert v.id.startswith("AU"), f"bad id: {v.id}"
        assert v.url.startswith("https://www.carsensor.net/usedcar/detail/")
        assert "プリウス" in v.title or "プラグイン" in v.title


def test_parse_search_results_extracts_prices_and_specs(search_html: str) -> None:
    v = parse_search_results(search_html)[0]
    assert v.price_man is not None and v.price_man > 0
    assert v.year is not None and 1990 < v.year <= 2026
    assert v.mileage_km is not None and v.mileage_km >= 0
    assert v.location is not None  # should have prefecture


def test_parse_search_results_image_url_is_absolute(search_html: str) -> None:
    v = parse_search_results(search_html)[0]
    if v.image_url is not None:
        assert v.image_url.startswith("https://")


def test_parse_search_results_raises_on_unrecognised_html() -> None:
    with pytest.raises(ParseError):
        parse_search_results("<html><body>nothing useful</body></html>")


def test_parse_detail_extracts_title_and_id(detail_html: str) -> None:
    v = parse_detail(detail_html)
    assert v.id.startswith("AU")
    assert "プリウス" in v.title
    assert v.url.endswith(f"{v.id}/index.html")


def test_parse_detail_raises_on_unrecognised_html() -> None:
    with pytest.raises(ParseError):
        parse_detail("<html></html>")


def test_vehicle_is_frozen() -> None:
    v = Vehicle(id="AU1", title="t", url="u")
    with pytest.raises(Exception):
        v.title = "y"  # type: ignore[misc]
